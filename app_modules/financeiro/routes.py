from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, session, url_for


def criar_financeiro_blueprint(services):
    """Cria o Blueprint financeiro com dependências fornecidas pelo app.py."""
    financeiro_bp = Blueprint("financeiro", __name__)

    login_required = services["login_required"]
    perfis_permitidos = services["perfis_permitidos"]

    @financeiro_bp.route("/financeiro/contas-caixa", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro", "Consulta")
    def financeiro_contas_caixa():
        usuario_logado = session.get("usuario_nome", "Usuário")
        empresa_logada_id = session.get("empresa_id")
        is_super_admin = services["usuario_eh_super_admin_global"]()

        contas = services["carregar_contas_caixa_financeiro"](
            empresa_logada_id,
            is_super_admin,
            somente_ativas=False,
        )

        con_saldo = services["obter_conexao"]()
        if con_saldo is not None:
            cur_saldo = con_saldo.cursor(dictionary=True)
            try:
                for conta in contas:
                    saldo_info = services["calcular_saldo_conta_caixa"](
                        cur_saldo,
                        conta["id"],
                        conta["empresa_id"],
                    )
                    conta["saldo_atual"] = (saldo_info or {}).get(
                        "saldo_atual",
                        services["converter_decimal"](conta.get("saldo_inicial")),
                    )
            except Exception as exc:
                print(f"Erro ao calcular saldos das contas caixa: {exc}")
                for conta in contas:
                    conta["saldo_atual"] = services["converter_decimal"](
                        conta.get("saldo_inicial")
                    )
            finally:
                services["fechar_cursor_conexao"](cur_saldo, con_saldo)
        else:
            for conta in contas:
                conta["saldo_atual"] = services["converter_decimal"](
                    conta.get("saldo_inicial")
                )

        resumo = {
            "ativas": 0,
            "inativas": 0,
            "saldo_inicial_total": Decimal("0.00"),
            "saldo_atual_total": Decimal("0.00"),
            "total": len(contas),
        }

        for conta in contas:
            if conta.get("status_conta") == "Ativa":
                resumo["ativas"] += 1
            else:
                resumo["inativas"] += 1

            resumo["saldo_inicial_total"] += services["converter_decimal"](
                conta.get("saldo_inicial")
            )
            resumo["saldo_atual_total"] += services["converter_decimal"](
                conta.get("saldo_atual")
            )

        return render_template(
            "financeiro_contas_caixa.html",
            usuario_logado=usuario_logado,
            contas=contas,
            resumo=resumo,
            is_super_admin=is_super_admin,
        )

    @financeiro_bp.route("/financeiro/movimentacoes-caixa", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro", "Consulta")
    def financeiro_movimentacoes_caixa():
        usuario_logado = session.get("usuario_nome", "Usuário")
        empresa_logada_id = session.get("empresa_id")
        is_super_admin = services["usuario_eh_super_admin_global"]()

        conta_caixa_id = (request.args.get("conta_caixa_id") or "").strip()
        tipo_movimentacao = (request.args.get("tipo_movimentacao") or "").strip()
        data_inicio = (request.args.get("data_inicio") or "").strip()
        data_fim = (request.args.get("data_fim") or "").strip()
        pesquisa = (request.args.get("pesquisa") or "").strip()
        empresa_id_filtro = (request.args.get("empresa_id") or "").strip()

        con = services["obter_conexao"]()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("financeiro.financeiro_titulos"))

        cur = con.cursor(dictionary=True)
        try:
            query = """
                SELECT m.*,
                       cx.nome_conta AS conta_caixa_nome,
                       t.numero_documento,
                       t.descricao AS titulo_descricao,
                       t.tipo_titulo,
                       p.nome_completo AS pessoa_nome,
                       e.nome_fantasia AS empresa_nome,
                       e.razao_social AS empresa_razao_social,
                       u.login AS usuario_login
                FROM movimentacoes_caixa m
                INNER JOIN contas_caixa cx
                        ON cx.id = m.conta_caixa_id
                       AND cx.empresa_id = m.empresa_id
                LEFT JOIN titulos_financeiros t
                       ON t.id = m.titulo_financeiro_id
                      AND t.empresa_id = m.empresa_id
                LEFT JOIN pessoas p
                       ON p.id = t.pessoa_id
                      AND p.empresa_id = t.empresa_id
                LEFT JOIN empresas e ON e.id = m.empresa_id
                LEFT JOIN usuarios u ON u.id = m.usuario_criacao_id
                WHERE 1 = 1
            """
            params = []

            if is_super_admin:
                if empresa_id_filtro and empresa_id_filtro.isdigit():
                    query += " AND m.empresa_id = %s"
                    params.append(int(empresa_id_filtro))
            else:
                query += " AND m.empresa_id = %s"
                params.append(empresa_logada_id)

            if conta_caixa_id and conta_caixa_id.isdigit():
                query += " AND m.conta_caixa_id = %s"
                params.append(int(conta_caixa_id))

            if tipo_movimentacao in ["ENTRADA", "SAIDA"]:
                query += " AND m.tipo_movimentacao = %s"
                params.append(tipo_movimentacao)

            if data_inicio:
                query += " AND m.data_movimentacao >= %s"
                params.append(data_inicio)

            if data_fim:
                query += " AND m.data_movimentacao <= %s"
                params.append(data_fim)

            if pesquisa:
                query += """
                    AND (
                        m.historico LIKE %s
                        OR m.observacao LIKE %s
                        OR t.numero_documento LIKE %s
                        OR t.descricao LIKE %s
                        OR p.nome_completo LIKE %s
                    )
                """
                termo = f"%{pesquisa}%"
                params.extend([termo, termo, termo, termo, termo])

            query += " ORDER BY m.data_movimentacao DESC, m.id DESC"
            cur.execute(query, params)
            movimentacoes = cur.fetchall()

            resumo = {
                "entradas": Decimal("0.00"),
                "saidas": Decimal("0.00"),
                "estornos": Decimal("0.00"),
                "saldo_movimentado": Decimal("0.00"),
                "total": len(movimentacoes),
            }

            for mov in movimentacoes:
                valor = services["converter_decimal"](
                    mov.get("valor_movimentacao")
                )
                status_mov = str(
                    mov.get("status_movimentacao") or "Ativa"
                )
                eh_estorno = (
                    bool(mov.get("estorno_de_movimentacao_id"))
                    or status_mov == "Estorno"
                )

                if eh_estorno:
                    resumo["estornos"] += valor
                elif status_mov != "Estornada":
                    if mov.get("tipo_movimentacao") == "ENTRADA":
                        resumo["entradas"] += valor
                    elif mov.get("tipo_movimentacao") == "SAIDA":
                        resumo["saidas"] += valor

                if mov.get("tipo_movimentacao") == "ENTRADA":
                    resumo["saldo_movimentado"] += valor
                elif mov.get("tipo_movimentacao") == "SAIDA":
                    resumo["saldo_movimentado"] -= valor

            contas_caixa = services["carregar_contas_caixa_financeiro"](
                empresa_logada_id,
                is_super_admin,
                somente_ativas=False,
            )
            empresas = (
                services["carregar_empresas_ativas"]()
                if is_super_admin
                else []
            )

        except Exception as exc:
            print(f"Erro ao carregar movimentações de caixa: {exc}")
            flash(
                f"Erro técnico ao carregar movimentações de caixa: {exc}",
                "danger",
            )
            movimentacoes = []
            resumo = {
                "entradas": 0,
                "saidas": 0,
                "estornos": 0,
                "saldo_movimentado": 0,
                "total": 0,
            }
            contas_caixa = []
            empresas = []
        finally:
            services["fechar_cursor_conexao"](cur, con)

        filtros = {
            "conta_caixa_id": conta_caixa_id,
            "tipo_movimentacao": tipo_movimentacao,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "pesquisa": pesquisa,
            "empresa_id": empresa_id_filtro,
        }

        return render_template(
            "financeiro_movimentacoes_caixa.html",
            usuario_logado=usuario_logado,
            movimentacoes=movimentacoes,
            resumo=resumo,
            contas_caixa=contas_caixa,
            empresas=empresas,
            filtros=filtros,
            is_super_admin=is_super_admin,
        )

    @financeiro_bp.route("/financeiro/conciliacao-caixa", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro", "Consulta")
    def financeiro_conciliacao_caixa():
        usuario_logado = session.get("usuario_nome", "Usuário")
        empresa_logada_id = session.get("empresa_id")
        is_super_admin = services["usuario_eh_super_admin_global"]()

        conta_caixa_id = (request.args.get("conta_caixa_id") or "").strip()
        status_conciliacao = (
            request.args.get("status_conciliacao") or ""
        ).strip()
        status_movimentacao = (
            request.args.get("status_movimentacao") or ""
        ).strip()
        tipo_movimentacao = (
            request.args.get("tipo_movimentacao") or ""
        ).strip()
        data_inicio = (request.args.get("data_inicio") or "").strip()
        data_fim = (request.args.get("data_fim") or "").strip()
        pesquisa = (request.args.get("pesquisa") or "").strip()
        empresa_id_filtro = (
            request.args.get("empresa_id") or ""
        ).strip()

        hoje_data = date.today()
        if not data_inicio:
            data_inicio = hoje_data.replace(day=1).strftime("%Y-%m-%d")
        if not data_fim:
            data_fim = hoje_data.strftime("%Y-%m-%d")

        con = services["obter_conexao"]()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("financeiro.financeiro_dashboard"))

        cur = con.cursor(dictionary=True)
        try:
            query = """
                SELECT m.*,
                       COALESCE(
                           NULLIF(m.status_conciliacao, ''),
                           'Pendente'
                       ) AS status_conciliacao_view,
                       COALESCE(
                           NULLIF(m.status_movimentacao, ''),
                           'Ativa'
                       ) AS status_movimentacao_view,
                       cx.nome_conta AS conta_caixa_nome,
                       t.numero_documento,
                       t.descricao AS titulo_descricao,
                       t.tipo_titulo,
                       p.nome_completo AS pessoa_nome,
                       p.cpf_cnpj AS pessoa_cpf_cnpj,
                       e.nome_fantasia AS empresa_nome,
                       e.razao_social AS empresa_razao_social,
                       u.login AS usuario_login,
                       uc.login AS usuario_conciliacao_login
                FROM movimentacoes_caixa m
                INNER JOIN contas_caixa cx
                        ON cx.id = m.conta_caixa_id
                       AND cx.empresa_id = m.empresa_id
                LEFT JOIN titulos_financeiros t
                       ON t.id = m.titulo_financeiro_id
                      AND t.empresa_id = m.empresa_id
                LEFT JOIN pessoas p
                       ON p.id = t.pessoa_id
                      AND p.empresa_id = t.empresa_id
                LEFT JOIN empresas e ON e.id = m.empresa_id
                LEFT JOIN usuarios u
                       ON u.id = m.usuario_criacao_id
                LEFT JOIN usuarios uc
                       ON uc.id = m.usuario_conciliacao_id
                WHERE 1 = 1
            """
            params = []

            if is_super_admin:
                if empresa_id_filtro and empresa_id_filtro.isdigit():
                    query += " AND m.empresa_id = %s"
                    params.append(int(empresa_id_filtro))
            else:
                query += " AND m.empresa_id = %s"
                params.append(empresa_logada_id)

            if conta_caixa_id and conta_caixa_id.isdigit():
                query += " AND m.conta_caixa_id = %s"
                params.append(int(conta_caixa_id))

            if tipo_movimentacao in ["ENTRADA", "SAIDA"]:
                query += " AND m.tipo_movimentacao = %s"
                params.append(tipo_movimentacao)

            if status_movimentacao in [
                "Ativa",
                "Estornada",
                "Estorno",
            ]:
                query += """
                    AND COALESCE(
                        NULLIF(m.status_movimentacao, ''),
                        'Ativa'
                    ) = %s
                """
                params.append(status_movimentacao)

            if status_conciliacao in [
                "Pendente",
                "Conciliada",
                "Divergente",
                "Nao conciliavel",
            ]:
                query += """
                    AND COALESCE(
                        NULLIF(m.status_conciliacao, ''),
                        'Pendente'
                    ) = %s
                """
                params.append(status_conciliacao)

            if data_inicio:
                query += " AND m.data_movimentacao >= %s"
                params.append(data_inicio)

            if data_fim:
                query += " AND m.data_movimentacao <= %s"
                params.append(data_fim)

            if pesquisa:
                query += """
                    AND (
                        m.historico LIKE %s
                        OR m.observacao LIKE %s
                        OR m.observacao_conciliacao LIKE %s
                        OR t.numero_documento LIKE %s
                        OR t.descricao LIKE %s
                        OR p.nome_completo LIKE %s
                        OR p.cpf_cnpj LIKE %s
                        OR CAST(m.id AS CHAR) LIKE %s
                        OR CAST(t.id AS CHAR) LIKE %s
                    )
                """
                termo = f"%{pesquisa}%"
                params.extend([termo] * 9)

            query += " ORDER BY m.data_movimentacao DESC, m.id DESC"
            cur.execute(query, params)
            movimentacoes = cur.fetchall()

            resumo = {
                "registros": len(movimentacoes),
                "pendentes_qtd": 0,
                "pendentes_reais_qtd": 0,
                "pendentes_nao_operacionais_qtd": 0,
                "conciliadas_qtd": 0,
                "divergentes_qtd": 0,
                "nao_conciliaveis_qtd": 0,
                "saldo_pendente": Decimal("0.00"),
                "saldo_pendente_real": Decimal("0.00"),
                "saldo_conciliado": Decimal("0.00"),
                "saldo_divergente": Decimal("0.00"),
                "saldo_nao_conciliavel": Decimal("0.00"),
                "entradas_conciliadas": Decimal("0.00"),
                "saidas_conciliadas": Decimal("0.00"),
                "entradas_nao_conciliaveis": Decimal("0.00"),
                "saidas_nao_conciliaveis": Decimal("0.00"),
            }

            for mov in movimentacoes:
                valor = services["converter_decimal"](
                    mov.get("valor_movimentacao")
                )
                sinal = (
                    valor
                    if mov.get("tipo_movimentacao") == "ENTRADA"
                    else -valor
                )
                stc = str(
                    mov.get("status_conciliacao_view") or "Pendente"
                )
                stm = str(
                    mov.get("status_movimentacao_view") or "Ativa"
                )

                mov["conciliacao_bancaria_real"] = stm == "Ativa"

                if stc == "Conciliada":
                    resumo["conciliadas_qtd"] += 1
                    resumo["saldo_conciliado"] += sinal
                    if mov.get("tipo_movimentacao") == "ENTRADA":
                        resumo["entradas_conciliadas"] += valor
                    else:
                        resumo["saidas_conciliadas"] += valor
                elif stc == "Divergente":
                    resumo["divergentes_qtd"] += 1
                    resumo["saldo_divergente"] += sinal
                elif stc == "Nao conciliavel":
                    resumo["nao_conciliaveis_qtd"] += 1
                    resumo["saldo_nao_conciliavel"] += sinal
                    if mov.get("tipo_movimentacao") == "ENTRADA":
                        resumo["entradas_nao_conciliaveis"] += valor
                    else:
                        resumo["saidas_nao_conciliaveis"] += valor
                else:
                    resumo["pendentes_qtd"] += 1
                    resumo["saldo_pendente"] += sinal
                    if stm == "Ativa":
                        resumo["pendentes_reais_qtd"] += 1
                        resumo["saldo_pendente_real"] += sinal
                    else:
                        resumo["pendentes_nao_operacionais_qtd"] += 1

            contas_caixa = services[
                "carregar_contas_caixa_financeiro"
            ](
                empresa_logada_id,
                is_super_admin,
                somente_ativas=False,
            )
            empresas = (
                services["carregar_empresas_ativas"]()
                if is_super_admin
                else []
            )
        except Exception as exc:
            print(f"Erro ao carregar conciliação de caixa: {exc}")
            flash(
                f"Erro técnico ao carregar conciliação de caixa: {exc}",
                "danger",
            )
            return redirect(url_for("financeiro.financeiro_dashboard"))
        finally:
            services["fechar_cursor_conexao"](cur, con)

        filtros = {
            "conta_caixa_id": conta_caixa_id,
            "status_conciliacao": status_conciliacao,
            "status_movimentacao": status_movimentacao,
            "tipo_movimentacao": tipo_movimentacao,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "pesquisa": pesquisa,
            "empresa_id": empresa_id_filtro,
        }

        return render_template(
            "financeiro_conciliacao_caixa.html",
            usuario_logado=usuario_logado,
            movimentacoes=movimentacoes,
            resumo=resumo,
            contas_caixa=contas_caixa,
            empresas=empresas,
            filtros=filtros,
            is_super_admin=is_super_admin,
        )

    @financeiro_bp.route(
        "/financeiro/conciliacao-caixa/acao",
        methods=["POST"],
    )
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro")
    def financeiro_conciliacao_caixa_acao():
        empresa_logada_id = session.get("empresa_id")
        usuario_id = session.get("usuario_id")
        is_super_admin = services["usuario_eh_super_admin_global"]()

        ids = request.form.getlist("movimentacao_ids")
        acao = (request.form.get("acao") or "").strip()
        observacao = (
            request.form.get("observacao_conciliacao") or ""
        ).strip()

        conta_caixa_id = (
            request.form.get("filtro_conta_caixa_id") or ""
        )
        status_conciliacao = (
            request.form.get("filtro_status_conciliacao") or ""
        )
        status_movimentacao = (
            request.form.get("filtro_status_movimentacao") or ""
        )
        tipo_movimentacao = (
            request.form.get("filtro_tipo_movimentacao") or ""
        )
        data_inicio = request.form.get("filtro_data_inicio") or ""
        data_fim = request.form.get("filtro_data_fim") or ""
        pesquisa = request.form.get("filtro_pesquisa") or ""
        empresa_id_filtro = (
            request.form.get("filtro_empresa_id") or ""
        )

        redirect_params = {
            "conta_caixa_id": conta_caixa_id,
            "status_conciliacao": status_conciliacao,
            "status_movimentacao": status_movimentacao,
            "tipo_movimentacao": tipo_movimentacao,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "pesquisa": pesquisa,
            "empresa_id": empresa_id_filtro,
        }
        redirect_params = {
            chave: valor
            for chave, valor in redirect_params.items()
            if valor
        }

        ids_validos = []
        for item in ids:
            try:
                ids_validos.append(int(item))
            except (TypeError, ValueError):
                continue

        if not ids_validos:
            flash(
                "Selecione pelo menos uma movimentação para conciliar.",
                "warning",
            )
            return redirect(
                url_for(
                    "financeiro.financeiro_conciliacao_caixa",
                    **redirect_params,
                )
            )

        mapa_status = {
            "conciliar": "Conciliada",
            "divergente": "Divergente",
            "pendente": "Pendente",
            "nao_conciliavel": "Nao conciliavel",
        }
        novo_status = mapa_status.get(acao)

        if not novo_status:
            flash("Ação de conciliação inválida.", "danger")
            return redirect(
                url_for(
                    "financeiro.financeiro_conciliacao_caixa",
                    **redirect_params,
                )
            )

        if (
            acao in ["divergente", "nao_conciliavel"]
            and not observacao
        ):
            flash(
                "Informe uma observação para marcar movimentação "
                "como divergente ou não conciliável.",
                "warning",
            )
            return redirect(
                url_for(
                    "financeiro.financeiro_conciliacao_caixa",
                    **redirect_params,
                )
            )

        con = services["obter_conexao"]()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(
                url_for(
                    "financeiro.financeiro_conciliacao_caixa",
                    **redirect_params,
                )
            )

        cur = con.cursor(dictionary=True)
        try:
            placeholders = ",".join(["%s"] * len(ids_validos))
            params = list(ids_validos)
            filtro_empresa_sql = ""

            if not is_super_admin:
                filtro_empresa_sql = " AND empresa_id = %s"
                params.append(empresa_logada_id)
            elif (
                empresa_id_filtro
                and str(empresa_id_filtro).isdigit()
            ):
                filtro_empresa_sql = " AND empresa_id = %s"
                params.append(int(empresa_id_filtro))

            if novo_status == "Pendente":
                sql = f"""
                    UPDATE movimentacoes_caixa
                    SET status_conciliacao = 'Pendente',
                        data_conciliacao = NULL,
                        usuario_conciliacao_id = NULL,
                        observacao_conciliacao = %s
                    WHERE id IN ({placeholders})
                    {filtro_empresa_sql}
                """
                params_update = [observacao or None] + params
            else:
                sql = f"""
                    UPDATE movimentacoes_caixa
                    SET status_conciliacao = %s,
                        data_conciliacao = NOW(),
                        usuario_conciliacao_id = %s,
                        observacao_conciliacao = %s
                    WHERE id IN ({placeholders})
                    {filtro_empresa_sql}
                """
                params_update = [
                    novo_status,
                    usuario_id,
                    observacao or None,
                ] + params

            cur.execute(sql, params_update)
            afetadas = cur.rowcount

            empresa_auditoria = empresa_logada_id
            if (
                is_super_admin
                and empresa_id_filtro
                and str(empresa_id_filtro).isdigit()
            ):
                empresa_auditoria = int(empresa_id_filtro)

            services["registrar_auditoria_financeira"](
                cur,
                empresa_id=empresa_auditoria,
                usuario_id=usuario_id,
                acao="CONCILIACAO_CAIXA_ATUALIZADA",
                modulo="CONCILIACAO_CAIXA",
                entidade_tipo="MOVIMENTACOES_CAIXA",
                entidade_id=None,
                status_novo=novo_status,
                motivo=f"Ação de conciliação: {acao}",
                observacao=(
                    observacao
                    or f"{afetadas} movimentação(ões) atualizada(s)."
                ),
                dados_depois={
                    "ids": ids_validos,
                    "acao": acao,
                    "novo_status": novo_status,
                    "quantidade": afetadas,
                },
            )
            con.commit()

            label = (
                "Não conciliável"
                if novo_status == "Nao conciliavel"
                else novo_status
            )
            flash(
                f"{afetadas} movimentação(ões) atualizada(s) "
                f"para {label}.",
                "success",
            )
        except Exception as exc:
            try:
                con.rollback()
            except Exception:
                pass
            print(f"Erro ao aplicar conciliação de caixa: {exc}")
            flash(
                f"Erro técnico ao aplicar conciliação: {exc}",
                "danger",
            )
        finally:
            services["fechar_cursor_conexao"](cur, con)

        return redirect(
            url_for(
                "financeiro.financeiro_conciliacao_caixa",
                **redirect_params,
            )
        )

    @financeiro_bp.route("/financeiro/dashboard", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro", "Consulta")
    def financeiro_dashboard():
        usuario_logado = session.get('usuario_nome', 'Usuário')
        empresa_logada_id = session.get('empresa_id')
        is_super_admin = services["usuario_eh_super_admin_global"]()

        if not empresa_logada_id:
            flash('Empresa não identificada na sessão. Faça login novamente.', 'danger')
            return redirect(url_for('logout'))

        hoje = date.today()
        primeiro_mes = hoje.replace(day=1)
        primeiro_mes_anterior = (primeiro_mes - timedelta(days=1)).replace(day=1)
        ultimo_mes_anterior = primeiro_mes - timedelta(days=1)

        periodo = (request.args.get('periodo') or 'mes_atual').strip()
        data_inicio = (request.args.get('data_inicio') or '').strip()
        data_fim = (request.args.get('data_fim') or '').strip()

        if periodo == 'hoje':
            data_inicio_dt = hoje
            data_fim_dt = hoje
        elif periodo == 'mes_anterior':
            data_inicio_dt = primeiro_mes_anterior
            data_fim_dt = ultimo_mes_anterior
        elif periodo == 'personalizado' and data_inicio and data_fim and services["validar_data_iso"](data_inicio) and services["validar_data_iso"](data_fim):
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date()
        else:
            periodo = 'mes_atual'
            data_inicio_dt = primeiro_mes
            data_fim_dt = hoje

        if data_inicio_dt > data_fim_dt:
            data_inicio_dt, data_fim_dt = data_fim_dt, data_inicio_dt

        tipo_titulo = (request.args.get('tipo_titulo') or '').strip()
        origem = (request.args.get('origem') or '').strip()
        conta_caixa_id = (request.args.get('conta_caixa_id') or '').strip()
        pessoa_id = (request.args.get('pessoa_id') or '').strip()
        pesquisa_pessoa = (request.args.get('pesquisa_pessoa') or '').strip()
        empresa_id_filtro = (request.args.get('empresa_id') or '').strip()

        empresa_consulta_id = empresa_logada_id
        if is_super_admin and empresa_id_filtro and empresa_id_filtro.isdigit():
            empresa_consulta_id = int(empresa_id_filtro)

        con = services["obter_conexao"]()
        if con is None:
            flash('Erro de conexão com o banco de dados.', 'danger')
            return redirect(url_for("financeiro.financeiro_titulos"))

        cur = con.cursor(dictionary=True)
        try:
            filtro_empresa_params = [empresa_consulta_id]
            if is_super_admin and not (empresa_id_filtro and empresa_id_filtro.isdigit()):
                filtro_empresa_params = []

            filtros_titulos = []
            params_titulos = []
            if filtro_empresa_params:
                filtros_titulos.append('t.empresa_id = %s')
                params_titulos.extend(filtro_empresa_params)
            else:
                filtros_titulos.append('t.empresa_id IS NOT NULL')

            if tipo_titulo in ['PAGAR', 'RECEBER']:
                filtros_titulos.append('t.tipo_titulo = %s')
                params_titulos.append(tipo_titulo)
            if origem in services["financeiro_base_origens"]():
                filtros_titulos.append('t.origem = %s')
                params_titulos.append(origem)
            if pessoa_id and pessoa_id.isdigit():
                filtros_titulos.append('t.pessoa_id = %s')
                params_titulos.append(int(pessoa_id))
            if pesquisa_pessoa:
                filtros_titulos.append('(p.nome_completo LIKE %s OR p.cpf_cnpj LIKE %s OR CAST(p.id AS CHAR) LIKE %s)')
                termo = f'%{pesquisa_pessoa}%'
                params_titulos.extend([termo, termo, termo])

            where_titulos = ' AND '.join(filtros_titulos) if filtros_titulos else '1=1'

            cur.execute(f"""
                SELECT
                    COALESCE(SUM(CASE WHEN t.tipo_titulo = 'PAGAR'
                        AND COALESCE(t.status_titulo, 'Aberto') NOT IN ('Pago','Recebido','Cancelado','Estornado')
                        THEN t.valor_liquido ELSE 0 END), 0) AS pagar_aberto,
                    COALESCE(SUM(CASE WHEN t.tipo_titulo = 'RECEBER'
                        AND COALESCE(t.status_titulo, 'Aberto') NOT IN ('Pago','Recebido','Cancelado','Estornado')
                        THEN t.valor_liquido ELSE 0 END), 0) AS receber_aberto,
                    COALESCE(SUM(CASE WHEN COALESCE(t.status_titulo, 'Aberto') NOT IN ('Pago','Recebido','Cancelado','Estornado')
                        AND t.data_vencimento IS NOT NULL AND t.data_vencimento < %s
                        THEN t.valor_liquido ELSE 0 END), 0) AS vencidos,
                    COUNT(CASE WHEN COALESCE(t.status_titulo, 'Aberto') NOT IN ('Pago','Recebido','Cancelado','Estornado')
                        AND t.data_vencimento IS NOT NULL AND t.data_vencimento < %s THEN 1 END) AS qtd_vencidos,
                    COALESCE(SUM(CASE WHEN t.status_titulo = 'Pago'
                        AND t.data_baixa BETWEEN %s AND %s THEN t.valor_baixado ELSE 0 END), 0) AS pagos_periodo,
                    COALESCE(SUM(CASE WHEN t.status_titulo = 'Recebido'
                        AND t.data_baixa BETWEEN %s AND %s THEN t.valor_baixado ELSE 0 END), 0) AS recebidos_periodo,
                    COALESCE(SUM(CASE WHEN t.status_titulo = 'Estornado'
                        AND DATE(COALESCE(t.data_estorno, t.updated_at, t.created_at)) BETWEEN %s AND %s THEN t.valor_liquido ELSE 0 END), 0) AS estornados_periodo,
                    COALESCE(SUM(CASE WHEN t.status_titulo = 'Cancelado'
                        AND DATE(COALESCE(t.data_cancelamento, t.updated_at, t.created_at)) BETWEEN %s AND %s THEN t.valor_liquido ELSE 0 END), 0) AS cancelados_periodo,
                    COUNT(CASE WHEN COALESCE(t.status_titulo, 'Aberto') NOT IN ('Pago','Recebido','Cancelado','Estornado') THEN 1 END) AS qtd_abertos
                FROM titulos_financeiros t
                LEFT JOIN pessoas p ON p.id = t.pessoa_id AND p.empresa_id = t.empresa_id
                WHERE {where_titulos}
            """, [hoje, hoje, data_inicio_dt, data_fim_dt, data_inicio_dt, data_fim_dt, data_inicio_dt, data_fim_dt, data_inicio_dt, data_fim_dt] + params_titulos)
            resumo_titulos = cur.fetchone() or {}

            filtros_mov = []
            params_mov = []
            if filtro_empresa_params:
                filtros_mov.append('m.empresa_id = %s')
                params_mov.extend(filtro_empresa_params)
            else:
                filtros_mov.append('m.empresa_id IS NOT NULL')
            filtros_mov.append('m.data_movimentacao BETWEEN %s AND %s')
            params_mov.extend([data_inicio_dt, data_fim_dt])
            if conta_caixa_id and conta_caixa_id.isdigit():
                filtros_mov.append('m.conta_caixa_id = %s')
                params_mov.append(int(conta_caixa_id))
            if tipo_titulo in ['PAGAR', 'RECEBER']:
                filtros_mov.append('t.tipo_titulo = %s')
                params_mov.append(tipo_titulo)
            if origem in services["financeiro_base_origens"]():
                filtros_mov.append('t.origem = %s')
                params_mov.append(origem)
            if pessoa_id and pessoa_id.isdigit():
                filtros_mov.append('t.pessoa_id = %s')
                params_mov.append(int(pessoa_id))
            if pesquisa_pessoa:
                filtros_mov.append('(p.nome_completo LIKE %s OR p.cpf_cnpj LIKE %s OR CAST(p.id AS CHAR) LIKE %s)')
                termo = f'%{pesquisa_pessoa}%'
                params_mov.extend([termo, termo, termo])

            where_mov = ' AND '.join(filtros_mov)
            cur.execute(f"""
                SELECT
                    COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'ENTRADA'
                        AND COALESCE(m.status_movimentacao, 'Ativa') = 'Ativa'
                        AND COALESCE(m.estorno_de_movimentacao_id, 0) = 0
                        THEN m.valor_movimentacao ELSE 0 END), 0) AS entradas_operacionais,
                    COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'SAIDA'
                        AND COALESCE(m.status_movimentacao, 'Ativa') = 'Ativa'
                        AND COALESCE(m.estorno_de_movimentacao_id, 0) = 0
                        THEN m.valor_movimentacao ELSE 0 END), 0) AS saidas_operacionais,
                    COALESCE(SUM(CASE WHEN (COALESCE(m.status_movimentacao, '') = 'Estorno'
                        OR COALESCE(m.estorno_de_movimentacao_id, 0) <> 0)
                        THEN m.valor_movimentacao ELSE 0 END), 0) AS estornos,
                    COALESCE(SUM(CASE WHEN (COALESCE(m.status_movimentacao, '') = 'Estorno'
                        OR COALESCE(m.estorno_de_movimentacao_id, 0) <> 0)
                        AND m.tipo_movimentacao = 'ENTRADA'
                        THEN m.valor_movimentacao ELSE 0 END), 0) AS estornos_entrada,
                    COALESCE(SUM(CASE WHEN (COALESCE(m.status_movimentacao, '') = 'Estorno'
                        OR COALESCE(m.estorno_de_movimentacao_id, 0) <> 0)
                        AND m.tipo_movimentacao = 'SAIDA'
                        THEN m.valor_movimentacao ELSE 0 END), 0) AS estornos_saida,
                    COALESCE(SUM(CASE WHEN COALESCE(m.status_movimentacao, '') = 'Estornada'
                        THEN m.valor_movimentacao ELSE 0 END), 0) AS movimentacoes_estornadas,
                    COALESCE(SUM(CASE WHEN COALESCE(m.status_movimentacao, 'Ativa') = 'Ativa'
                        AND COALESCE(m.estorno_de_movimentacao_id, 0) = 0
                        THEN CASE WHEN m.tipo_movimentacao = 'ENTRADA' THEN m.valor_movimentacao ELSE -m.valor_movimentacao END
                        ELSE 0 END), 0) AS saldo_operacional,
                    COALESCE(SUM(CASE WHEN COALESCE(m.status_movimentacao, 'Ativa') <> 'Estornada'
                        THEN CASE WHEN m.tipo_movimentacao = 'ENTRADA' THEN m.valor_movimentacao ELSE -m.valor_movimentacao END
                        ELSE 0 END), 0) AS saldo_liquido,
                    COUNT(*) AS total_movimentacoes
                FROM movimentacoes_caixa m
                LEFT JOIN titulos_financeiros t ON t.id = m.titulo_financeiro_id AND t.empresa_id = m.empresa_id
                LEFT JOIN pessoas p ON p.id = t.pessoa_id AND p.empresa_id = t.empresa_id
                WHERE {where_mov}
            """, params_mov)
            resumo_caixa = cur.fetchone() or {}

            cur.execute(f"""
                SELECT COALESCE(t.origem, 'MANUAL') AS origem,
                       COUNT(*) AS quantidade,
                       COALESCE(SUM(t.valor_liquido), 0) AS total
                FROM titulos_financeiros t
                LEFT JOIN pessoas p ON p.id = t.pessoa_id AND p.empresa_id = t.empresa_id
                WHERE {where_titulos}
                  AND DATE(COALESCE(t.data_emissao, t.created_at)) BETWEEN %s AND %s
                GROUP BY COALESCE(t.origem, 'MANUAL')
                ORDER BY total DESC
                LIMIT 8
            """, params_titulos + [data_inicio_dt, data_fim_dt])
            despesas_por_origem = cur.fetchall()

            cur.execute(f"""
                SELECT COALESCE(p.nome_completo, 'Sem pessoa vinculada') AS pessoa_nome,
                       COALESCE(p.cpf_cnpj, '') AS pessoa_cpf_cnpj,
                       COALESCE(p.tipo_cadastro, '') AS pessoa_tipo,
                       COUNT(*) AS quantidade,
                       COALESCE(SUM(t.valor_liquido), 0) AS total
                FROM titulos_financeiros t
                LEFT JOIN pessoas p ON p.id = t.pessoa_id AND p.empresa_id = t.empresa_id
                WHERE {where_titulos}
                  AND t.tipo_titulo = 'PAGAR'
                  AND COALESCE(t.status_titulo, 'Aberto') IN ('Pago','Estornado','Aberto','Solicitado')
                  AND DATE(COALESCE(t.data_baixa, t.data_vencimento, t.data_emissao, t.created_at)) BETWEEN %s AND %s
                GROUP BY p.id, p.nome_completo, p.cpf_cnpj, p.tipo_cadastro
                ORDER BY total DESC
                LIMIT 10
            """, params_titulos + [data_inicio_dt, data_fim_dt])
            ranking_pessoas = cur.fetchall()

            cur.execute(f"""
                SELECT cx.nome_conta,
                       COUNT(*) AS quantidade,
                       COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'ENTRADA'
                            AND COALESCE(m.status_movimentacao, 'Ativa') = 'Ativa'
                            AND COALESCE(m.estorno_de_movimentacao_id, 0) = 0
                            THEN m.valor_movimentacao ELSE 0 END), 0) AS entradas,
                       COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'SAIDA'
                            AND COALESCE(m.status_movimentacao, 'Ativa') = 'Ativa'
                            AND COALESCE(m.estorno_de_movimentacao_id, 0) = 0
                            THEN m.valor_movimentacao ELSE 0 END), 0) AS saidas,
                       COALESCE(SUM(CASE WHEN (COALESCE(m.status_movimentacao, '') = 'Estorno'
                            OR COALESCE(m.estorno_de_movimentacao_id, 0) <> 0)
                            THEN m.valor_movimentacao ELSE 0 END), 0) AS estornos,
                       COALESCE(SUM(CASE WHEN COALESCE(m.status_movimentacao, '') = 'Estornada'
                            THEN m.valor_movimentacao ELSE 0 END), 0) AS estornadas,
                       COALESCE(SUM(CASE WHEN COALESCE(m.status_movimentacao, 'Ativa') <> 'Estornada'
                            THEN CASE WHEN m.tipo_movimentacao = 'ENTRADA' THEN m.valor_movimentacao ELSE -m.valor_movimentacao END ELSE 0 END), 0) AS saldo
                FROM movimentacoes_caixa m
                INNER JOIN contas_caixa cx ON cx.id = m.conta_caixa_id AND cx.empresa_id = m.empresa_id
                LEFT JOIN titulos_financeiros t ON t.id = m.titulo_financeiro_id AND t.empresa_id = m.empresa_id
                LEFT JOIN pessoas p ON p.id = t.pessoa_id AND p.empresa_id = t.empresa_id
                WHERE {where_mov}
                GROUP BY cx.id, cx.nome_conta
                ORDER BY ABS(COALESCE(SUM(CASE WHEN COALESCE(m.status_movimentacao, 'Ativa') <> 'Estornada'
                            THEN CASE WHEN m.tipo_movimentacao = 'ENTRADA' THEN m.valor_movimentacao ELSE -m.valor_movimentacao END ELSE 0 END), 0)) DESC,
                         quantidade DESC
                LIMIT 8
            """, params_mov)
            movimentacoes_por_conta = cur.fetchall()

            cur.execute(f"""
                SELECT t.id, t.tipo_titulo, t.numero_documento, t.descricao, t.valor_liquido,
                       t.data_vencimento, t.status_titulo, p.nome_completo AS pessoa_nome
                FROM titulos_financeiros t
                LEFT JOIN pessoas p ON p.id = t.pessoa_id AND p.empresa_id = t.empresa_id
                WHERE {where_titulos}
                  AND COALESCE(t.status_titulo, 'Aberto') NOT IN ('Pago','Recebido','Cancelado','Estornado')
                  AND t.data_vencimento BETWEEN %s AND %s
                ORDER BY t.data_vencimento ASC, t.valor_liquido DESC
                LIMIT 10
            """, params_titulos + [hoje, hoje + timedelta(days=7)])
            titulos_vencendo = cur.fetchall()

            cur.execute(f"""
                SELECT m.id, m.data_movimentacao, m.tipo_movimentacao, m.valor_movimentacao,
                       m.status_movimentacao, m.estorno_de_movimentacao_id, m.historico,
                       cx.nome_conta AS conta_caixa_nome, t.id AS titulo_id,
                       t.numero_documento, t.tipo_titulo, p.nome_completo AS pessoa_nome
                FROM movimentacoes_caixa m
                INNER JOIN contas_caixa cx ON cx.id = m.conta_caixa_id AND cx.empresa_id = m.empresa_id
                LEFT JOIN titulos_financeiros t ON t.id = m.titulo_financeiro_id AND t.empresa_id = m.empresa_id
                LEFT JOIN pessoas p ON p.id = t.pessoa_id AND p.empresa_id = t.empresa_id
                WHERE {where_mov}
                ORDER BY m.data_movimentacao DESC, m.id DESC
                LIMIT 10
            """, params_mov)
            ultimas_movimentacoes = cur.fetchall()

            cur.execute(f"""
                SELECT COALESCE(t.status_titulo, 'Aberto') AS status_titulo,
                       COUNT(*) AS quantidade,
                       COALESCE(SUM(t.valor_liquido), 0) AS total
                FROM titulos_financeiros t
                LEFT JOIN pessoas p ON p.id = t.pessoa_id AND p.empresa_id = t.empresa_id
                WHERE {where_titulos}
                  AND DATE(COALESCE(t.data_emissao, t.created_at)) BETWEEN %s AND %s
                GROUP BY COALESCE(t.status_titulo, 'Aberto')
                ORDER BY quantidade DESC
            """, params_titulos + [data_inicio_dt, data_fim_dt])
            resumo_status = cur.fetchall()

            contas_caixa = services["carregar_contas_caixa_financeiro"](empresa_logada_id, is_super_admin)
            empresas = []
            if is_super_admin:
                cur.execute('SELECT id, razao_social, nome_fantasia FROM empresas ORDER BY nome_fantasia ASC, razao_social ASC')
                empresas = cur.fetchall()

            filtros = {
                'periodo': periodo,
                'data_inicio': data_inicio_dt.strftime('%Y-%m-%d'),
                'data_fim': data_fim_dt.strftime('%Y-%m-%d'),
                'tipo_titulo': tipo_titulo,
                'origem': origem,
                'conta_caixa_id': conta_caixa_id,
                'pessoa_id': pessoa_id,
                'pesquisa_pessoa': pesquisa_pessoa,
                'empresa_id': empresa_id_filtro,
            }

            return render_template(
                'financeiro_dashboard.html',
                usuario_logado=usuario_logado,
                filtros=filtros,
                resumo_titulos=resumo_titulos,
                resumo_caixa=resumo_caixa,
                despesas_por_origem=despesas_por_origem,
                ranking_pessoas=ranking_pessoas,
                movimentacoes_por_conta=movimentacoes_por_conta,
                titulos_vencendo=titulos_vencendo,
                ultimas_movimentacoes=ultimas_movimentacoes,
                resumo_status=resumo_status,
                contas_caixa=contas_caixa,
                empresas=empresas,
                origens=services["financeiro_base_origens"](),
                is_super_admin=is_super_admin,
                hoje=hoje,
            )
        except Exception as e:
            print(f'Erro ao carregar dashboard financeiro: {e}')
            flash(f'Erro técnico ao carregar dashboard financeiro: {e}', 'danger')
            return redirect(url_for("financeiro.financeiro_titulos"))
        finally:
            services["fechar_cursor_conexao"](cur, con)


    @financeiro_bp.route("/financeiro/titulos", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro", "Consulta")
    def financeiro_titulos():
        usuario_logado = session.get('usuario_nome', 'Usuário')
        empresa_logada_id = session.get('empresa_id')
        is_super_admin = services["usuario_eh_super_admin_global"]()

        if not empresa_logada_id:
            flash("Empresa não identificada na sessão. Faça login novamente.", "danger")
            return redirect(url_for('logout'))

        tipo_titulo = (request.args.get('tipo_titulo') or '').strip()
        status_titulo = (request.args.get('status_titulo') or '').strip()
        origem = (request.args.get('origem') or '').strip()
        pessoa_id = (request.args.get('pessoa_id') or '').strip()
        data_inicio = (request.args.get('data_inicio') or '').strip()
        data_fim = (request.args.get('data_fim') or '').strip()
        vencimento_inicio = (request.args.get('vencimento_inicio') or '').strip()
        vencimento_fim = (request.args.get('vencimento_fim') or '').strip()
        pesquisa = (request.args.get('pesquisa') or '').strip()
        empresa_id_filtro = (request.args.get('empresa_id') or '').strip()

        con = services["obter_conexao"]()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for('dashboard'))

        cur = con.cursor(dictionary=True)

        try:
            query = """
                SELECT t.id,
                       t.empresa_id,
                       t.tipo_titulo,
                       t.origem,
                       t.origem_id,
                       t.pessoa_id,
                       t.numero_documento,
                       t.descricao,
                       t.historico,
                       t.valor_original,
                       t.valor_desconto,
                       t.valor_acrescimo,
                       t.valor_liquido,
                       t.data_emissao,
                       t.data_competencia,
                       t.data_vencimento,
                       t.forma_pagamento,
                       t.status_titulo,
                       t.observacao,
                       t.created_at,
                       p.nome_completo AS pessoa_nome,
                       p.cpf_cnpj AS pessoa_cpf_cnpj,
                       p.tipo_cadastro AS pessoa_tipo,
                       cx.nome_conta AS conta_caixa_nome,
                       e.nome_fantasia AS empresa_nome,
                       e.razao_social AS empresa_razao_social
                FROM titulos_financeiros t
                LEFT JOIN pessoas p ON p.id = t.pessoa_id AND p.empresa_id = t.empresa_id
                LEFT JOIN contas_caixa cx ON cx.id = t.conta_caixa_prevista_id AND cx.empresa_id = t.empresa_id
                INNER JOIN empresas e ON e.id = t.empresa_id
                WHERE 1 = 1
            """
            params = []

            if is_super_admin:
                if empresa_id_filtro and empresa_id_filtro.isdigit():
                    query += " AND t.empresa_id = %s"
                    params.append(int(empresa_id_filtro))
            else:
                query += " AND t.empresa_id = %s"
                params.append(empresa_logada_id)

            if tipo_titulo in ['PAGAR', 'RECEBER']:
                query += " AND t.tipo_titulo = %s"
                params.append(tipo_titulo)

            if status_titulo in services["financeiro_base_status_titulos"]():
                query += " AND t.status_titulo = %s"
                params.append(status_titulo)

            if origem in services["financeiro_base_origens"]():
                query += " AND t.origem = %s"
                params.append(origem)

            if pessoa_id and pessoa_id.isdigit():
                query += " AND t.pessoa_id = %s"
                params.append(int(pessoa_id))

            if data_inicio:
                query += " AND t.data_emissao >= %s"
                params.append(data_inicio)

            if data_fim:
                query += " AND t.data_emissao <= %s"
                params.append(data_fim)

            if vencimento_inicio:
                query += " AND t.data_vencimento >= %s"
                params.append(vencimento_inicio)

            if vencimento_fim:
                query += " AND t.data_vencimento <= %s"
                params.append(vencimento_fim)

            if pesquisa:
                query += """
                    AND (
                        t.numero_documento LIKE %s
                        OR t.descricao LIKE %s
                        OR t.historico LIKE %s
                        OR p.nome_completo LIKE %s
                        OR p.cpf_cnpj LIKE %s
                    )
                """
                termo = f"%{pesquisa}%"
                params.extend([termo, termo, termo, termo, termo])

            query += " ORDER BY t.data_vencimento ASC, t.id DESC"
            cur.execute(query, params)
            titulos = cur.fetchall()

            resumo = {
                'pagar_aberto': Decimal('0.00'),
                'receber_aberto': Decimal('0.00'),
                'vencidos': Decimal('0.00'),
                'qtd_vencidos': 0,
                'pagos_recebidos_mes': Decimal('0.00'),
                # Total filtrado mantém todos os registros da listagem, inclusive cancelados,
                # para preservar a visão histórica do filtro aplicado.
                'total_titulos': len(titulos),
                # Indicadores gerenciais: somente títulos que ainda exigem ação.
                'qtd_abertos': 0,
                'qtd_cancelados': 0,
                'qtd_baixados': 0
            }

            hoje = date.today()
            mes_atual = hoje.strftime('%Y-%m')

            for titulo in titulos:
                status = titulo.get('status_titulo') or 'Aberto'
                tipo = titulo.get('tipo_titulo') or ''
                valor = services["converter_decimal"](titulo.get('valor_liquido'))
                vencimento = titulo.get('data_vencimento')

                if status not in ['Pago', 'Recebido', 'Cancelado', 'Estornado']:
                    resumo['qtd_abertos'] += 1

                    if tipo == 'PAGAR':
                        resumo['pagar_aberto'] += valor
                    elif tipo == 'RECEBER':
                        resumo['receber_aberto'] += valor

                    if vencimento and vencimento < hoje:
                        resumo['vencidos'] += valor
                        resumo['qtd_vencidos'] += 1

                elif status in ['Cancelado', 'Estornado']:
                    resumo['qtd_cancelados'] += 1

                elif status in ['Pago', 'Recebido']:
                    resumo['qtd_baixados'] += 1
                    data_emissao = titulo.get('data_emissao')
                    if data_emissao and str(data_emissao)[:7] == mes_atual:
                        resumo['pagos_recebidos_mes'] += valor

            pessoas = services["carregar_pessoas_financeiro"](empresa_logada_id, is_super_admin)
            contas_caixa = services["carregar_contas_caixa_financeiro"](empresa_logada_id, is_super_admin)
            empresas = []
            if is_super_admin:
                cur.execute("SELECT id, razao_social, nome_fantasia FROM empresas ORDER BY nome_fantasia ASC, razao_social ASC")
                empresas = cur.fetchall()

        except Exception as e:
            print(f"Erro ao carregar títulos financeiros: {e}")
            flash(f"Erro técnico ao carregar títulos financeiros: {e}", "danger")
            titulos = []
            resumo = {
                'pagar_aberto': 0,
                'receber_aberto': 0,
                'vencidos': 0,
                'qtd_vencidos': 0,
                'pagos_recebidos_mes': 0,
                'total_titulos': 0,
                'qtd_abertos': 0,
                'qtd_cancelados': 0,
                'qtd_baixados': 0
            }
            pessoas = []
            contas_caixa = []
            empresas = []

        finally:
            services["fechar_cursor_conexao"](cur, con)

        filtros = {
            'tipo_titulo': tipo_titulo,
            'status_titulo': status_titulo,
            'origem': origem,
            'pessoa_id': pessoa_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'vencimento_inicio': vencimento_inicio,
            'vencimento_fim': vencimento_fim,
            'pesquisa': pesquisa,
            'empresa_id': empresa_id_filtro
        }

        return render_template(
            'financeiro_titulos.html',
            usuario_logado=usuario_logado,
            titulos=titulos,
            resumo=resumo,
            filtros=filtros,
            pessoas=pessoas,
            contas_caixa=contas_caixa,
            empresas=empresas,
            status_titulos=services["financeiro_base_status_titulos"](),
            origens=services["financeiro_base_origens"](),
            formas_pagamento=services["financeiro_base_formas_pagamento"](),
            is_super_admin=is_super_admin
        )


    return financeiro_bp
