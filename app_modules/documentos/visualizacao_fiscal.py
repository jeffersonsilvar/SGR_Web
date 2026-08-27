from __future__ import annotations

from decimal import Decimal, InvalidOperation
from io import BytesIO
import re
import xml.etree.ElementTree as ET

from flask import flash, redirect, render_template, send_file, session, url_for

from app_modules.storage import StorageService, StorageServiceError
from danfse_parser import parse_nfse_xml


def _local(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _primeiro(parent, nome):
    if parent is None:
        return None
    for el in parent.iter():
        if _local(el.tag) == nome:
            return el
    return None


def _texto(parent, nome):
    el = _primeiro(parent, nome)
    return (el.text or "").strip() if el is not None and el.text else ""


def _digits(valor):
    return re.sub(r"\D", "", str(valor or ""))


def _decimal(valor):
    texto = str(valor or "0").strip().replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return Decimal(texto).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0.00")


def _documento(parent):
    if parent is None:
        return ""
    return _digits(_texto(parent, "CNPJ") or _texto(parent, "CPF"))


def _endereco(parent, tag_endereco):
    endereco = _primeiro(parent, tag_endereco)
    if endereco is None:
        return ""
    partes = [
        _texto(endereco, "xLgr"),
        _texto(endereco, "nro"),
        _texto(endereco, "xBairro"),
        _texto(endereco, "xMun"),
        _texto(endereco, "UF"),
    ]
    return " · ".join(item for item in partes if item)


def _parse_nfe_visual(root):
    inf = _primeiro(root, "infNFe")
    if inf is None:
        raise ValueError("Estrutura NF-e não localizada no XML.")

    ide = _primeiro(inf, "ide")
    emit = _primeiro(inf, "emit")
    dest = _primeiro(inf, "dest")
    total = _primeiro(inf, "ICMSTot")
    protocolo = _primeiro(root, "infProt")

    chave = re.sub(r"^[A-Za-z]+", "", str(inf.attrib.get("Id") or ""))
    itens = []
    for det in inf.iter():
        if _local(det.tag) != "det":
            continue
        prod = _primeiro(det, "prod")
        if prod is None:
            continue
        itens.append({
            "codigo": _texto(prod, "cProd"),
            "descricao": _texto(prod, "xProd"),
            "ncm": _texto(prod, "NCM"),
            "cfop": _texto(prod, "CFOP"),
            "unidade": _texto(prod, "uCom"),
            "quantidade": _texto(prod, "qCom"),
            "valor_unitario": _decimal(_texto(prod, "vUnCom")),
            "valor_total": _decimal(_texto(prod, "vProd")),
        })

    return {
        "modelo": "NFE",
        "titulo": "NF-e",
        "subtitulo": "Nota Fiscal Eletrônica",
        "numero": _texto(ide, "nNF"),
        "serie": _texto(ide, "serie"),
        "chave": chave,
        "emissao": (_texto(ide, "dhEmi") or _texto(ide, "dEmi"))[:19],
        "protocolo": _texto(protocolo, "nProt"),
        "status_protocolo": _texto(protocolo, "xMotivo"),
        "emitente": {
            "nome": _texto(emit, "xNome"),
            "documento": _documento(emit),
            "ie": _texto(emit, "IE"),
            "endereco": _endereco(emit, "enderEmit"),
        },
        "destinatario": {
            "nome": _texto(dest, "xNome"),
            "documento": _documento(dest),
            "ie": _texto(dest, "IE"),
            "endereco": _endereco(dest, "enderDest"),
        },
        "itens": itens,
        "servico": None,
        "transporte": None,
        "totais": {
            "produtos": _decimal(_texto(total, "vProd")),
            "frete": _decimal(_texto(total, "vFrete")),
            "desconto": _decimal(_texto(total, "vDesc")),
            "icms": _decimal(_texto(total, "vICMS")),
            "total": _decimal(_texto(total, "vNF")),
        },
    }


def _parse_cte_visual(root):
    inf = _primeiro(root, "infCte")
    if inf is None:
        raise ValueError("Estrutura CT-e não localizada no XML.")

    ide = _primeiro(inf, "ide")
    emit = _primeiro(inf, "emit")
    dest = _primeiro(inf, "dest")
    rem = _primeiro(inf, "rem")
    vprest = _primeiro(inf, "vPrest")
    protocolo = _primeiro(root, "infProt")
    chave = re.sub(r"^[A-Za-z]+", "", str(inf.attrib.get("Id") or ""))

    componentes = []
    if vprest is not None:
        for comp in vprest.iter():
            if _local(comp.tag) != "Comp":
                continue
            componentes.append({
                "nome": _texto(comp, "xNome"),
                "valor": _decimal(_texto(comp, "vComp")),
            })

    return {
        "modelo": "CTE",
        "titulo": "CT-e",
        "subtitulo": "Conhecimento de Transporte Eletrônico",
        "numero": _texto(ide, "nCT"),
        "serie": _texto(ide, "serie"),
        "chave": chave,
        "emissao": (_texto(ide, "dhEmi") or _texto(ide, "dEmi"))[:19],
        "protocolo": _texto(protocolo, "nProt"),
        "status_protocolo": _texto(protocolo, "xMotivo"),
        "emitente": {
            "nome": _texto(emit, "xNome"),
            "documento": _documento(emit),
            "ie": _texto(emit, "IE"),
            "endereco": _endereco(emit, "enderEmit"),
        },
        "destinatario": {
            "nome": _texto(dest, "xNome"),
            "documento": _documento(dest),
            "ie": _texto(dest, "IE"),
            "endereco": _endereco(dest, "enderDest"),
        },
        "itens": [],
        "servico": None,
        "transporte": {
            "remetente_nome": _texto(rem, "xNome"),
            "remetente_documento": _documento(rem),
            "municipio_inicio": _texto(ide, "xMunIni"),
            "uf_inicio": _texto(ide, "UFIni"),
            "municipio_fim": _texto(ide, "xMunFim"),
            "uf_fim": _texto(ide, "UFFim"),
            "componentes": componentes,
        },
        "totais": {
            "servico": _decimal(_texto(vprest, "vTPrest")),
            "receber": _decimal(_texto(vprest, "vRec")),
            "total": _decimal(_texto(vprest, "vTPrest")),
        },
    }


def _parse_nfse_visual(xml_bytes):
    dados = parse_nfse_xml(xml_bytes)
    prestador = dados.get("prestador") or {}
    tomador = dados.get("tomador") or {}
    servico = dados.get("servico") or {}
    valores = dados.get("valores") or {}

    numero = dados.get("numero_nfse") or dados.get("numero_nf") or ""
    if numero == "-":
        numero = ""

    return {
        "modelo": "NFSE",
        "titulo": "NFS-e",
        "subtitulo": "Nota Fiscal de Serviço Eletrônica",
        "numero": numero,
        "serie": "" if dados.get("serie_dps") in (None, "-") else dados.get("serie_dps"),
        "chave": "" if dados.get("chave_acesso") in (None, "-") else dados.get("chave_acesso"),
        "emissao": dados.get("data_emissao") or "",
        "protocolo": dados.get("protocolo") or "",
        "status_protocolo": "",
        "emitente": {
            "nome": prestador.get("nome") or "",
            "documento": _digits(prestador.get("cpf_cnpj")),
            "ie": prestador.get("inscricao_municipal") or "",
            "endereco": prestador.get("endereco") or "",
        },
        "destinatario": {
            "nome": tomador.get("nome") or "",
            "documento": _digits(tomador.get("cpf_cnpj")),
            "ie": tomador.get("inscricao_municipal") or "",
            "endereco": tomador.get("endereco") or "",
        },
        "itens": [],
        "servico": {
            "descricao": servico.get("descricao") or "",
            "codigo": servico.get("codigo_tributacao") or servico.get("codigo_servico") or "",
            "municipio": servico.get("municipio_incidencia") or "",
        },
        "transporte": None,
        "totais": {
            "servico": _decimal(valores.get("valor_servico")),
            "iss": _decimal(valores.get("valor_iss")),
            "retencoes": _decimal(valores.get("total_retencoes")),
            "total": _decimal(valores.get("valor_liquido") or valores.get("valor_servico")),
        },
    }


def interpretar_xml_fiscal(xml_bytes):
    """Converte XML fiscal em um modelo de apresentação sem alterar o original."""
    if not xml_bytes:
        raise ValueError("Arquivo XML vazio.")
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"XML fiscal inválido: {exc}") from exc

    nomes = {_local(el.tag) for el in root.iter()}
    if "NFe" in nomes or "infNFe" in nomes:
        return _parse_nfe_visual(root)
    if "CTe" in nomes or "infCte" in nomes:
        return _parse_cte_visual(root)
    return _parse_nfse_visual(xml_bytes)


