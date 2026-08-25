from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, session, url_for


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
        return Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")


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
        empresa_id_filtro = (request.args.get("empresa_id") or "").strip() if is_super_admin else str(empresa_logada_id)

        if not _data_iso(data_inicio):
            data_inicio = (hoje - timedelta(days=90)).strftime("%Y-%m-%d")
        if not _data_iso(data_fim):
            data_fim = hoje.strftime("%Y-%m-%d")

        con = obter_conexao()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("financeiro.financeiro_dashboard"))

        cur = con.cursor(dictionary=True)
        try:
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
                where.append("nf.status_nf = %s")
                params.append(status)

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
                    nf.tipo_documento_pagamento,
                    nf.numero_nf AS numero_documento,
                    nf.chave_acesso,
                    nf.data_emissao,
                    nf.valor_total,
                    nf.valor_bruto,
                    nf.valor_liquido,
                    nf.prestador_cpf_cnpj,
                    nf.tomador_cpf_cnpj,
                    nf.status_nf AS status_documento,
                    nf.nome_arquivo_xml,
                    nf.data_envio,
                    nf.data_aprovacao,
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
                    nf.id, nf.empresa_id, nf.motorista_id, nf.tipo_documento_pagamento,
                    nf.numero_nf, nf.chave_acesso, nf.data_emissao, nf.valor_total,
                    nf.valor_bruto, nf.valor_liquido, nf.prestador_cpf_cnpj,
                    nf.tomador_cpf_cnpj, nf.status_nf, nf.nome_arquivo_xml,
                    nf.data_envio, nf.data_aprovacao, nf.observacao,
                    p.nome_completo, p.cpf_cnpj,
                    e.nome_fantasia, e.razao_social
                ORDER BY nf.data_envio DESC, nf.id DESC
                LIMIT 500
                """,
                params,
            )
            documentos = cur.fetchall() or []

            for documento in documentos:
                documento["tipo_documento"] = "NFS-e Prestador"
                documento["origem_documento"] = "Portal do Prestador (legado Motorista)"
                documento["valor_total"] = _decimal(documento.get("valor_total"))
                documento["valor_rotas"] = _decimal(documento.get("valor_rotas"))

            resumo = {
                "total": len(documentos),
                "valor_total": sum((_decimal(d.get("valor_total")) for d in documentos), Decimal("0.00")),
                "enviadas": sum(1 for d in documentos if d.get("status_documento") == "Enviada"),
                "em_analise": sum(1 for d in documentos if d.get("status_documento") == "Em análise"),
                "aprovadas": sum(1 for d in documentos if d.get("status_documento") in ("Aprovada", "Pagamento solicitado", "Pagamento confirmado")),
                "recusadas": sum(1 for d in documentos if d.get("status_documento") == "Recusada"),
            }

            cur.execute(
                """
                SELECT DISTINCT status_nf
                FROM motorista_notas_fiscais
                WHERE status_nf IS NOT NULL AND status_nf <> ''
                ORDER BY status_nf ASC
                """
            )
            statuses = [row.get("status_nf") for row in (cur.fetchall() or [])]

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
                "empresa_id": empresa_id_filtro,
            }

            return render_template(
                "documentos_fiscais.html",
                usuario_logado=usuario_logado,
                documentos=documentos,
                resumo=resumo,
                filtros=filtros,
                statuses=statuses,
                empresas=empresas,
                is_super_admin=is_super_admin,
            )
        except Exception as exc:
            print(f"Erro ao carregar Central de Documentos Fiscais: {exc}")
            flash(f"Erro técnico ao carregar documentos fiscais: {exc}", "danger")
            return redirect(url_for("financeiro.financeiro_dashboard"))
        finally:
            _fechar(cur, con)

    return documentos_bp
