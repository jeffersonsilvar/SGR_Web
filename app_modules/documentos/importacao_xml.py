from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import uuid
import xml.etree.ElementTree as ET

from flask import current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from danfse_parser import parse_nfse_xml
from app_modules.storage import StorageService, StorageServiceError


SESSAO_RASCUNHO = "documento_fiscal_importacao_xml"
SUFIXOS_JURIDICOS = {"ltda": "Ltda", "sa": "S.A.", "s/a": "S.A.", "eireli": "Eireli", "mei": "MEI", "epp": "EPP", "me": "ME"}
PREPOSICOES = {"de", "da", "do", "das", "dos", "e"}


def _local(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _digits(valor):
    return re.sub(r"\D", "", str(valor or ""))


def normalizar_nome_apresentacao(valor):
    """Normaliza apresentação sem alterar o XML original preservado em arquivo."""
    texto = " ".join(str(valor or "").strip().split())
    if not texto:
        return ""
    partes = []
    for indice, palavra in enumerate(texto.split(" ")):
        chave = palavra.lower()
        if chave in SUFIXOS_JURIDICOS:
            partes.append(SUFIXOS_JURIDICOS[chave])
        elif indice > 0 and chave in PREPOSICOES:
            partes.append(chave)
        elif palavra.isupper() or palavra.islower():
            partes.append(palavra.capitalize())
        else:
            partes.append(palavra)
    return " ".join(partes)


def _texto(parent, nome):
    if parent is None:
        return ""
    for el in parent.iter():
        if _local(el.tag) == nome and el.text:
            return el.text.strip()
    return ""


def _primeiro(root, nome):
    for el in root.iter():
        if _local(el.tag) == nome:
            return el
    return None


def _data_iso(valor):
    texto = str(valor or "").strip()
    if not texto:
        return ""
    texto = texto[:10]
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""


def _decimal_xml(valor):
    texto = str(valor or "").strip().replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return f"{Decimal(texto).quantize(Decimal('0.01')):.2f}"
    except (InvalidOperation, ValueError):
        return "0.00"


def _parse_nfe(root):
    inf = _primeiro(root, "infNFe")
    if inf is None:
        raise ValueError("Estrutura NF-e não localizada no XML.")
    ide = _primeiro(inf, "ide")
    emit = _primeiro(inf, "emit")
    dest = _primeiro(inf, "dest")
    total = _primeiro(inf, "ICMSTot")
    if emit is None or ide is None:
        raise ValueError("XML de NF-e sem identificação do emitente/nota.")

    chave = str(inf.attrib.get("Id") or "")
    chave = re.sub(r"^[A-Za-z]+", "", chave)
    numero = _texto(ide, "nNF")
    serie = _texto(ide, "serie")
    emissao = _data_iso(_texto(ide, "dhEmi") or _texto(ide, "dEmi"))
    nome_original = _texto(emit, "xNome")
    cnpj_cpf = _digits(_texto(emit, "CNPJ") or _texto(emit, "CPF"))
    destinatario = _digits(_texto(dest, "CNPJ") or _texto(dest, "CPF")) if dest is not None else ""
    valor = _decimal_xml(_texto(total, "vNF") if total is not None else "0")

    produtos = []
    for det in inf.iter():
        if _local(det.tag) == "prod":
            nome = _texto(det, "xProd")
            if nome and nome not in produtos:
                produtos.append(nome)
            if len(produtos) >= 3:
                break
    descricao = "; ".join(produtos) if produtos else f"NF-e {numero}"

    return {
        "tipo_documento": "NFE_USO_CONSUMO",
        "numero_documento": numero,
        "serie": serie,
        "chave_acesso": chave,
        "data_emissao": emissao,
        "data_competencia": emissao,
        "valor_total": valor,
        "nome_emitente_original": nome_original,
        "nome_emitente": normalizar_nome_apresentacao(nome_original),
        "cpf_cnpj_emitente": cnpj_cpf,
        "cpf_cnpj_destinatario": destinatario,
        "descricao": descricao[:255],
        "modelo_detectado": "NF-e",
    }


def _parse_nfse(xml_bytes):
    dados = parse_nfse_xml(xml_bytes)
    prestador = dados.get("prestador") or {}
    tomador = dados.get("tomador") or {}
    servico = dados.get("servico") or {}
    valores = dados.get("valores") or {}
    nome_original = prestador.get("nome") or ""
    numero = dados.get("numero_nfse") or dados.get("numero_nf") or ""
    if numero == "-":
        numero = ""
    return {
        "tipo_documento": "NFSE_ADMIN",
        "numero_documento": numero,
        "serie": dados.get("serie_dps") if dados.get("serie_dps") not in (None, "-") else "",
        "chave_acesso": dados.get("chave_acesso") if dados.get("chave_acesso") not in (None, "-") else "",
        "data_emissao": _data_iso(dados.get("data_emissao")),
        "data_competencia": _data_iso(dados.get("competencia")) or _data_iso(dados.get("data_emissao")),
        "valor_total": _decimal_xml(valores.get("valor_liquido") or valores.get("valor_servico")),
        "nome_emitente_original": nome_original,
        "nome_emitente": normalizar_nome_apresentacao(nome_original),
        "cpf_cnpj_emitente": _digits(prestador.get("cpf_cnpj")),
        "cpf_cnpj_destinatario": _digits(tomador.get("cpf_cnpj")),
        "descricao": str(servico.get("descricao") or f"NFS-e {numero}")[:255],
        "modelo_detectado": "NFS-e",
    }


def extrair_documento_xml(xml_bytes):
    if not xml_bytes:
        raise ValueError("Arquivo XML vazio.")
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"XML fiscal inválido: {exc}") from exc

    nomes = {_local(el.tag) for el in root.iter()}
    if "NFe" in nomes or "infNFe" in nomes:
        dados = _parse_nfe(root)
    else:
        dados = _parse_nfse(xml_bytes)

    obrigatorios = ("numero_documento", "data_emissao", "cpf_cnpj_emitente")
    faltantes = [campo for campo in obrigatorios if not dados.get(campo)]
    if faltantes:
        raise ValueError("Não foi possível identificar campos obrigatórios no XML: " + ", ".join(faltantes))
    if Decimal(dados.get("valor_total") or "0") <= 0:
        raise ValueError("Não foi possível identificar um valor fiscal válido no XML.")
    return dados


