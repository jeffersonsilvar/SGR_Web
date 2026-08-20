from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import json

from flask import flash, redirect, render_template, request, session, url_for


TIPOS_CONTA_CAIXA = (
    "Conta corrente",
    "Conta pagamento",
    "Caixa físico",
    "Carteira digital",
    "Outro",
)

STATUS_CONTA_CAIXA = ("Ativa", "Inativa")


def _decimal(valor):
    try:
        if valor is None or str(valor).strip() == "":
            return Decimal("0.00")
        texto = str(valor).strip().replace("R$", "").replace(" ", "")
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        return Decimal(texto).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


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


def _registrar_auditoria_conta(
    cur,
    *,
    empresa_id,
    usuario_id,
    acao,
    conta_id,
    status_anterior=None,
    status_novo=None,
    valor_anterior=None,
    valor_novo=None,
    motivo=None,
    observacao=None,
    dados_antes=None,
    dados_depois=None,
):
    cur.execute(
        """
        INSERT INTO auditoria_financeira (
            empresa_id, usuario_id, modulo, acao,
            entidade_tipo, entidade_id,
            status_anterior, status_novo,
            valor_anterior, valor_novo,
            motivo, observacao,
            dados_antes, dados_depois,
            ip_origem, user_agent
        ) VALUES (
            %s, %s, 'CONTAS_CAIXA', %s,
            'CONTA_CAIXA', %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s
        )
        """,
        (
            empresa_id,
            usuario_id,
            acao,
            conta_id,
            status_anterior,
            status_novo,
            valor_anterior,
            valor_novo,
            motivo,
            observacao,
            json.dumps(dados_antes, ensure_ascii=False, default=str) if dados_antes is not None else None,
            json.dumps(dados_depois, ensure_ascii=False, default=str) if dados_depois is not None else None,
            request.remote_addr,
            request.headers.get("User-Agent"),
        ),
    )


def _conta_tem_movimentacao(cur, *, conta_id, empresa_id):
    cur.execute(
        """
        SELECT 1
        FROM movimentacoes_caixa
        WHERE conta_caixa_id = %s
          AND empresa_id = %s
        LIMIT 1
        """,
        (conta_id, empresa_id),
    )
    return cur.fetchone() is not None


