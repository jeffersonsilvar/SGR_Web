from __future__ import annotations

from datetime import datetime

from flask import flash, redirect, render_template, request, session, url_for

from app_modules.storage import StorageService, StorageServiceError
from . import routes as routes_module


ROTA_CADASTRO_MANUAL = "/documentos-fiscais/novo"


def _deferred_registra_rota(funcao, rota):
    """Identifica o deferred criado por Blueprint.add_url_rule para uma rota.

    A etapa 16.4 substitui apenas o handler legado de cadastro manual antes do
    Blueprint ser registrado no Flask, sem alterar as demais rotas do módulo.
    """
    for celula in getattr(funcao, "__closure__", None) or ():
        try:
            valor = celula.cell_contents
        except ValueError:
            continue
        if valor == rota:
            return True
        if isinstance(valor, (tuple, list, set)) and rota in valor:
            return True
        if isinstance(valor, dict) and rota in valor.values():
            return True
    return False


def _remover_handler_legado(documentos_bp):
    anteriores = list(documentos_bp.deferred_functions)
    documentos_bp.deferred_functions = [
        funcao for funcao in anteriores if not _deferred_registra_rota(funcao, ROTA_CADASTRO_MANUAL)
    ]
    removidos = len(anteriores) - len(documentos_bp.deferred_functions)
    if removidos != 1:
        raise RuntimeError(
            "Não foi possível substituir com segurança a rota de cadastro manual de Documento Fiscal."
        )


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
        "CTE": "CTe_Transporte",
    }.get(tipo_documento, "Outros_Documentos_Fiscais")