def _buscar_pessoa_por_documento(cur, empresa_id, cpf_cnpj):
    documento = _digits(cpf_cnpj)
    if not documento:
        return None
    cur.execute(
        """
        SELECT id, nome_completo, cpf_cnpj
        FROM pessoas
        WHERE empresa_id = %s
          AND REPLACE(REPLACE(REPLACE(REPLACE(cpf_cnpj, '.', ''), '/', ''), '-', ''), ' ', '') = %s
        ORDER BY id
        LIMIT 1
        """,
        (empresa_id, documento),
    )
    return cur.fetchone()


def _salvar_temporario(arquivo, empresa_id, tipo):
    """Salva apenas para processamento. Nunca é o armazenamento permanente."""
    if not arquivo or not arquivo.filename:
        return None
    nome = secure_filename(arquivo.filename)
    ext = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
    esperado = "xml" if tipo == "XML" else "pdf"
    if ext != esperado:
        raise ValueError(f"O arquivo {tipo} precisa ter extensão .{esperado}.")
    relativo = Path("uploads") / "documentos_fiscais" / "tmp" / str(empresa_id) / f"{uuid.uuid4().hex}.{ext}"
    absoluto = Path(current_app.root_path) / relativo
    absoluto.parent.mkdir(parents=True, exist_ok=True)
    arquivo.save(str(absoluto))
    return relativo.as_posix()


def _remover_temporario(relativo):
    if not relativo:
        return
    try:
        caminho = Path(current_app.root_path) / relativo
        if caminho.exists():
            caminho.unlink()
    except Exception:
        pass


def _empresa_nome(cur, empresa_id):
    cur.execute(
        """
        SELECT COALESCE(NULLIF(nome_fantasia, ''), NULLIF(razao_social, ''), CONCAT('Empresa_', id)) AS nome
        FROM empresas
        WHERE id = %s
        LIMIT 1
        """,
        (empresa_id,),
    )
    row = cur.fetchone() or {}
    return row.get("nome") or f"Empresa_{empresa_id}"


def _subcategoria_storage(tipo_documento):
    return {
        "NFE_USO_CONSUMO": "NFe_Uso_Consumo",
        "NFSE_ADMIN": "NFSe_Administrativa",
    }.get(tipo_documento, "Outros_Documentos_Fiscais")