def _buscar_documento_e_xml(cur, documento_id, empresa_id, is_super_admin):
    params = [documento_id]
    filtro_empresa = ""
    if not is_super_admin:
        filtro_empresa = " AND df.empresa_id = %s"
        params.append(int(empresa_id))

    cur.execute(
        f"""
        SELECT df.*, e.nome_fantasia AS empresa_nome, e.razao_social AS empresa_razao_social
        FROM documentos_fiscais df
        INNER JOIN empresas e ON e.id = df.empresa_id
        WHERE df.id = %s {filtro_empresa}
        LIMIT 1
        """,
        params,
    )
    documento = cur.fetchone()
    if not documento:
        return None, None

    cur.execute(
        """
        SELECT id, empresa_id, origem, origem_id, tipo_arquivo, nome_original,
               nome_armazenado, mime_type, storage_provider, caminho_local,
               drive_file_id, drive_folder_id, sha256_hex, versao, status_arquivo
        FROM arquivos_sistema
        WHERE empresa_id = %s
          AND origem = 'DOCUMENTO_FISCAL'
          AND origem_id = %s
          AND tipo_arquivo = 'XML_FISCAL'
          AND status_arquivo = 'ATIVO'
        ORDER BY versao DESC, id DESC
        LIMIT 1
        """,
        (documento["empresa_id"], documento_id),
    )
    return documento, cur.fetchone()


