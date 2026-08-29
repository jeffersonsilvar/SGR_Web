from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
import uuid

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename


STATUS_DOCUMENTAIS = ("Recebido", "Em análise", "Aprovado", "Recusado", "Cancelado")
STATUS_LEGADOS_APROVADOS = (
    "Aprovada",
    "Pagamento solicitado",
    "Pagamento confirmado",
    "Estornada",
)
TIPOS_DOCUMENTO_ADMIN = {
    "NFSE_ADMIN": "NFS-e Administrativa",
    "NFE_USO_CONSUMO": "NF-e Uso/Consumo",
    "OUTRO": "Outro Documento Fiscal",
}
EXTENSOES_UPLOAD = {"xml", "pdf"}


def _data_iso(valor):
    if not valor:
        return False
    try:
        datetime.strptime(valor, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _fechar(cur=None, con=None):
    try:
        if cur:
            cur.close()
    except Exception:
        pass
    try:
        if con:
            con.close()
    except Exception:
        pass


def _decimal(valor):
    try:
        texto = str(valor or "0").strip().replace("R$", "").replace(" ", "")
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        return Decimal(texto).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0.00")


def _somente_digitos(valor):
    return "".join(ch for ch in str(valor or "") if ch.isdigit())


def _status_documental_compativel(status_legado):
    """Projeta o status antigo da NF no novo domínio documental genérico."""
    status_legado = (status_legado or "").strip()
    if status_legado in STATUS_LEGADOS_APROVADOS:
        return "Aprovado"
    if status_legado == "Enviada":
        return "Recebido"
    if status_legado == "Em análise":
        return "Em análise"
    if status_legado == "Recusada":
        return "Recusado"
    return status_legado or "Recebido"


def _status_legado_para_filtro(status_documental):
    if status_documental == "Recebido":
        return ("Enviada",)
    if status_documental == "Em análise":
        return ("Em análise",)
    if status_documental == "Aprovado":
        return STATUS_LEGADOS_APROVADOS
    if status_documental == "Recusado":
        return ("Recusada",)
    return ()


def _tabela_existe(cur, nome):
    cur.execute("SHOW TABLES LIKE %s", (nome,))
    return cur.fetchone() is not None


def _arquivo_valido(arquivo, extensao_esperada=None):
    if not arquivo or not arquivo.filename:
        return True
    nome = secure_filename(arquivo.filename)
    if "." not in nome:
        return False
    ext = nome.rsplit(".", 1)[1].lower()
    if ext not in EXTENSOES_UPLOAD:
        return False
    return extensao_esperada is None or ext == extensao_esperada


def _salvar_upload_documento(arquivo, empresa_id, documento_id, tipo_arquivo):
    if not arquivo or not arquivo.filename:
        return None

    nome_seguro = secure_filename(arquivo.filename)
    extensao = nome_seguro.rsplit(".", 1)[1].lower()
    nome_final = f"{uuid.uuid4().hex}_{tipo_arquivo.lower()}.{extensao}"
    relativo = Path("uploads") / "documentos_fiscais" / str(empresa_id) / str(documento_id) / nome_final
    absoluto = Path(current_app.root_path) / relativo
    absoluto.parent.mkdir(parents=True, exist_ok=True)
    arquivo.save(str(absoluto))
    return relativo.as_posix()


def _empresa_alvo(is_super_admin, empresa_logada_id, valor_form=None):
    if not is_super_admin:
        return int(empresa_logada_id or 0)
    valor = str(valor_form or empresa_logada_id or "").strip()
    return int(valor) if valor.isdigit() else 0


def criar_documentos_blueprint(services):
    login_required = services["login_required"]
    perfis_permitidos = services["perfis_permitidos"]
    usuario_eh_super_admin_global = services["usuario_eh_super_admin_global"]
    obter_conexao = services["obter_conexao"]

    documentos_bp = Blueprint("documentos", __name__)

    @documentos_bp.route("/documentos-fiscais", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def central_documentos_fiscais():
        usuario_logado = session.get("usuario_nome", "Usuário")
        empresa_logada_id = session.get("empresa_id")
        is_super_admin = usuario_eh_super_admin_global()

        if not empresa_logada_id:
            flash("Empresa não identificada na sessão. Faça login novamente.", "danger")
            return redirect(url_for("logout"))

        hoje = date.today()
        data_inicio = (request.args.get("data_inicio") or (hoje - timedelta(days=90)).strftime("%Y-%m-%d")).strip()
        data_fim = (request.args.get("data_fim") or hoje.strftime("%Y-%m-%d")).strip()
        status = (request.args.get("status") or "").strip()
        pesquisa = (request.args.get("pesquisa") or "").strip()
        tipo = (request.args.get("tipo") or "").strip()
        empresa_id_filtro = (request.args.get("empresa_id") or "").strip() if is_super_admin else str(empresa_logada_id)

        if not _data_iso(data_inicio):
            data_inicio = (hoje - timedelta(days=90)).strftime("%Y-%m-%d")
        if not _data_iso(data_fim):
            data_fim = hoje.strftime("%Y-%m-%d")
        if status not in STATUS_DOCUMENTAIS:
            status = ""
        if tipo not in ("", "NFSE_PRESTADOR", *TIPOS_DOCUMENTO_ADMIN.keys()):
            tipo = ""

        con = obter_conexao()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("financeiro.financeiro_dashboard"))

        cur = con.cursor(dictionary=True)
        try:
            documentos = []

            # Compatibilidade 16.1: mantém a leitura das NFS-e de prestadores legadas.
            if tipo in ("", "NFSE_PRESTADOR"):
                where = ["nf.data_envio >= %s", "nf.data_envio < DATE_ADD(%s, INTERVAL 1 DAY)"]
                params = [data_inicio, data_fim]

                if is_super_admin:
                    if empresa_id_filtro and empresa_id_filtro.isdigit():
                        where.append("nf.empresa_id = %s")
                        params.append(int(empresa_id_filtro))
                else:
                    where.append("nf.empresa_id = %s")
                    params.append(int(empresa_logada_id))

                if status:
                    status_legados = _status_legado_para_filtro(status)
                    if not status_legados:
                        where.append("1 = 0")
                    elif len(status_legados) == 1:
                        where.append("nf.status_nf = %s")
                        params.append(status_legados[0])
                    else:
                        placeholders = ", ".join(["%s"] * len(status_legados))
                        where.append(f"nf.status_nf IN ({placeholders})")
                        params.extend(status_legados)

                if pesquisa:
                    like = f"%{pesquisa}%"
                    where.append(
                        """
                        (
                            nf.numero_nf LIKE %s
                            OR nf.chave_acesso LIKE %s
                            OR nf.prestador_cpf_cnpj LIKE %s
                            OR p.nome_completo LIKE %s
                            OR p.cpf_cnpj LIKE %s
                        )
                        """
                    )
                    params.extend([like, like, like, like, like])

                where_sql = " AND ".join(where)
                cur.execute(
                    f"""
                    SELECT
                        nf.id,
                        nf.empresa_id,
                        nf.motorista_id AS pessoa_id,
                        nf.numero_nf AS numero_documento,
                        nf.chave_acesso,
                        nf.data_emissao,
                        nf.valor_total,
                        nf.prestador_cpf_cnpj,
                        nf.tomador_cpf_cnpj,
                        nf.status_nf AS status_legado,
                        nf.data_envio,
                        nf.observacao,
                        p.nome_completo AS prestador_nome,
                        p.cpf_cnpj AS prestador_documento_cadastro,
                        e.nome_fantasia AS empresa_nome,
                        e.razao_social AS empresa_razao_social,
                        COUNT(v.id) AS qtd_rotas,
                        COALESCE(SUM(v.valor_rota), 0) AS valor_rotas
                    FROM motorista_notas_fiscais nf
                    INNER JOIN pessoas p
                            ON p.id = nf.motorista_id
                           AND p.empresa_id = nf.empresa_id
                    INNER JOIN empresas e
                            ON e.id = nf.empresa_id
                    LEFT JOIN motorista_nf_rotas v
                           ON v.motorista_nf_id = nf.id
                          AND v.empresa_id = nf.empresa_id
                    WHERE {where_sql}
                    GROUP BY
                        nf.id, nf.empresa_id, nf.motorista_id, nf.numero_nf,
                        nf.chave_acesso, nf.data_emissao, nf.valor_total,
                        nf.prestador_cpf_cnpj, nf.tomador_cpf_cnpj, nf.status_nf,
                        nf.data_envio, nf.observacao, p.nome_completo, p.cpf_cnpj,
                        e.nome_fantasia, e.razao_social
                    ORDER BY nf.data_envio DESC, nf.id DESC
                    LIMIT 500
                    """,
                    params,
                )
                legados = cur.fetchall() or []
                for documento in legados:
                    documento["fonte"] = "LEGADO"
                    documento["tipo_documento_codigo"] = "NFSE_PRESTADOR"
                    documento["tipo_documento"] = "NFS-e Prestador"
                    documento["origem_documento"] = "Portal do Prestador (legado Motorista)"
                    documento["status_documento"] = _status_documental_compativel(documento.get("status_legado"))
                    documento["valor_total"] = _decimal(documento.get("valor_total"))
                    documento["valor_rotas"] = _decimal(documento.get("valor_rotas"))
                documentos.extend(legados)

            # Etapa 16.2: documentos fiscais administrativos na estrutura genérica.
            if tipo != "NFSE_PRESTADOR" and _tabela_existe(cur, "documentos_fiscais"):
                where_novo = ["df.created_at >= %s", "df.created_at < DATE_ADD(%s, INTERVAL 1 DAY)"]
                params_novo = [data_inicio, data_fim]

                if is_super_admin:
                    if empresa_id_filtro and empresa_id_filtro.isdigit():
                        where_novo.append("df.empresa_id = %s")
                        params_novo.append(int(empresa_id_filtro))
                else:
                    where_novo.append("df.empresa_id = %s")
                    params_novo.append(int(empresa_logada_id))

                if status:
                    where_novo.append("df.status_documento = %s")
                    params_novo.append(status)
                if tipo in TIPOS_DOCUMENTO_ADMIN:
                    where_novo.append("df.tipo_documento = %s")
                    params_novo.append(tipo)
                if pesquisa:
                    like = f"%{pesquisa}%"
                    where_novo.append(
                        """
                        (
                            df.numero_documento LIKE %s
                            OR df.chave_acesso LIKE %s
                            OR df.cpf_cnpj_emitente LIKE %s
                            OR df.nome_emitente LIKE %s
                            OR p.nome_completo LIKE %s
                            OR p.cpf_cnpj LIKE %s
                        )
                        """
                    )
                    params_novo.extend([like, like, like, like, like, like])

                cur.execute(
                    f"""
                    SELECT
                        df.id,
                        df.empresa_id,
                        df.pessoa_id,
                        df.tipo_documento AS tipo_documento_codigo,
                        df.numero_documento,
                        df.chave_acesso,
                        df.data_emissao,
                        df.valor_total,
                        df.cpf_cnpj_emitente AS prestador_cpf_cnpj,
                        df.cpf_cnpj_destinatario AS tomador_cpf_cnpj,
                        df.status_documento,
                        df.created_at AS data_envio,
                        df.observacao,
                        COALESCE(p.nome_completo, df.nome_emitente) AS prestador_nome,
                        p.cpf_cnpj AS prestador_documento_cadastro,
                        e.nome_fantasia AS empresa_nome,
                        e.razao_social AS empresa_razao_social,
                        0 AS qtd_rotas,
                        0 AS valor_rotas
                    FROM documentos_fiscais df
                    LEFT JOIN pessoas p
                           ON p.id = df.pessoa_id
                          AND p.empresa_id = df.empresa_id
                    INNER JOIN empresas e
                            ON e.id = df.empresa_id
                    WHERE {' AND '.join(where_novo)}
                    ORDER BY df.created_at DESC, df.id DESC
                    LIMIT 500
                    """,
                    params_novo,
                )
                novos = cur.fetchall() or []
                for documento in novos:
                    documento["fonte"] = "NOVO"
                    documento["tipo_documento"] = TIPOS_DOCUMENTO_ADMIN.get(
                        documento.get("tipo_documento_codigo"), "Documento Fiscal"
                    )
                    documento["origem_documento"] = "Cadastro interno"
                    documento["status_legado"] = None
                    documento["valor_total"] = _decimal(documento.get("valor_total"))
                    documento["valor_rotas"] = Decimal("0.00")
                documentos.extend(novos)

            documentos.sort(
                key=lambda d: (
                    d.get("data_envio") or datetime.min,
                    int(d.get("id") or 0),
                ),
                reverse=True,
            )
            documentos = documentos[:500]

            resumo = {
                "total": len(documentos),
                "valor_total": sum((_decimal(d.get("valor_total")) for d in documentos), Decimal("0.00")),
                "recebidos": sum(1 for d in documentos if d.get("status_documento") == "Recebido"),
                "em_analise": sum(1 for d in documentos if d.get("status_documento") == "Em análise"),
                "aprovados": sum(1 for d in documentos if d.get("status_documento") == "Aprovado"),
                "recusados": sum(1 for d in documentos if d.get("status_documento") == "Recusado"),
            }

            empresas = []
            if is_super_admin:
                cur.execute(
                    """
                    SELECT id, nome_fantasia, razao_social
                    FROM empresas
                    WHERE status_empresa = 'Ativa'
                    ORDER BY COALESCE(NULLIF(nome_fantasia, ''), razao_social) ASC
                    """
                )
                empresas = cur.fetchall() or []

            filtros = {
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "status": status,
                "pesquisa": pesquisa,
                "tipo": tipo,
                "empresa_id": empresa_id_filtro,
            }

            return render_template(
                "documentos_fiscais.html",
                usuario_logado=usuario_logado,
                documentos=documentos,
                resumo=resumo,
                filtros=filtros,
                statuses=list(STATUS_DOCUMENTAIS),
                tipos_documento=TIPOS_DOCUMENTO_ADMIN,
                empresas=empresas,
                is_super_admin=is_super_admin,
            )
        except Exception as exc:
            print(f"Erro ao carregar Central de Documentos Fiscais: {exc}")
            flash(f"Erro técnico ao carregar documentos fiscais: {exc}", "danger")
            return redirect(url_for("financeiro.financeiro_dashboard"))
        finally:
            _fechar(cur, con)

    @documentos_bp.route("/documentos-fiscais/novo", methods=["GET", "POST"])
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
                    tipos_documento=TIPOS_DOCUMENTO_ADMIN,
                    empresas=empresas,
                    is_super_admin=is_super_admin,
                    empresa_id_padrao=empresa_logada_id,
                )

            empresa_id = _empresa_alvo(is_super_admin, empresa_logada_id, request.form.get("empresa_id"))
            tipo_documento = (request.form.get("tipo_documento") or "").strip()
            pessoa_id_raw = (request.form.get("pessoa_id") or "").strip()
            pessoa_id = int(pessoa_id_raw) if pessoa_id_raw.isdigit() else None
            nome_emitente = (request.form.get("nome_emitente") or "").strip()[:180]
            cpf_cnpj_emitente = _somente_digitos(request.form.get("cpf_cnpj_emitente"))[:20] or None
            cpf_cnpj_destinatario = _somente_digitos(request.form.get("cpf_cnpj_destinatario"))[:20] or None
            numero_documento = (request.form.get("numero_documento") or "").strip()[:60]
            serie = (request.form.get("serie") or "").strip()[:30] or None
            chave_acesso = (request.form.get("chave_acesso") or "").strip().replace(" ", "")[:120] or None
            data_emissao = (request.form.get("data_emissao") or "").strip()
            data_competencia = (request.form.get("data_competencia") or "").strip() or None
            valor_total = _decimal(request.form.get("valor_total"))
            descricao = (request.form.get("descricao") or "").strip()[:255] or None
            observacao = (request.form.get("observacao") or "").strip() or None
            arquivo_xml = request.files.get("arquivo_xml")
            arquivo_pdf = request.files.get("arquivo_pdf")

            erros = []
            if not empresa_id:
                erros.append("Selecione uma empresa válida.")
            if tipo_documento not in TIPOS_DOCUMENTO_ADMIN:
                erros.append("Selecione um tipo de documento fiscal válido.")
            if not numero_documento:
                erros.append("Informe o número do documento.")
            if not _data_iso(data_emissao):
                erros.append("Informe uma data de emissão válida.")
            if data_competencia and not _data_iso(data_competencia):
                erros.append("Informe uma competência válida.")
            if valor_total <= 0:
                erros.append("O valor total deve ser maior que zero.")
            if not _arquivo_valido(arquivo_xml, "xml"):
                erros.append("O arquivo XML informado é inválido.")
            if not _arquivo_valido(arquivo_pdf, "pdf"):
                erros.append("O arquivo PDF informado é inválido.")

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
                    cpf_cnpj_emitente = cpf_cnpj_emitente or _somente_digitos(pessoa.get("cpf_cnpj"))[:20] or None

            if not pessoa_id and not nome_emitente:
                erros.append("Informe ou selecione o emitente/fornecedor.")

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
                    tipos_documento=TIPOS_DOCUMENTO_ADMIN,
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
                    %s, %s, %s, 'INTERNO', %s, %s, %s, %s, %s, %s,
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

            caminho_xml = _salvar_upload_documento(arquivo_xml, empresa_id, documento_id, "XML")
            caminho_pdf = _salvar_upload_documento(arquivo_pdf, empresa_id, documento_id, "PDF")
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
        except Exception as exc:
            try:
                con.rollback()
            except Exception:
                pass
            print(f"Erro ao cadastrar documento fiscal: {exc}")
            flash(f"Erro técnico ao cadastrar documento fiscal: {exc}", "danger")
            return redirect(url_for("documentos.central_documentos_fiscais"))
        finally:
            _fechar(cur, con)

    @documentos_bp.route("/documentos-fiscais/<int:id>", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def detalhes_documento_fiscal(id):
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
            params = [id]
            filtro_empresa = ""
            if not is_super_admin:
                filtro_empresa = " AND df.empresa_id = %s"
                params.append(int(empresa_logada_id))

            cur.execute(
                f"""
                SELECT
                    df.*,
                    p.nome_completo AS pessoa_nome,
                    p.cpf_cnpj AS pessoa_documento,
                    e.nome_fantasia AS empresa_nome,
                    e.razao_social AS empresa_razao_social
                FROM documentos_fiscais df
                LEFT JOIN pessoas p
                       ON p.id = df.pessoa_id
                      AND p.empresa_id = df.empresa_id
                INNER JOIN empresas e ON e.id = df.empresa_id
                WHERE df.id = %s {filtro_empresa}
                LIMIT 1
                """,
                params,
            )
            documento = cur.fetchone()
            if not documento:
                flash("Documento fiscal não encontrado ou sem acesso para esta empresa.", "warning")
                return redirect(url_for("documentos.central_documentos_fiscais"))

            documento["tipo_documento_descricao"] = TIPOS_DOCUMENTO_ADMIN.get(
                documento.get("tipo_documento"), documento.get("tipo_documento") or "Documento Fiscal"
            )
            documento["valor_total"] = _decimal(documento.get("valor_total"))
            return render_template("documento_fiscal_detalhes.html", documento=documento)
        finally:
            _fechar(cur, con)

    @documentos_bp.route("/documentos-fiscais/api/pessoas", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def api_pessoas_documento_fiscal():
        empresa_logada_id = session.get("empresa_id")
        is_super_admin = usuario_eh_super_admin_global()
        empresa_id = _empresa_alvo(is_super_admin, empresa_logada_id, request.args.get("empresa_id"))
        termo = (request.args.get("q") or "").strip()

        if not empresa_id or len(termo) < 2:
            return jsonify([])

        con = obter_conexao()
        if con is None:
            return jsonify([]), 503
        cur = con.cursor(dictionary=True)
        try:
            like = f"%{termo}%"
            digitos = _somente_digitos(termo)
            cur.execute(
                """
                SELECT id, nome_completo, cpf_cnpj, tipo_cadastro, tipo_prestador
                FROM pessoas
                WHERE empresa_id = %s
                  AND (
                    nome_completo LIKE %s
                    OR cpf_cnpj LIKE %s
                    OR CAST(id AS CHAR) = %s
                  )
                ORDER BY nome_completo
                LIMIT 20
                """,
                (empresa_id, like, f"%{digitos or termo}%", termo),
            )
            resultados = []
            for pessoa in cur.fetchall() or []:
                categoria = pessoa.get("tipo_cadastro") or "Pessoa"
                if pessoa.get("tipo_prestador"):
                    categoria = f"{categoria} / {pessoa.get('tipo_prestador')}"
                resultados.append(
                    {
                        "id": pessoa.get("id"),
                        "nome": pessoa.get("nome_completo"),
                        "documento": pessoa.get("cpf_cnpj") or "",
                        "categoria": categoria,
                        "label": f"#{pessoa.get('id')} — {pessoa.get('nome_completo')} — {pessoa.get('cpf_cnpj') or 'sem documento'}",
                    }
                )
            return jsonify(resultados)
        finally:
            _fechar(cur, con)

    return documentos_bp