def registrar_rotas_contas_caixa_auditoria(financeiro_bp, services):
    login_required = services["login_required"]
    perfis_permitidos = services["perfis_permitidos"]
    usuario_eh_super_admin_global = services["usuario_eh_super_admin_global"]
    obter_conexao = services["obter_conexao"]

    @financeiro_bp.route("/financeiro/contas-caixa/nova", methods=["GET", "POST"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def nova_conta_caixa():
        usuario_logado = session.get("usuario_nome", "Usuário")
        empresa_logada_id = session.get("empresa_id")
        usuario_id = session.get("usuario_id")
        is_super_admin = usuario_eh_super_admin_global()

        if not empresa_logada_id:
            flash("Empresa não identificada na sessão. Faça login novamente.", "danger")
            return redirect(url_for("logout"))

        con = obter_conexao()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("financeiro.financeiro_contas_caixa"))

        cur = con.cursor(dictionary=True)
        try:
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
                empresas = cur.fetchall()

            if request.method == "POST":
                empresa_id = empresa_logada_id
                if is_super_admin:
                    empresa_id_form = (request.form.get("empresa_id") or "").strip()
                    if not empresa_id_form.isdigit():
                        flash("Selecione a empresa da conta caixa.", "danger")
                        return render_template(
                            "financeiro_conta_caixa_form.html",
                            usuario_logado=usuario_logado,
                            conta=None,
                            empresas=empresas,
                            tipos_conta=TIPOS_CONTA_CAIXA,
                            is_super_admin=is_super_admin,
                        )
                    empresa_id = int(empresa_id_form)

                nome_conta = (request.form.get("nome_conta") or "").strip()
                tipo_conta = (request.form.get("tipo_conta") or "").strip()
                banco = (request.form.get("banco") or "").strip()
                agencia = (request.form.get("agencia") or "").strip()
                numero_conta = (request.form.get("numero_conta") or "").strip()
                saldo_inicial = _decimal(request.form.get("saldo_inicial"))
                observacao = (request.form.get("observacao") or "").strip()

                if not nome_conta:
                    flash("Informe o nome da conta caixa.", "danger")
                    return redirect(url_for("financeiro.nova_conta_caixa"))
                if tipo_conta not in TIPOS_CONTA_CAIXA:
                    flash("Selecione um tipo de conta válido.", "danger")
                    return redirect(url_for("financeiro.nova_conta_caixa"))

                cur.execute(
                    "SELECT id FROM empresas WHERE id = %s AND status_empresa = 'Ativa' LIMIT 1",
                    (empresa_id,),
                )
                if not cur.fetchone():
                    flash("Empresa inválida ou inativa.", "danger")
                    return redirect(url_for("financeiro.nova_conta_caixa"))

                cur.execute(
                    """
                    INSERT INTO contas_caixa (
                        empresa_id, nome_conta, tipo_conta, banco, agencia, numero_conta,
                        saldo_inicial, status_conta, observacao, usuario_criacao_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Ativa', %s, %s)
                    """,
                    (
                        empresa_id,
                        nome_conta,
                        tipo_conta,
                        banco or None,
                        agencia or None,
                        numero_conta or None,
                        saldo_inicial,
                        observacao or None,
                        usuario_id,
                    ),
                )
                conta_id = cur.lastrowid
                depois = {
                    "nome_conta": nome_conta,
                    "tipo_conta": tipo_conta,
                    "banco": banco or None,
                    "agencia": agencia or None,
                    "numero_conta": numero_conta or None,
                    "saldo_inicial": str(saldo_inicial),
                    "status_conta": "Ativa",
                    "observacao": observacao or None,
                }
                _registrar_auditoria_conta(
                    cur,
                    empresa_id=empresa_id,
                    usuario_id=usuario_id,
                    acao="CONTA_CAIXA_CRIADA",
                    conta_id=conta_id,
                    status_novo="Ativa",
                    valor_novo=saldo_inicial,
                    motivo="Criação de conta caixa",
                    observacao=f"Conta caixa '{nome_conta}' criada.",
                    dados_depois=depois,
                )
                con.commit()
                flash("Conta caixa criada com sucesso.", "success")
                return redirect(url_for("financeiro.financeiro_contas_caixa"))

            return render_template(
                "financeiro_conta_caixa_form.html",
                usuario_logado=usuario_logado,
                conta=None,
                empresas=empresas,
                tipos_conta=TIPOS_CONTA_CAIXA,
                is_super_admin=is_super_admin,
            )
        except Exception as exc:
            try:
                con.rollback()
            except Exception:
                pass
            print(f"Erro ao criar conta caixa: {exc}")
            flash(f"Erro técnico ao criar conta caixa: {exc}", "danger")
            return redirect(url_for("financeiro.financeiro_contas_caixa"))
        finally:
            _fechar(cur, con)

    @financeiro_bp.route("/financeiro/contas-caixa/<int:id>/editar", methods=["GET", "POST"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def editar_conta_caixa(id):
        usuario_logado = session.get("usuario_nome", "Usuário")
        empresa_logada_id = session.get("empresa_id")
        usuario_id = session.get("usuario_id")
        is_super_admin = usuario_eh_super_admin_global()

        if not empresa_logada_id:
            flash("Empresa não identificada na sessão. Faça login novamente.", "danger")
            return redirect(url_for("logout"))

        con = obter_conexao()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("financeiro.financeiro_contas_caixa"))

        cur = con.cursor(dictionary=True)
        try:
            if is_super_admin:
                cur.execute("SELECT * FROM contas_caixa WHERE id = %s LIMIT 1", (id,))
            else:
                cur.execute(
                    "SELECT * FROM contas_caixa WHERE id = %s AND empresa_id = %s LIMIT 1",
                    (id, empresa_logada_id),
                )
            conta = cur.fetchone()
            if not conta:
                flash("Conta caixa não encontrada para esta empresa.", "warning")
                return redirect(url_for("financeiro.financeiro_contas_caixa"))

            empresa_id = int(conta["empresa_id"])
            tem_movimentacao = _conta_tem_movimentacao(cur, conta_id=id, empresa_id=empresa_id)

            if request.method == "POST":
                nome_conta = (request.form.get("nome_conta") or "").strip()
                tipo_conta = (request.form.get("tipo_conta") or "").strip()
                banco = (request.form.get("banco") or "").strip()
                agencia = (request.form.get("agencia") or "").strip()
                numero_conta = (request.form.get("numero_conta") or "").strip()
                status_conta = (request.form.get("status_conta") or "Ativa").strip()
                observacao = (request.form.get("observacao") or "").strip()

                if not nome_conta:
                    flash("Informe o nome da conta caixa.", "danger")
                    return redirect(url_for("financeiro.editar_conta_caixa", id=id))
                if tipo_conta not in TIPOS_CONTA_CAIXA:
                    flash("Selecione um tipo de conta válido.", "danger")
                    return redirect(url_for("financeiro.editar_conta_caixa", id=id))
                if status_conta not in STATUS_CONTA_CAIXA:
                    flash("Status da conta inválido.", "danger")
                    return redirect(url_for("financeiro.editar_conta_caixa", id=id))

                saldo_anterior = _decimal(conta.get("saldo_inicial"))
                saldo_inicial = saldo_anterior
                if not tem_movimentacao:
                    saldo_inicial = _decimal(request.form.get("saldo_inicial"))

                antes = {
                    "nome_conta": conta.get("nome_conta"),
                    "tipo_conta": conta.get("tipo_conta"),
                    "banco": conta.get("banco"),
                    "agencia": conta.get("agencia"),
                    "numero_conta": conta.get("numero_conta"),
                    "saldo_inicial": str(saldo_anterior),
                    "status_conta": conta.get("status_conta"),
                    "observacao": conta.get("observacao"),
                }
                depois = {
                    "nome_conta": nome_conta,
                    "tipo_conta": tipo_conta,
                    "banco": banco or None,
                    "agencia": agencia or None,
                    "numero_conta": numero_conta or None,
                    "saldo_inicial": str(saldo_inicial),
                    "status_conta": status_conta,
                    "observacao": observacao or None,
                }

                cur.execute(
                    """
                    UPDATE contas_caixa
                    SET nome_conta = %s,
                        tipo_conta = %s,
                        banco = %s,
                        agencia = %s,
                        numero_conta = %s,
                        saldo_inicial = %s,
                        status_conta = %s,
                        observacao = %s,
                        updated_at = NOW()
                    WHERE id = %s
                      AND empresa_id = %s
                    """,
                    (
                        nome_conta,
                        tipo_conta,
                        banco or None,
                        agencia or None,
                        numero_conta or None,
                        saldo_inicial,
                        status_conta,
                        observacao or None,
                        id,
                        empresa_id,
                    ),
                )
                if cur.rowcount != 1:
                    raise RuntimeError("Conta caixa não pôde ser atualizada.")

                _registrar_auditoria_conta(
                    cur,
                    empresa_id=empresa_id,
                    usuario_id=usuario_id,
                    acao="CONTA_CAIXA_EDITADA",
                    conta_id=id,
                    status_anterior=conta.get("status_conta"),
                    status_novo=status_conta,
                    valor_anterior=saldo_anterior,
                    valor_novo=saldo_inicial,
                    motivo="Edição de conta caixa",
                    observacao=(
                        f"Conta caixa '{nome_conta}' editada. "
                        + ("Saldo inicial preservado por existir histórico de movimentação." if tem_movimentacao else "Saldo inicial elegível para edição por não haver movimentações.")
                    ),
                    dados_antes=antes,
                    dados_depois=depois,
                )
                con.commit()
                flash("Conta caixa atualizada com sucesso.", "success")
                return redirect(url_for("financeiro.financeiro_contas_caixa"))

            conta["tem_movimentacao"] = tem_movimentacao
            empresas = []
            return render_template(
                "financeiro_conta_caixa_form.html",
                usuario_logado=usuario_logado,
                conta=conta,
                empresas=empresas,
                tipos_conta=TIPOS_CONTA_CAIXA,
                is_super_admin=is_super_admin,
            )
        except Exception as exc:
            try:
                con.rollback()
            except Exception:
                pass
            print(f"Erro ao editar conta caixa {id}: {exc}")
            flash(f"Erro técnico ao editar conta caixa: {exc}", "danger")
            return redirect(url_for("financeiro.financeiro_contas_caixa"))
        finally:
            _fechar(cur, con)

    @financeiro_bp.route("/financeiro/auditoria", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def financeiro_auditoria():
        usuario_logado = session.get("usuario_nome", "Usuário")
        empresa_logada_id = session.get("empresa_id")
        is_super_admin = usuario_eh_super_admin_global()

        if not empresa_logada_id:
            flash("Empresa não identificada na sessão. Faça login novamente.", "danger")
            return redirect(url_for("logout"))

        hoje = date.today()
        data_inicio = (request.args.get("data_inicio") or (hoje - timedelta(days=30)).strftime("%Y-%m-%d")).strip()
        data_fim = (request.args.get("data_fim") or hoje.strftime("%Y-%m-%d")).strip()
        acao = (request.args.get("acao") or "").strip()
        modulo = (request.args.get("modulo") or "").strip()
        entidade_tipo = (request.args.get("entidade_tipo") or "").strip()
        usuario_id_filtro = (request.args.get("usuario_id") or "").strip()
        pesquisa = (request.args.get("pesquisa") or "").strip()
        empresa_id_filtro = (request.args.get("empresa_id") or "").strip() if is_super_admin else str(empresa_logada_id)

        if not _data_iso(data_inicio):
            data_inicio = (hoje - timedelta(days=30)).strftime("%Y-%m-%d")
        if not _data_iso(data_fim):
            data_fim = hoje.strftime("%Y-%m-%d")

        con = obter_conexao()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("financeiro.financeiro_dashboard"))

        cur = con.cursor(dictionary=True)
        try:
            where = ["a.created_at >= %s", "a.created_at < DATE_ADD(%s, INTERVAL 1 DAY)"]
            params = [data_inicio, data_fim]

            if is_super_admin:
                if empresa_id_filtro and empresa_id_filtro.isdigit():
                    where.append("a.empresa_id = %s")
                    params.append(int(empresa_id_filtro))
            else:
                where.append("a.empresa_id = %s")
                params.append(int(empresa_logada_id))

            if acao:
                where.append("a.acao = %s")
                params.append(acao)
            if modulo:
                where.append("a.modulo = %s")
                params.append(modulo)
            if entidade_tipo:
                where.append("a.entidade_tipo = %s")
                params.append(entidade_tipo)
            if usuario_id_filtro and usuario_id_filtro.isdigit():
                where.append("a.usuario_id = %s")
                params.append(int(usuario_id_filtro))
            if pesquisa:
                like = f"%{pesquisa}%"
                where.append(
                    """
                    (
                        a.motivo LIKE %s OR a.observacao LIKE %s OR a.acao LIKE %s
                        OR a.entidade_tipo LIKE %s OR CAST(a.entidade_id AS CHAR) LIKE %s
                        OR CAST(a.titulo_financeiro_id AS CHAR) LIKE %s
                        OR p.nome_completo LIKE %s OR u.login LIKE %s
                    )
                    """
                )
                params.extend([like] * 8)

            where_sql = " AND ".join(where)
            cur.execute(
                f"""
                SELECT
                    a.*,
                    e.nome_fantasia AS empresa_nome,
                    u.login AS usuario_login,
                    pu.nome_completo AS usuario_nome,
                    p.nome_completo AS pessoa_nome
                FROM auditoria_financeira a
                LEFT JOIN empresas e ON e.id = a.empresa_id
                LEFT JOIN usuarios u ON u.id = a.usuario_id
                LEFT JOIN pessoas pu ON pu.id = u.pessoa_id
                LEFT JOIN pessoas p ON p.id = a.pessoa_id
                WHERE {where_sql}
                ORDER BY a.created_at DESC, a.id DESC
                LIMIT 500
                """,
                params,
            )
            auditorias = cur.fetchall()

            cur.execute(
                f"""
                SELECT
                    COUNT(*) AS total,
                    COUNT(DISTINCT a.usuario_id) AS usuarios_distintos,
                    SUM(CASE WHEN a.acao LIKE 'BAIXA%%' THEN 1 ELSE 0 END) AS baixas,
                    SUM(CASE WHEN a.acao LIKE 'ESTORNO%%' THEN 1 ELSE 0 END) AS estornos,
                    SUM(CASE WHEN a.acao LIKE 'CONCILIACAO%%' THEN 1 ELSE 0 END) AS conciliacoes,
                    SUM(CASE WHEN a.acao LIKE 'CONFIGURACAO%%' THEN 1 ELSE 0 END) AS configuracoes
                FROM auditoria_financeira a
                LEFT JOIN usuarios u ON u.id = a.usuario_id
                LEFT JOIN pessoas p ON p.id = a.pessoa_id
                WHERE {where_sql}
                """,
                params,
            )
            resumo = cur.fetchone() or {}

            cur.execute("SELECT DISTINCT acao FROM auditoria_financeira WHERE acao IS NOT NULL AND acao <> '' ORDER BY acao ASC")
            acoes = [row.get("acao") for row in cur.fetchall()]
            cur.execute("SELECT DISTINCT modulo FROM auditoria_financeira WHERE modulo IS NOT NULL AND modulo <> '' ORDER BY modulo ASC")
            modulos = [row.get("modulo") for row in cur.fetchall()]
            cur.execute("SELECT DISTINCT entidade_tipo FROM auditoria_financeira WHERE entidade_tipo IS NOT NULL AND entidade_tipo <> '' ORDER BY entidade_tipo ASC")
            entidades = [row.get("entidade_tipo") for row in cur.fetchall()]

            usuario_where = "u.status_usuario = 'Ativo'"
            usuario_params = []
            if not is_super_admin:
                usuario_where += " AND (u.empresa_id = %s OR EXISTS (SELECT 1 FROM usuario_empresas_acesso uea WHERE uea.usuario_id = u.id AND uea.empresa_id = %s))"
                usuario_params.extend([empresa_logada_id, empresa_logada_id])
            cur.execute(
                f"""
                SELECT u.id, u.login, COALESCE(p.nome_completo, u.login) AS nome
                FROM usuarios u
                LEFT JOIN pessoas p ON p.id = u.pessoa_id
                WHERE {usuario_where}
                ORDER BY COALESCE(p.nome_completo, u.login), u.login ASC
                """,
                usuario_params,
            )
            usuarios = cur.fetchall()

            empresas = []
            if is_super_admin:
                cur.execute("SELECT id, nome_fantasia, razao_social FROM empresas ORDER BY nome_fantasia ASC")
                empresas = cur.fetchall()

            filtros = {
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "acao": acao,
                "modulo": modulo,
                "entidade_tipo": entidade_tipo,
                "usuario_id": usuario_id_filtro,
                "pesquisa": pesquisa,
                "empresa_id": empresa_id_filtro,
            }

            return render_template(
                "financeiro_auditoria.html",
                usuario_logado=usuario_logado,
                auditorias=auditorias,
                resumo=resumo,
                filtros=filtros,
                acoes=acoes,
                modulos=modulos,
                entidades=entidades,
                usuarios=usuarios,
                empresas=empresas,
                is_super_admin=is_super_admin,
            )
        except Exception as exc:
            print(f"Erro ao carregar auditoria financeira: {exc}")
            flash(f"Erro técnico ao carregar auditoria financeira: {exc}", "danger")
            return redirect(url_for("financeiro.financeiro_dashboard"))
        finally:
            _fechar(cur, con)