def registrar_visualizacao_fiscal(documentos_bp, services):
    login_required = services["login_required"]
    perfis_permitidos = services["perfis_permitidos"]
    usuario_eh_super_admin_global = services["usuario_eh_super_admin_global"]
    obter_conexao = services["obter_conexao"]

    @documentos_bp.route("/documentos-fiscais/<int:id>/visualizar", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def visualizar_documento_fiscal(id):
        empresa_id = session.get("empresa_id")
        if not empresa_id:
            flash("Empresa não identificada na sessão.", "danger")
            return redirect(url_for("logout"))

        con = obter_conexao()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))

        cur = con.cursor(dictionary=True)
        try:
            documento, arquivo = _buscar_documento_e_xml(
                cur, id, empresa_id, usuario_eh_super_admin_global()
            )
            if not documento:
                flash("Documento fiscal não encontrado ou sem acesso para esta empresa.", "warning")
                return redirect(url_for("documentos.central_documentos_fiscais"))
            if not arquivo:
                flash("Este documento ainda não possui XML no armazenamento central do SGR.", "warning")
                return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))

            storage = StorageService(provider=arquivo.get("storage_provider"))
            xml_bytes = storage.baixar_arquivo(arquivo)
            dados = interpretar_xml_fiscal(xml_bytes)
            return render_template(
                "documento_fiscal_visualizacao.html",
                documento=documento,
                arquivo=arquivo,
                dados=dados,
            )
        except (StorageServiceError, ValueError) as exc:
            flash(f"Não foi possível visualizar o documento fiscal: {exc}", "danger")
            return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                con.close()
            except Exception:
                pass

    @documentos_bp.route("/documentos-fiscais/<int:id>/xml-original", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def baixar_xml_original(id):
        empresa_id = session.get("empresa_id")
        if not empresa_id:
            flash("Empresa não identificada na sessão.", "danger")
            return redirect(url_for("logout"))

        con = obter_conexao()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))

        cur = con.cursor(dictionary=True)
        try:
            documento, arquivo = _buscar_documento_e_xml(
                cur, id, empresa_id, usuario_eh_super_admin_global()
            )
            if not documento or not arquivo:
                flash("XML original não localizado ou sem acesso.", "warning")
                return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))

            storage = StorageService(provider=arquivo.get("storage_provider"))
            xml_bytes = storage.baixar_arquivo(arquivo)
            nome = arquivo.get("nome_original") or f"documento_fiscal_{id}.xml"
            return send_file(
                BytesIO(xml_bytes),
                mimetype="application/xml",
                as_attachment=True,
                download_name=nome,
                max_age=0,
            )
        except StorageServiceError as exc:
            flash(f"Não foi possível baixar o XML original: {exc}", "danger")
            return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                con.close()
            except Exception:
                pass