def registrar_importacao_xml(documentos_bp, services):
    login_required = services["login_required"]
    perfis_permitidos = services["perfis_permitidos"]
    usuario_eh_super_admin_global = services["usuario_eh_super_admin_global"]
    obter_conexao = services["obter_conexao"]

    @documentos_bp.route("/documentos-fiscais/importar", methods=["GET", "POST"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def importar_documento_fiscal():
        empresa_logada_id = session.get("empresa_id")
        is_super_admin = usuario_eh_super_admin_global()
        if not empresa_logada_id:
            flash("Empresa não identificada na sessão.", "danger")
            return redirect(url_for("logout"))

        con = obter_conexao()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("documentos.central_documentos_fiscais"))
        cur = con.cursor(dictionary=True)
        try:
            empresas = []
            if is_super_admin:
                cur.execute("SELECT id, nome_fantasia, razao_social FROM empresas WHERE status_empresa = 'Ativa' ORDER BY COALESCE(NULLIF(nome_fantasia, ''), razao_social)")
                empresas = cur.fetchall() or []

            if request.method == "GET":
                return render_template("documento_fiscal_importar.html", rascunho=None, pessoa=None, empresas=empresas, is_super_admin=is_super_admin, empresa_id_padrao=empresa_logada_id)

            acao = (request.form.get("acao") or "analisar").strip()
            if acao == "analisar":
                empresa_raw = (request.form.get("empresa_id") or empresa_logada_id or "").strip() if isinstance(request.form.get("empresa_id") or empresa_logada_id, str) else str(request.form.get("empresa_id") or empresa_logada_id)
                empresa_id = int(empresa_raw) if empresa_raw.isdigit() else 0
                if not is_super_admin:
                    empresa_id = int(empresa_logada_id)
                arquivo_xml = request.files.get("arquivo_xml")
                arquivo_pdf = request.files.get("arquivo_pdf")
                if not empresa_id or not arquivo_xml or not arquivo_xml.filename:
                    flash("Selecione a empresa e informe o XML fiscal.", "warning")
                    return render_template("documento_fiscal_importar.html", rascunho=None, pessoa=None, empresas=empresas, is_super_admin=is_super_admin, empresa_id_padrao=empresa_logada_id)

                xml_bytes = arquivo_xml.read()
                arquivo_xml.stream.seek(0)
                dados = extrair_documento_xml(xml_bytes)

                if dados.get("chave_acesso"):
                    cur.execute("SELECT id FROM documentos_fiscais WHERE empresa_id = %s AND chave_acesso = %s LIMIT 1", (empresa_id, dados["chave_acesso"]))
                    duplicado = cur.fetchone()
                    if duplicado:
                        flash(f"Este XML já está importado como Documento Fiscal #{duplicado['id']}.", "warning")
                        return redirect(url_for("documentos.detalhes_documento_fiscal", id=duplicado["id"]))

                pessoa = _buscar_pessoa_por_documento(cur, empresa_id, dados["cpf_cnpj_emitente"])
                nome_xml_original = secure_filename(arquivo_xml.filename) or "documento.xml"
                nome_pdf_original = secure_filename(arquivo_pdf.filename) if arquivo_pdf and arquivo_pdf.filename else None
                temp_xml = _salvar_temporario(arquivo_xml, empresa_id, "XML")
                temp_pdf = _salvar_temporario(arquivo_pdf, empresa_id, "PDF") if arquivo_pdf and arquivo_pdf.filename else None
                rascunho = {
                    **dados,
                    "empresa_id": empresa_id,
                    "temp_xml": temp_xml,
                    "temp_pdf": temp_pdf,
                    "nome_xml_original": nome_xml_original,
                    "nome_pdf_original": nome_pdf_original,
                }
                session[SESSAO_RASCUNHO] = rascunho
                session.modified = True
                return render_template("documento_fiscal_importar.html", rascunho=rascunho, pessoa=pessoa, empresas=empresas, is_super_admin=is_super_admin, empresa_id_padrao=empresa_id)

            rascunho = session.get(SESSAO_RASCUNHO) or {}
            empresa_id = int(rascunho.get("empresa_id") or 0)
            if not empresa_id or (not is_super_admin and empresa_id != int(empresa_logada_id)):
                flash("Rascunho de importação inválido ou expirado.", "warning")
                return redirect(url_for("documentos.importar_documento_fiscal"))

            pessoa = _buscar_pessoa_por_documento(cur, empresa_id, rascunho.get("cpf_cnpj_emitente"))
            if not pessoa:
                flash("Fornecedor ainda não está cadastrado. Cadastre a Pessoa pelo CNPJ e depois conclua a importação.", "warning")
                return render_template("documento_fiscal_importar.html", rascunho=rascunho, pessoa=None, empresas=empresas, is_super_admin=is_super_admin, empresa_id_padrao=empresa_id)

            if rascunho.get("chave_acesso"):
                cur.execute("SELECT id FROM documentos_fiscais WHERE empresa_id = %s AND chave_acesso = %s LIMIT 1", (empresa_id, rascunho["chave_acesso"]))
                duplicado = cur.fetchone()
                if duplicado:
                    session.pop(SESSAO_RASCUNHO, None)
                    flash(f"Documento já importado como #{duplicado['id']}.", "warning")
                    return redirect(url_for("documentos.detalhes_documento_fiscal", id=duplicado["id"]))

            cur.execute(
                """
                INSERT INTO documentos_fiscais (
                    empresa_id, pessoa_id, tipo_documento, origem_documento,
                    numero_documento, serie, chave_acesso, data_emissao, data_competencia,
                    valor_total, nome_emitente, cpf_cnpj_emitente, cpf_cnpj_destinatario,
                    descricao, status_documento, observacao, usuario_criacao_id, usuario_atualizacao_id
                ) VALUES (%s, %s, %s, 'IMPORTACAO_XML', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Recebido', %s, %s, %s)
                """,
                (
                    empresa_id, pessoa["id"], rascunho["tipo_documento"], rascunho["numero_documento"],
                    rascunho.get("serie") or None, rascunho.get("chave_acesso") or None,
                    rascunho["data_emissao"], rascunho.get("data_competencia") or None,
                    rascunho["valor_total"], rascunho.get("nome_emitente"), rascunho.get("cpf_cnpj_emitente"),
                    rascunho.get("cpf_cnpj_destinatario") or None, rascunho.get("descricao") or None,
                    f"Importado automaticamente de XML {rascunho.get('modelo_detectado')}. Nome original do emitente preservado no XML: {rascunho.get('nome_emitente_original') or '-'}",
                    session.get("usuario_id"), session.get("usuario_id"),
                ),
            )
            documento_id = int(cur.lastrowid)

            storage = StorageService()
            empresa_nome = _empresa_nome(cur, empresa_id)
            pasta_registro = f"documento_{documento_id}_{pessoa.get('nome_completo') or 'fornecedor'}"
            data_referencia = datetime.strptime(rascunho["data_emissao"], "%Y-%m-%d")

            temp_xml = rascunho.get("temp_xml")
            if not temp_xml:
                raise StorageServiceError("XML temporário não localizado. A importação não foi concluída.")
            info_xml = storage.armazenar_arquivo(
                cur,
                caminho_local=str(Path(current_app.root_path) / temp_xml),
                empresa_id=empresa_id,
                empresa_nome=empresa_nome,
                categoria="Documentos_Fiscais",
                subcategoria=_subcategoria_storage(rascunho.get("tipo_documento")),
                pasta_registro=pasta_registro,
                origem="DOCUMENTO_FISCAL",
                origem_id=documento_id,
                tipo_arquivo="XML_FISCAL",
                nome_original=rascunho.get("nome_xml_original") or "documento.xml",
                pessoa_id=pessoa["id"],
                criado_por_usuario_id=session.get("usuario_id"),
                data_referencia=data_referencia,
            )

            info_pdf = None
            temp_pdf = rascunho.get("temp_pdf")
            if temp_pdf:
                info_pdf = storage.armazenar_arquivo(
                    cur,
                    caminho_local=str(Path(current_app.root_path) / temp_pdf),
                    empresa_id=empresa_id,
                    empresa_nome=empresa_nome,
                    categoria="Documentos_Fiscais",
                    subcategoria=_subcategoria_storage(rascunho.get("tipo_documento")),
                    pasta_registro=pasta_registro,
                    origem="DOCUMENTO_FISCAL",
                    origem_id=documento_id,
                    tipo_arquivo="PDF_FISCAL",
                    nome_original=rascunho.get("nome_pdf_original") or "documento.pdf",
                    pessoa_id=pessoa["id"],
                    criado_por_usuario_id=session.get("usuario_id"),
                    data_referencia=data_referencia,
                )

            cur.execute(
                "UPDATE documentos_fiscais SET arquivo_xml = %s, arquivo_pdf = %s WHERE id = %s AND empresa_id = %s",
                (info_xml["url_interna"], info_pdf["url_interna"] if info_pdf else None, documento_id, empresa_id),
            )
            con.commit()

            _remover_temporario(temp_xml)
            _remover_temporario(temp_pdf)
            session.pop(SESSAO_RASCUNHO, None)
            flash(f"Documento Fiscal #{documento_id} importado, armazenado no Google Drive e vinculado ao fornecedor {pessoa['nome_completo']}.", "success")
            return redirect(url_for("documentos.detalhes_documento_fiscal", id=documento_id))
        except (ValueError, StorageServiceError) as exc:
            try:
                con.rollback()
            except Exception:
                pass
            flash(str(exc), "warning")
            return redirect(url_for("documentos.importar_documento_fiscal"))
        except Exception as exc:
            try:
                con.rollback()
            except Exception:
                pass
            print(f"Erro ao importar XML fiscal: {exc}")
            flash(f"Erro técnico ao importar XML fiscal: {exc}", "danger")
            return redirect(url_for("documentos.importar_documento_fiscal"))
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                con.close()
            except Exception:
                pass