def registrar_cadastro_manual_storage(documentos_bp, services):
    """Substitui o cadastro manual legado por uma versão baseada no StorageService.

    Os uploads deixam de ser persistidos em ``uploads/documentos_fiscais``.
    XML/PDF permanecem locais apenas durante o processamento do StorageService.
    """
    _remover_handler_legado(documentos_bp)

    # CT-e passa a ser um tipo fiscal de primeira classe também no cadastro manual,
    # central e detalhe, pois essas telas consultam o mesmo dicionário em runtime.
    routes_module.TIPOS_DOCUMENTO_ADMIN.setdefault("CTE", "CT-e Transporte")

    login_required = services["login_required"]
    perfis_permitidos = services["perfis_permitidos"]
    usuario_eh_super_admin_global = services["usuario_eh_super_admin_global"]
    obter_conexao = services["obter_conexao"]

    @documentos_bp.route(ROTA_CADASTRO_MANUAL, methods=["GET", "POST"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def novo_documento_fiscal():
        empresa_logada_id = session.get("empresa_id")
        is_super_admin = usuario_eh_super_admin_global()
        usuario_id = session.get("usuario_id")

        if not empresa_logada_id:
            flash("Empresa não identificada na sessão. Faça login novamente.", "danger")
            return redirect(url_for("logout"))

        con = obter_conexao()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("documentos.central_documentos_fiscais"))

        cur = con.cursor(dictionary=True)
        try:
            empresas = []
            if is_super_admin:
                cur.execute(
                    """
                    SELECT id, nome_fantasia, razao_social
                    FROM empresas
                    WHERE status_empresa = 'Ativa'
                    ORDER BY COALESCE(NULLIF(nome_fantasia, ''), razao_social)
                    """
                )
                empresas = cur.fetchall() or []

            if request.method == "GET":
                return render_template(
                    "documento_fiscal_form.html",
                    tipos_documento=routes_module.TIPOS_DOCUMENTO_ADMIN,
                    empresas=empresas,
                    is_super_admin=is_super_admin,
                    empresa_id_padrao=empresa_logada_id,
                )

            empresa_id = routes_module._empresa_alvo(
                is_super_admin, empresa_logada_id, request.form.get("empresa_id")
            )
            tipo_documento = (request.form.get("tipo_documento") or "").strip()
            pessoa_id_raw = (request.form.get("pessoa_id") or "").strip()
            pessoa_id = int(pessoa_id_raw) if pessoa_id_raw.isdigit() else None
            nome_emitente = (request.form.get("nome_emitente") or "").strip()[:180]
            cpf_cnpj_emitente = routes_module._somente_digitos(
                request.form.get("cpf_cnpj_emitente")
            )[:20] or None
            cpf_cnpj_destinatario = routes_module._somente_digitos(
                request.form.get("cpf_cnpj_destinatario")
            )[:20] or None
            numero_documento = (request.form.get("numero_documento") or "").strip()[:60]
            serie = (request.form.get("serie") or "").strip()[:30] or None
            chave_acesso = (request.form.get("chave_acesso") or "").strip().replace(" ", "")[:120] or None
            data_emissao = (request.form.get("data_emissao") or "").strip()
            data_competencia = (request.form.get("data_competencia") or "").strip() or None
            valor_total = routes_module._decimal(request.form.get("valor_total"))
            descricao = (request.form.get("descricao") or "").strip()[:255] or None
            observacao = (request.form.get("observacao") or "").strip() or None
            arquivo_xml = request.files.get("arquivo_xml")
            arquivo_pdf = request.files.get("arquivo_pdf")

            erros = []
            if not empresa_id:
                erros.append("Selecione uma empresa válida.")
            if tipo_documento not in routes_module.TIPOS_DOCUMENTO_ADMIN:
                erros.append("Selecione um tipo de documento fiscal válido.")
            if not numero_documento:
                erros.append("Informe o número do documento.")
            if not routes_module._data_iso(data_emissao):
                erros.append("Informe uma data de emissão válida.")
            if data_competencia and not routes_module._data_iso(data_competencia):
                erros.append("Informe uma competência válida.")
            if valor_total <= 0:
                erros.append("O valor total deve ser maior que zero.")
            if not routes_module._arquivo_valido(arquivo_xml, "xml"):
                erros.append("O arquivo XML informado é inválido.")
            if not routes_module._arquivo_valido(arquivo_pdf, "pdf"):
                erros.append("O arquivo PDF informado é inválido.")

            pessoa = None
            if pessoa_id:
                cur.execute(
                    "SELECT id, nome_completo, cpf_cnpj FROM pessoas WHERE id = %s AND empresa_id = %s LIMIT 1",
                    (pessoa_id, empresa_id),
                )
                pessoa = cur.fetchone()
                if not pessoa:
                    erros.append("A Pessoa/Fornecedor selecionada não pertence à empresa.")
                else:
                    nome_emitente = nome_emitente or (pessoa.get("nome_completo") or "")[:180]
                    cpf_cnpj_emitente = cpf_cnpj_emitente or routes_module._somente_digitos(
                        pessoa.get("cpf_cnpj")
                    )[:20] or None
            else:
                erros.append(
                    "Selecione a Pessoa/Fornecedor. Documentos fiscais finalizados precisam estar vinculados ao cadastro de Pessoas."
                )

            if chave_acesso and not erros:
                cur.execute(
                    "SELECT id FROM documentos_fiscais WHERE empresa_id = %s AND chave_acesso = %s LIMIT 1",
                    (empresa_id, chave_acesso),
                )
                if cur.fetchone():
                    erros.append("Já existe um documento fiscal com esta chave de acesso nesta empresa.")

            if erros:
                for erro in erros:
                    flash(erro, "warning")
                return render_template(
                    "documento_fiscal_form.html",
                    tipos_documento=routes_module.TIPOS_DOCUMENTO_ADMIN,
                    empresas=empresas,
                    is_super_admin=is_super_admin,
                    empresa_id_padrao=empresa_id or empresa_logada_id,
                    form=request.form,
                )

            cur.execute(
                """
                INSERT INTO documentos_fiscais (
                    empresa_id, pessoa_id, tipo_documento, origem_documento,
                    numero_documento, serie, chave_acesso, data_emissao,
                    data_competencia, valor_total, nome_emitente,
                    cpf_cnpj_emitente, cpf_cnpj_destinatario, descricao,
                    status_documento, observacao, usuario_criacao_id,
                    usuario_atualizacao_id
                ) VALUES (
                    %s, %s, %s, 'CADASTRO_MANUAL', %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, 'Recebido', %s, %s, %s
                )
                """,
                (
                    empresa_id,
                    pessoa_id,
                    tipo_documento,
                    numero_documento,
                    serie,
                    chave_acesso,
                    data_emissao,
                    data_competencia,
                    valor_total,
                    nome_emitente,
                    cpf_cnpj_emitente,
                    cpf_cnpj_destinatario,
                    descricao,
                    observacao,
                    usuario_id,
                    usuario_id,
                ),
            )
            documento_id = cur.lastrowid

            storage = StorageService()
            empresa_nome = _empresa_nome(cur, empresa_id)
            data_referencia = datetime.strptime(data_emissao, "%Y-%m-%d")
            pasta_registro = f"documento_{documento_id}"
            comum = {
                "empresa_id": empresa_id,
                "empresa_nome": empresa_nome,
                "categoria": "Documentos_Fiscais",
                "subcategoria": _subcategoria_storage(tipo_documento),
                "pasta_registro": pasta_registro,
                "origem": "DOCUMENTO_FISCAL",
                "origem_id": documento_id,
                "pessoa_id": pessoa_id,
                "criado_por_usuario_id": usuario_id,
                "data_referencia": data_referencia,
            }

            info_xml = storage.armazenar_upload(
                cur,
                arquivo=arquivo_xml,
                tipo_arquivo="XML_FISCAL",
                **comum,
            )
            info_pdf = storage.armazenar_upload(
                cur,
                arquivo=arquivo_pdf,
                tipo_arquivo="PDF_FISCAL",
                **comum,
            )

            caminho_xml = info_xml.get("url_interna") if info_xml else None
            caminho_pdf = info_pdf.get("url_interna") if info_pdf else None
            if caminho_xml or caminho_pdf:
                cur.execute(
                    """
                    UPDATE documentos_fiscais
                    SET arquivo_xml = %s,
                        arquivo_pdf = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND empresa_id = %s
                    """,
                    (caminho_xml, caminho_pdf, documento_id, empresa_id),
                )

            con.commit()
            flash(f"Documento fiscal #{documento_id} cadastrado com sucesso.", "success")
            return redirect(url_for("documentos.detalhes_documento_fiscal", id=documento_id))
        except StorageServiceError as exc:
            try:
                con.rollback()
            except Exception:
                pass
            flash(
                f"O documento não foi cadastrado porque o armazenamento está indisponível: {exc}",
                "danger",
            )
            return redirect(url_for("documentos.central_documentos_fiscais"))
        except Exception as exc:
            try:
                con.rollback()
            except Exception:
                pass
            print(f"Erro ao cadastrar documento fiscal: {exc}")
            flash(f"Erro técnico ao cadastrar documento fiscal: {exc}", "danger")
            return redirect(url_for("documentos.central_documentos_fiscais"))
        finally:
            routes_module._fechar(cur, con)
