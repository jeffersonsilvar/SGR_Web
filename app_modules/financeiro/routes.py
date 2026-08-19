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


    @financeiro_bp.route("/financeiro/titulos/<int:id>", methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro", "Consulta")
    def detalhes_titulo_financeiro(id):
        usuario_logado = session.get('usuario_nome', 'Usuário')
        empresa_logada_id = session.get('empresa_id')
        is_super_admin = services["usuario_eh_super_admin_global"]()

        con = services["obter_conexao"]()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for('financeiro.financeiro_titulos'))

        cur = con.cursor(dictionary=True)
        try:
            query = """
                SELECT t.*,
                       p.nome_completo AS pessoa_nome,
                       p.cpf_cnpj AS pessoa_cpf_cnpj,
                       p.tipo_cadastro AS pessoa_tipo,
                       cx.nome_conta AS conta_caixa_nome,
                       cxb.nome_conta AS conta_caixa_baixa_nome,
                       e.nome_fantasia AS empresa_nome,
                       e.razao_social AS empresa_razao_social,
                       u.login AS usuario_criacao_login,
                       ub.login AS usuario_baixa_login,
                       ue.login AS usuario_estorno_login
                FROM titulos_financeiros t
                LEFT JOIN pessoas p ON p.id = t.pessoa_id AND p.empresa_id = t.empresa_id
                LEFT JOIN contas_caixa cx ON cx.id = t.conta_caixa_prevista_id AND cx.empresa_id = t.empresa_id
                LEFT JOIN contas_caixa cxb ON cxb.id = t.conta_caixa_baixa_id AND cxb.empresa_id = t.empresa_id
                LEFT JOIN empresas e ON e.id = t.empresa_id
                LEFT JOIN usuarios u ON u.id = t.usuario_criacao_id
                LEFT JOIN usuarios ub ON ub.id = t.usuario_baixa_id
                LEFT JOIN usuarios ue ON ue.id = t.usuario_estorno_id
                WHERE t.id = %s
            """
            params = [id]
            if not is_super_admin:
                query += " AND t.empresa_id = %s"
                params.append(empresa_logada_id)
            query += " LIMIT 1"

            cur.execute(query, params)
            titulo = cur.fetchone()
            if not titulo:
                flash("Título financeiro não encontrado ou não pertence à empresa logada.", "danger")
                return redirect(url_for('financeiro.financeiro_titulos'))

            cur.execute("""
                SELECT id, tipo_vinculo, origem_tabela, origem_id, descricao, valor_vinculo
                FROM titulos_financeiros_vinculos
                WHERE titulo_financeiro_id = %s
                  AND empresa_id = %s
                ORDER BY id ASC
            """, (id, titulo['empresa_id']))
            vinculos = cur.fetchall()

            cur.execute("""
                SELECT m.*,
                       cx.nome_conta AS conta_caixa_nome,
                       u.login AS usuario_login
                FROM movimentacoes_caixa m
                INNER JOIN contas_caixa cx ON cx.id = m.conta_caixa_id AND cx.empresa_id = m.empresa_id
                LEFT JOIN usuarios u ON u.id = m.usuario_criacao_id
                WHERE m.titulo_financeiro_id = %s
                  AND m.empresa_id = %s
                ORDER BY m.data_movimentacao DESC, m.id DESC
            """, (id, titulo['empresa_id']))
            movimentacoes = cur.fetchall()

            parametros_financeiros = services["carregar_parametros_financeiros_empresa"](titulo['empresa_id'], cur=cur)
            conta_padrao_id = str(parametros_financeiros.get('caixa.conta_padrao_id', {}).get('valor') or '')
            forma_pagamento_padrao = parametros_financeiros.get('caixa.forma_pagamento_padrao', {}).get('valor') or (titulo.get('forma_pagamento') or 'PIX')

            contas_caixa = []
            if titulo.get('status_titulo') not in ['Pago', 'Recebido', 'Cancelado', 'Estornado']:
                cur.execute("""
                    SELECT id, nome_conta, tipo_conta, banco, agencia, numero_conta, saldo_inicial, status_conta
                    FROM contas_caixa
                    WHERE empresa_id = %s
                      AND status_conta = 'Ativa'
                    ORDER BY nome_conta ASC
                """, (titulo['empresa_id'],))
                contas_caixa = cur.fetchall()
                for conta in contas_caixa:
                    saldo_info = services["calcular_saldo_conta_caixa"](cur, conta['id'], titulo['empresa_id'])
                    conta['saldo_atual'] = (saldo_info or {}).get('saldo_atual', Decimal('0.00'))

        except Exception as e:
            print(f"Erro ao carregar detalhes do título financeiro: {e}")
            flash(f"Erro técnico ao carregar título financeiro: {e}", "danger")
            return redirect(url_for('financeiro.financeiro_titulos'))
        finally:
            services["fechar_cursor_conexao"](cur, con)

        return render_template(
            'financeiro_titulo_detalhes.html',
            usuario_logado=usuario_logado,
            titulo=titulo,
            vinculos=vinculos,
            movimentacoes=movimentacoes,
            contas_caixa=contas_caixa,
            formas_pagamento=services["financeiro_base_formas_pagamento"](),
            parametros_financeiros=parametros_financeiros,
            parametro_bool=services["parametro_bool"],
            conta_padrao_id=conta_padrao_id,
            forma_pagamento_padrao=forma_pagamento_padrao,
            is_super_admin=is_super_admin,
            hoje=date.today().strftime('%Y-%m-%d')
        )

    @financeiro_bp.route("/financeiro/titulos/novo", methods=["GET", "POST"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro")
    def novo_titulo_financeiro():
        usuario_logado = session.get('usuario_nome', 'Usuário')
        empresa_logada_id = session.get('empresa_id')
        usuario_id = session.get('usuario_id')
        is_super_admin = services["usuario_eh_super_admin_global"]()

        if not empresa_logada_id:
            flash("Empresa não identificada na sessão. Faça login novamente.", "danger")
            return redirect(url_for('logout'))

        if request.method == 'POST':
            empresa_id = request.form.get('empresa_id') if is_super_admin else empresa_logada_id
            tipo_titulo = (request.form.get('tipo_titulo') or '').strip()
            pessoa_id = (request.form.get('pessoa_id') or '').strip()
            numero_documento = (request.form.get('numero_documento') or '').strip()
            descricao = (request.form.get('descricao') or '').strip()
            historico = (request.form.get('historico') or '').strip()
            data_emissao = (request.form.get('data_emissao') or '').strip()
            data_competencia = (request.form.get('data_competencia') or '').strip()
            data_vencimento = (request.form.get('data_vencimento') or '').strip()
            forma_pagamento = (request.form.get('forma_pagamento') or '').strip()
            conta_caixa_prevista_id = (request.form.get('conta_caixa_prevista_id') or '').strip()
            valor_original = services["converter_decimal"](request.form.get('valor_original'))
            valor_desconto = services["converter_decimal"](request.form.get('valor_desconto'))
            valor_acrescimo = services["converter_decimal"](request.form.get('valor_acrescimo'))
            observacao = (request.form.get('observacao') or '').strip()

            if not empresa_id or not str(empresa_id).isdigit():
                flash("Selecione uma empresa válida.", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))
            empresa_id = int(empresa_id)

            if tipo_titulo not in ['PAGAR', 'RECEBER']:
                flash("Selecione se o título é Conta a Pagar ou Conta a Receber.", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))

            if not pessoa_id or not pessoa_id.isdigit():
                flash("Selecione a pessoa responsável pelo título.", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))
            pessoa_id = int(pessoa_id)

            if not numero_documento:
                flash("Informe o número do documento.", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))

            if not descricao:
                flash("Informe uma descrição para o título.", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))

            if not data_emissao or not services["validar_data_iso"](data_emissao):
                flash("Informe uma data de emissão válida.", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))

            if not data_competencia:
                data_competencia = data_emissao

            if not services["validar_data_iso"](data_competencia):
                flash("Informe uma data de competência válida.", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))

            if not data_vencimento or not services["validar_data_iso"](data_vencimento):
                flash("Informe uma data de vencimento válida.", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))

            if valor_original <= 0:
                flash("Informe um valor maior que zero.", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))

            if forma_pagamento and forma_pagamento not in services["financeiro_base_formas_pagamento"]():
                flash("Forma de pagamento inválida.", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))

            conta_caixa_prevista_id_int = None
            if conta_caixa_prevista_id:
                if not conta_caixa_prevista_id.isdigit():
                    flash("Conta caixa inválida.", "danger")
                    return redirect(url_for('financeiro.novo_titulo_financeiro'))
                conta_caixa_prevista_id_int = int(conta_caixa_prevista_id)

            valor_liquido = (valor_original - valor_desconto + valor_acrescimo).quantize(Decimal('0.01'))
            if valor_liquido <= 0:
                flash("O valor líquido do título precisa ser maior que zero.", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))

            con = services["obter_conexao"]()
            if con is None:
                flash("Erro de conexão com o banco de dados.", "danger")
                return redirect(url_for('financeiro.financeiro_titulos'))

            cur = con.cursor(dictionary=True)
            try:
                cur.execute("SELECT id FROM empresas WHERE id = %s AND status_empresa = 'Ativa' LIMIT 1", (empresa_id,))
                if not cur.fetchone():
                    flash("Empresa inválida ou inativa.", "danger")
                    return redirect(url_for('financeiro.novo_titulo_financeiro'))

                cur.execute("""
                    SELECT id, nome_completo
                    FROM pessoas
                    WHERE id = %s
                      AND empresa_id = %s
                      AND status_cadastro = 'Ativo'
                    LIMIT 1
                """, (pessoa_id, empresa_id))
                pessoa = cur.fetchone()
                if not pessoa:
                    flash("Pessoa inválida ou não pertence à empresa informada.", "danger")
                    return redirect(url_for('financeiro.novo_titulo_financeiro'))

                if conta_caixa_prevista_id_int:
                    cur.execute("""
                        SELECT id
                        FROM contas_caixa
                        WHERE id = %s
                          AND empresa_id = %s
                          AND status_conta = 'Ativa'
                        LIMIT 1
                    """, (conta_caixa_prevista_id_int, empresa_id))
                    if not cur.fetchone():
                        flash("Conta caixa inválida ou inativa.", "danger")
                        return redirect(url_for('financeiro.novo_titulo_financeiro'))

                if not historico:
                    historico = f"{descricao} - Documento {numero_documento} - {pessoa['nome_completo']}"

                cur.execute("""
                    INSERT INTO titulos_financeiros
                        (empresa_id, tipo_titulo, origem, origem_id, pessoa_id, numero_documento,
                         descricao, historico, valor_original, valor_desconto, valor_acrescimo,
                         valor_liquido, data_emissao, data_competencia, data_vencimento,
                         forma_pagamento, conta_caixa_prevista_id, status_titulo, observacao,
                         usuario_criacao_id)
                    VALUES
                        (%s, %s, 'MANUAL', NULL, %s, %s,
                         %s, %s, %s, %s, %s,
                         %s, %s, %s, %s,
                         %s, %s, 'Aberto', %s,
                         %s)
                """, (
                    empresa_id,
                    tipo_titulo,
                    pessoa_id,
                    numero_documento,
                    descricao,
                    historico,
                    valor_original,
                    valor_desconto,
                    valor_acrescimo,
                    valor_liquido,
                    data_emissao,
                    data_competencia,
                    data_vencimento,
                    forma_pagamento or None,
                    conta_caixa_prevista_id_int,
                    observacao or None,
                    usuario_id
                ))

                titulo_id = cur.lastrowid
                services["registrar_auditoria_financeira"](
                    cur,
                    empresa_id=empresa_id,
                    usuario_id=usuario_id,
                    acao='TITULO_MANUAL_CRIADO',
                    modulo='TITULOS_FINANCEIROS',
                    entidade_tipo='TITULO_FINANCEIRO',
                    entidade_id=titulo_id,
                    titulo_financeiro_id=titulo_id,
                    pessoa_id=pessoa_id,
                    status_novo='Aberto',
                    valor_novo=valor_liquido,
                    motivo='Criação manual de título financeiro',
                    observacao=f'Título manual #{titulo_id} criado. Documento: {numero_documento}.',
                    dados_depois={
                        'tipo_titulo': tipo_titulo,
                        'numero_documento': numero_documento,
                        'descricao': descricao,
                        'valor_original': str(valor_original),
                        'valor_liquido': str(valor_liquido),
                        'data_vencimento': data_vencimento,
                    }
                )
                con.commit()

                flash(f"Título financeiro #{titulo_id} criado com sucesso.", "success")
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=titulo_id))

            except Exception as e:
                con.rollback()
                print(f"Erro ao criar título financeiro: {e}")
                flash(f"Erro técnico ao criar título financeiro: {e}", "danger")
                return redirect(url_for('financeiro.novo_titulo_financeiro'))
            finally:
                services["fechar_cursor_conexao"](cur, con)

        pessoas = services["carregar_pessoas_financeiro"](empresa_logada_id, is_super_admin)
        contas_caixa = services["carregar_contas_caixa_financeiro"](empresa_logada_id, is_super_admin)
        parametros_financeiros = services["carregar_parametros_financeiros_empresa"](empresa_logada_id)
        conta_padrao_id = (parametros_financeiros.get('caixa.conta_padrao_id', {}) or {}).get('valor') or ''
        forma_pagamento_padrao = (parametros_financeiros.get('caixa.forma_pagamento_padrao', {}) or {}).get('valor') or 'PIX'
        empresas = []
        if is_super_admin:
            empresas = services["carregar_empresas_ativas"]()

        return render_template(
            'financeiro_titulo_form.html',
            usuario_logado=usuario_logado,
            pessoas=pessoas,
            contas_caixa=contas_caixa,
            empresas=empresas,
            formas_pagamento=services["financeiro_base_formas_pagamento"](),
            is_super_admin=is_super_admin,
            parametros_financeiros=parametros_financeiros,
            parametro_bool=services["parametro_bool"],
            conta_padrao_id=conta_padrao_id,
            forma_pagamento_padrao=forma_pagamento_padrao,
            hoje=date.today().strftime('%Y-%m-%d')
        )




    # ----------------------------------------------------------
    # Bloco 5 — Calcula saldo atual de uma conta caixa.
    # Saldo = saldo inicial + entradas baixadas - saídas baixadas.
    # ----------------------------------------------------------
    def calcular_saldo_conta_caixa(cur, conta_caixa_id, empresa_id):
        cur.execute("""
            SELECT
                c.id,
                c.nome_conta,
                c.saldo_inicial,
                COALESCE(SUM(
                    CASE
                        WHEN m.tipo_movimentacao = 'ENTRADA'
                            THEN COALESCE(m.valor_movimentacao, 0)
                        WHEN m.tipo_movimentacao = 'SAIDA'
                            THEN -COALESCE(m.valor_movimentacao, 0)
                        ELSE 0
                    END
                ), 0) AS saldo_movimentado
            FROM contas_caixa c
            LEFT JOIN movimentacoes_caixa m
                   ON m.conta_caixa_id = c.id
                  AND m.empresa_id = c.empresa_id
            WHERE c.id = %s
              AND c.empresa_id = %s
            GROUP BY c.id, c.nome_conta, c.saldo_inicial
            LIMIT 1
        """, (conta_caixa_id, empresa_id))
        row = cur.fetchone()
        if not row:
            return None

        saldo = services["converter_decimal"](row.get('saldo_inicial')) + services["converter_decimal"](row.get('saldo_movimentado'))
        row['saldo_atual'] = saldo.quantize(Decimal('0.01'))
        return row


    # ----------------------------------------------------------
    # Bloco 5 — Salva comprovante de baixa financeira.
    # Usa Google Drive quando habilitado e mantém fallback local.
    # ----------------------------------------------------------
    def salvar_comprovante_baixa_titulo(cur, arquivo, *, empresa_id, titulo_id, pessoa_id=None, usuario_id=None):
        if not arquivo or not arquivo.filename:
            return None

        nome_original = str(arquivo.filename or 'comprovante').strip()
        nome_seguro = nome_original.replace('\\', '_').replace('/', '_')
        nome_seguro = re.sub(r'[^a-zA-Z0-9_.-]+', '_', nome_seguro) or 'comprovante'

        pasta = os.path.join(app.root_path, 'uploads', 'comprovantes_financeiros')
        os.makedirs(pasta, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        nome_final = f"empresa_{empresa_id}_titulo_{titulo_id}_{timestamp}_{nome_seguro}"
        caminho_final = os.path.join(pasta, nome_final)
        arquivo.save(caminho_final)

        caminho_relativo = f"uploads/comprovantes_financeiros/{nome_final}"

        try:
            return tentar_enviar_arquivo_google_drive(
                cur,
                caminho_final,
                caminho_relativo,
                empresa_id=empresa_id,
                motorista_id=pessoa_id,
                origem='COMPROVANTE_FINANCEIRO',
                origem_id=titulo_id,
                tipo_arquivo='COMPROVANTE_FINANCEIRO',
                nome_original=nome_original,
                mime_type=getattr(arquivo, 'mimetype', None) or 'application/octet-stream',
                criado_por_usuario_id=usuario_id or session.get('usuario_id'),
            )
        except Exception as exc:
            print(f"[Financeiro] Falha ao enviar comprovante do título {titulo_id}: {exc}")
            return caminho_relativo


    # ----------------------------------------------------------
    # Bloco 5 — Atualiza documento do motorista e rotas após baixa.
    # Usado quando o título nasceu de NF_MOTORISTA ou SEM_NF_MOTORISTA.
    # ----------------------------------------------------------
    def aplicar_baixa_em_documento_motorista_e_rotas(cur, *, titulo_id, empresa_id, usuario_id):
        """
        Bloco 5.1.2 — Sincronização robusta de baixa para documentos de motorista.

        Esta versão evita processamento rota a rota com várias consultas e não abre novas
        conexões dentro da transação principal. Ela faz a sincronização em massa:
        - Documento do motorista -> Pagamento confirmado;
        - Rotas vinculadas -> Pagamento confirmado / Quitada;
        - Histórico registrado usando a mesma conexão/cursor da baixa.
        """
        cur.execute("""
            SELECT id, empresa_id, origem, origem_id, numero_documento, status_titulo
            FROM titulos_financeiros
            WHERE id = %s
              AND empresa_id = %s
            LIMIT 1
        """, (titulo_id, empresa_id))
        titulo = cur.fetchone() or {}

        origem_titulo = str(titulo.get('origem') or '').strip()
        status_titulo = str(titulo.get('status_titulo') or '').strip()

        if origem_titulo not in ['NF_MOTORISTA', 'SEM_NF_MOTORISTA']:
            return

        if status_titulo not in ['Pago', 'Recebido']:
            return

        # ----------------------------------------------------------
        # 1. Localiza documento(s) do motorista vinculados ao título.
        # ----------------------------------------------------------
        nf_ids = []

        if titulo.get('origem_id'):
            try:
                nf_ids.append(int(titulo.get('origem_id')))
            except Exception:
                pass

        cur.execute("""
            SELECT origem_id
            FROM titulos_financeiros_vinculos
            WHERE titulo_financeiro_id = %s
              AND empresa_id = %s
              AND origem_id IS NOT NULL
              AND (
                    origem_tabela = 'motorista_notas_fiscais'
                    OR tipo_vinculo IN ('NF_MOTORISTA', 'SEM_NF_MOTORISTA')
                  )
        """, (titulo_id, empresa_id))

        for row in cur.fetchall():
            try:
                nf_ids.append(int(row.get('origem_id')))
            except Exception:
                pass

        nf_ids = sorted(set([x for x in nf_ids if x]))

        # ----------------------------------------------------------
        # 2. Localiza rotas vinculadas ao título ou aos documentos.
        # ----------------------------------------------------------
        rota_ids = []

        cur.execute("""
            SELECT origem_id
            FROM titulos_financeiros_vinculos
            WHERE titulo_financeiro_id = %s
              AND empresa_id = %s
              AND origem_id IS NOT NULL
              AND (origem_tabela = 'rotas' OR tipo_vinculo = 'ROTA')
        """, (titulo_id, empresa_id))

        for row in cur.fetchall():
            try:
                rota_ids.append(int(row.get('origem_id')))
            except Exception:
                pass

        if nf_ids:
            placeholders_nf = ','.join(['%s'] * len(nf_ids))
            cur.execute(f"""
                SELECT DISTINCT rota_id
                FROM motorista_nf_rotas
                WHERE empresa_id = %s
                  AND motorista_nf_id IN ({placeholders_nf})
                  AND rota_id IS NOT NULL
            """, [empresa_id] + nf_ids)

            for row in cur.fetchall():
                try:
                    rota_ids.append(int(row.get('rota_id')))
                except Exception:
                    pass

        rota_ids = sorted(set([x for x in rota_ids if x]))

        # ----------------------------------------------------------
        # 3. Histórico e atualização dos documentos em lote.
        # ----------------------------------------------------------
        if nf_ids:
            placeholders_nf = ','.join(['%s'] * len(nf_ids))

            # Registra histórico antes da atualização para guardar status anterior.
            cur.execute(f"""
                INSERT INTO historico_operacoes
                    (empresa_id, tipo_operacao, usuario_id, status_anterior, status_novo, motivo, observacao)
                SELECT
                    empresa_id,
                    'NF_MOTORISTA',
                    %s,
                    status_nf,
                    'Pagamento confirmado',
                    'Baixa financeira do título',
                    CONCAT('NF Motorista ID ', id, '. Pagamento confirmado pela baixa do título financeiro #', %s, '.')
                FROM motorista_notas_fiscais
                WHERE empresa_id = %s
                  AND id IN ({placeholders_nf})
                  AND COALESCE(status_nf, '') NOT IN ('Pagamento confirmado', 'Recusada', 'Estornada', 'Cancelada')
            """, [usuario_id, titulo_id, empresa_id] + nf_ids)

            cur.execute(f"""
                UPDATE motorista_notas_fiscais
                SET status_nf = 'Pagamento confirmado',
                    data_pagamento = COALESCE(data_pagamento, NOW()),
                    usuario_pagamento_id = COALESCE(usuario_pagamento_id, %s),
                    observacao = CONCAT(
                        COALESCE(observacao, ''),
                        CASE WHEN COALESCE(observacao, '') = '' THEN '' ELSE '\n' END,
                        'Pagamento confirmado em ',
                        DATE_FORMAT(NOW(), '%d/%m/%Y %H:%i'),
                        '. Título financeiro baixado: #',
                        %s
                    )
                WHERE empresa_id = %s
                  AND id IN ({placeholders_nf})
                  AND COALESCE(status_nf, '') NOT IN ('Pagamento confirmado', 'Recusada', 'Estornada', 'Cancelada')
            """, [usuario_id, titulo_id, empresa_id] + nf_ids)

        # ----------------------------------------------------------
        # 4. Histórico e atualização das rotas em lote.
        # ----------------------------------------------------------
        if rota_ids:
            placeholders_rota = ','.join(['%s'] * len(rota_ids))

            cur.execute(f"""
                INSERT INTO historico_operacoes
                    (empresa_id, tipo_operacao, rota_id, usuario_id, status_anterior, status_novo, motivo, observacao)
                SELECT
                    empresa_id,
                    'STATUS_MOTORISTA_ROTA',
                    id,
                    %s,
                    status_motorista,
                    'Pagamento confirmado',
                    'Baixa financeira do título',
                    CONCAT('Rota quitada pela baixa do título financeiro #', %s, '.')
                FROM rotas
                WHERE empresa_id = %s
                  AND id IN ({placeholders_rota})
                  AND COALESCE(situacao_rota, '') <> 'Cancelada'
                  AND COALESCE(status_motorista, '') <> 'Pagamento confirmado'
            """, [usuario_id, titulo_id, empresa_id] + rota_ids)

            cur.execute(f"""
                UPDATE rotas
                SET status_motorista = 'Pagamento confirmado',
                    situacao_rota = 'Quitada'
                WHERE empresa_id = %s
                  AND id IN ({placeholders_rota})
                  AND COALESCE(situacao_rota, '') <> 'Cancelada'
            """, [empresa_id] + rota_ids)



    @financeiro_bp.route("/financeiro/titulos/<int:id>/cancelar", methods=["POST"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro")
    def cancelar_titulo_financeiro(id):
        empresa_logada_id = session.get('empresa_id')
        usuario_id = session.get('usuario_id')
        is_super_admin = services["usuario_eh_super_admin_global"]()
        motivo = (request.form.get('motivo_cancelamento') or '').strip()

        if len(motivo) < 5:
            flash("Informe um motivo de cancelamento com pelo menos 5 caracteres.", "warning")
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        con = services["obter_conexao"]()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for('financeiro.financeiro_titulos'))

        cur = con.cursor(dictionary=True)
        try:
            query = "SELECT id, empresa_id, status_titulo FROM titulos_financeiros WHERE id = %s"
            params = [id]
            if not is_super_admin:
                query += " AND empresa_id = %s"
                params.append(empresa_logada_id)
            query += " LIMIT 1"
            cur.execute(query, params)
            titulo = cur.fetchone()

            if not titulo:
                flash("Título financeiro não encontrado ou não pertence à empresa logada.", "danger")
                return redirect(url_for('financeiro.financeiro_titulos'))

            if titulo.get('status_titulo') in ['Pago', 'Recebido', 'Cancelado', 'Estornado']:
                flash(f"Este título não pode ser cancelado. Status atual: {titulo.get('status_titulo')}.", "warning")
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            cur.execute("""
                UPDATE titulos_financeiros
                SET status_titulo = 'Cancelado',
                    motivo_cancelamento = %s,
                    data_cancelamento = NOW(),
                    usuario_cancelamento_id = %s,
                    updated_at = NOW()
                WHERE id = %s
                  AND empresa_id = %s
            """, (motivo, usuario_id, id, titulo['empresa_id']))
            services["registrar_auditoria_financeira"](
                cur,
                empresa_id=titulo['empresa_id'],
                usuario_id=usuario_id,
                acao='TITULO_CANCELADO',
                modulo='TITULOS_FINANCEIROS',
                entidade_tipo='TITULO_FINANCEIRO',
                entidade_id=id,
                titulo_financeiro_id=id,
                status_anterior=titulo.get('status_titulo'),
                status_novo='Cancelado',
                motivo=motivo,
                observacao=f'Título financeiro #{id} cancelado.',
            )
            con.commit()
            flash("Título financeiro cancelado com sucesso.", "success")
        except Exception as e:
            con.rollback()
            print(f"Erro ao cancelar título financeiro: {e}")
            flash("Erro técnico ao cancelar título financeiro.", "danger")
        finally:
            services["fechar_cursor_conexao"](cur, con)

        return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))




    @financeiro_bp.route("/financeiro/titulos/<int:id>/baixar", methods=["POST"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro")
    def baixar_titulo_financeiro(id):
        empresa_logada_id = session.get('empresa_id')
        usuario_id = session.get('usuario_id')
        is_super_admin = services["usuario_eh_super_admin_global"]()

        conta_caixa_id = (request.form.get('conta_caixa_id') or '').strip()
        data_pagamento = (request.form.get('data_pagamento') or '').strip()
        forma_pagamento = (request.form.get('forma_pagamento') or '').strip()
        valor_pago = services["converter_decimal"](request.form.get('valor_pago'))
        observacao_baixa = (request.form.get('observacao_baixa') or '').strip()
        comprovante = request.files.get('comprovante')

        if not conta_caixa_id or not conta_caixa_id.isdigit():
            flash("Selecione uma conta caixa válida para baixar o título.", "danger")
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))
        conta_caixa_id = int(conta_caixa_id)

        if not data_pagamento or not services["validar_data_iso"](data_pagamento):
            flash("Informe uma data de pagamento/recebimento válida.", "danger")
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        if forma_pagamento not in services["financeiro_base_formas_pagamento"]():
            flash("Selecione uma forma de pagamento válida.", "danger")
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        con = services["obter_conexao"]()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for('financeiro.financeiro_titulos'))

        cur = con.cursor(dictionary=True)
        try:
            query = """
                SELECT id, empresa_id, tipo_titulo, origem, origem_id, pessoa_id, numero_documento,
                       descricao, historico, valor_liquido, status_titulo
                FROM titulos_financeiros
                WHERE id = %s
            """
            params = [id]
            if not is_super_admin:
                query += " AND empresa_id = %s"
                params.append(empresa_logada_id)
            query += " LIMIT 1"
            cur.execute(query, params)
            titulo = cur.fetchone()

            if not titulo:
                flash("Título financeiro não encontrado ou não pertence à empresa logada.", "danger")
                return redirect(url_for('financeiro.financeiro_titulos'))

            parametros_financeiros = services["carregar_parametros_financeiros_empresa"](titulo['empresa_id'], cur=cur)
            exigir_comprovante_baixa = services["parametro_bool"](parametros_financeiros.get('baixa.exigir_comprovante', {}).get('valor'))
            permitir_saldo_negativo = services["parametro_bool"](parametros_financeiros.get('caixa.permitir_saldo_negativo', {}).get('valor'))
            permitir_data_retroativa = services["parametro_bool"](parametros_financeiros.get('baixa.permitir_data_retroativa', {}).get('valor'))
            try:
                limite_dias_retroativo = max(0, int(parametros_financeiros.get('baixa.limite_dias_retroativo', {}).get('valor') or 0))
            except Exception:
                limite_dias_retroativo = 0

            data_pagamento_dt = datetime.strptime(data_pagamento, '%Y-%m-%d').date()
            hoje = date.today()
            if data_pagamento_dt > hoje:
                flash('Baixa com data futura não é permitida. Use vencimento/agendamento para eventos futuros.', 'warning')
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))
            if data_pagamento_dt < hoje:
                if not permitir_data_retroativa:
                    flash('Baixa retroativa bloqueada pelas configurações financeiras da empresa.', 'warning')
                    return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))
                if limite_dias_retroativo > 0 and (hoje - data_pagamento_dt).days > limite_dias_retroativo:
                    flash(
                        f'Baixa retroativa limitada a {limite_dias_retroativo} dia(s) pelas configurações financeiras da empresa.',
                        'warning'
                    )
                    return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            if exigir_comprovante_baixa and (not comprovante or not getattr(comprovante, 'filename', '')):
                flash('Comprovante obrigatório para baixa, conforme configuração financeira da empresa.', 'warning')
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            status_atual = titulo.get('status_titulo') or 'Aberto'
            if status_atual in ['Pago', 'Recebido', 'Cancelado', 'Estornado']:
                flash(f"Este título não pode ser baixado. Status atual: {status_atual}.", "warning")
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            # Proteção contra duplicidade: se já existe movimentação ativa para este título,
            # não cria outra baixa mesmo que o status do título ainda não tenha sido atualizado.
            movimentacoes_ativas = services["buscar_movimentacoes_baixa_nao_estornadas"](
                cur,
                titulo_id=id,
                empresa_id=titulo['empresa_id']
            )
            movimentacao_existente = movimentacoes_ativas[0] if movimentacoes_ativas else None
            if movimentacao_existente:
                flash(
                    "Este título já possui uma movimentação de caixa ativa vinculada. "
                    "A baixa não foi duplicada. Abra as movimentações do título para conferir.",
                    "warning"
                )
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            valor_liquido = services["converter_decimal"](titulo.get('valor_liquido'))
            if valor_pago <= 0:
                flash("Informe um valor de baixa maior que zero.", "danger")
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            if valor_pago != valor_liquido:
                flash(
                    'O valor da baixa precisa ser igual ao valor líquido do título. Diferenças devem ser tratadas por desconto, acréscimo ou futura baixa parcial formal.',
                    'warning'
                )
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            cur.execute("""
                SELECT id, nome_conta, status_conta
                FROM contas_caixa
                WHERE id = %s
                  AND empresa_id = %s
                  AND status_conta = 'Ativa'
                LIMIT 1
            """, (conta_caixa_id, titulo['empresa_id']))
            conta = cur.fetchone()
            if not conta:
                flash("Conta caixa inválida, inativa ou não pertence à empresa do título.", "danger")
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            tipo_movimentacao = 'SAIDA' if titulo.get('tipo_titulo') == 'PAGAR' else 'ENTRADA'
            novo_status = 'Pago' if titulo.get('tipo_titulo') == 'PAGAR' else 'Recebido'

            if tipo_movimentacao == 'SAIDA':
                saldo_info = services["calcular_saldo_conta_caixa"](cur, conta_caixa_id, titulo['empresa_id'])
                saldo_atual = services["converter_decimal"]((saldo_info or {}).get('saldo_atual'))
                if saldo_atual < valor_pago and not permitir_saldo_negativo:
                    flash(
                        f"Baixa bloqueada: a conta caixa '{conta['nome_conta']}' possui saldo de {services["moeda_br"](saldo_atual)}, "
                        f"menor que o valor do pagamento {services["moeda_br"](valor_pago)}. "
                        "A empresa está configurada para não permitir caixa negativo.",
                        "danger"
                    )
                    return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            comprovante_url = services["salvar_comprovante_baixa_titulo"](
                cur,
                comprovante,
                empresa_id=titulo['empresa_id'],
                titulo_id=id,
                pessoa_id=titulo.get('pessoa_id'),
                usuario_id=usuario_id,
            )

            historico_mov = (
                f"Baixa do título #{id} - {titulo.get('descricao') or titulo.get('numero_documento')}"
            )

            # Segunda checagem dentro do fluxo imediatamente antes de inserir,
            # reduzindo risco de duplicidade em duplo clique ou retentativa do navegador.
            if services["buscar_movimentacoes_baixa_nao_estornadas"](
                cur,
                titulo_id=id,
                empresa_id=titulo['empresa_id']
            ):
                flash(
                    "Este título já possui baixa registrada. A operação não foi duplicada.",
                    "warning"
                )
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            cur.execute("""
                INSERT INTO movimentacoes_caixa
                    (empresa_id, conta_caixa_id, titulo_financeiro_id, tipo_movimentacao,
                     data_movimentacao, valor_movimentacao, forma_pagamento, historico,
                     observacao, comprovante_url, status_movimentacao, usuario_criacao_id)
                VALUES
                    (%s, %s, %s, %s,
                     %s, %s, %s, %s,
                     %s, %s, 'Ativa', %s)
            """, (
                titulo['empresa_id'],
                conta_caixa_id,
                id,
                tipo_movimentacao,
                data_pagamento,
                valor_pago,
                forma_pagamento,
                historico_mov,
                observacao_baixa or None,
                comprovante_url,
                usuario_id
            ))

            cur.execute("""
                UPDATE titulos_financeiros
                SET status_titulo = %s,
                    conta_caixa_baixa_id = %s,
                    data_baixa = %s,
                    valor_baixado = %s,
                    forma_pagamento = %s,
                    observacao_baixa = %s,
                    comprovante_url = %s,
                    usuario_baixa_id = %s,
                    updated_at = NOW()
                WHERE id = %s
                  AND empresa_id = %s
            """, (
                novo_status,
                conta_caixa_id,
                data_pagamento,
                valor_pago,
                forma_pagamento,
                observacao_baixa or None,
                comprovante_url,
                usuario_id,
                id,
                titulo['empresa_id']
            ))

            if titulo.get('origem') in ['NF_MOTORISTA', 'SEM_NF_MOTORISTA']:
                services["aplicar_baixa_em_documento_motorista_e_rotas"](
                    cur,
                    titulo_id=id,
                    empresa_id=titulo['empresa_id'],
                    usuario_id=usuario_id
                )

            services["registrar_auditoria_financeira"](
                cur,
                empresa_id=titulo['empresa_id'],
                usuario_id=usuario_id,
                acao='BAIXA_TITULO',
                modulo='BAIXA_FINANCEIRA',
                entidade_tipo='TITULO_FINANCEIRO',
                entidade_id=id,
                titulo_financeiro_id=id,
                pessoa_id=titulo.get('pessoa_id'),
                status_anterior=status_atual,
                status_novo=novo_status,
                valor_anterior=titulo.get('valor_liquido'),
                valor_novo=valor_pago,
                motivo='Baixa financeira de título',
                observacao=observacao_baixa or f'Título #{id} baixado como {novo_status}.',
                dados_depois={
                    'conta_caixa_id': conta_caixa_id,
                    'data_pagamento': data_pagamento,
                    'forma_pagamento': forma_pagamento,
                    'tipo_movimentacao': tipo_movimentacao,
                    'comprovante_url': comprovante_url,
                }
            )
            con.commit()
            flash(f"Título financeiro #{id} baixado com sucesso como {novo_status}.", "success")
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        except Exception as e:
            try:
                con.rollback()
            except Exception as rollback_error:
                print(f"Aviso: não foi possível executar rollback da baixa do título {id}: {rollback_error}")

            print(f"Erro ao baixar título financeiro {id}: {e}")
            flash(
                "Erro técnico ao baixar título financeiro. "
                "A operação foi interrompida com segurança; confira se o título possui movimentação antes de tentar novamente.",
                "danger"
            )
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        finally:
            services["fechar_cursor_conexao"](cur, con)

    @financeiro_bp.route("/financeiro/titulos/<int:id>/estornar", methods=["POST"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro")
    def estornar_baixa_titulo_financeiro(id):
        empresa_logada_id = session.get('empresa_id')
        usuario_id = session.get('usuario_id')
        is_super_admin = services["usuario_eh_super_admin_global"]()

        motivo = (request.form.get('motivo_estorno') or '').strip()
        data_estorno = (request.form.get('data_estorno') or '').strip()
        destino = (request.form.get('destino_estorno') or '').strip()
        observacao_estorno = (request.form.get('observacao_estorno') or '').strip()

        if len(motivo) < 5:
            flash("Informe um motivo de estorno com pelo menos 5 caracteres.", "warning")
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        if not data_estorno or not services["validar_data_iso"](data_estorno):
            flash("Informe uma data de estorno válida.", "danger")
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        if destino not in ['reabrir', 'encerrar']:
            flash("Selecione o destino do título após o estorno.", "danger")
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        con = services["obter_conexao"]()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for('financeiro.financeiro_titulos'))

        cur = con.cursor(dictionary=True)
        try:
            query = """
                SELECT id, empresa_id, tipo_titulo, origem, origem_id, pessoa_id, numero_documento,
                       descricao, historico, valor_liquido, status_titulo, data_baixa, valor_baixado
                FROM titulos_financeiros
                WHERE id = %s
            """
            params = [id]
            if not is_super_admin:
                query += " AND empresa_id = %s"
                params.append(empresa_logada_id)
            query += " LIMIT 1"
            cur.execute(query, params)
            titulo = cur.fetchone()

            if not titulo:
                flash("Título financeiro não encontrado ou não pertence à empresa logada.", "danger")
                return redirect(url_for('financeiro.financeiro_titulos'))

            status_atual = titulo.get('status_titulo') or ''
            if status_atual not in ['Pago', 'Recebido']:
                flash(f"Somente títulos pagos ou recebidos podem ter a baixa estornada. Status atual: {status_atual}.", "warning")
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            movimentacoes = services["buscar_movimentacoes_baixa_nao_estornadas"](
                cur,
                titulo_id=id,
                empresa_id=titulo['empresa_id']
            )
            if not movimentacoes:
                flash("Nenhuma movimentação de baixa ativa foi encontrada para estornar este título.", "warning")
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            for mov in movimentacoes:
                tipo_inverso = 'ENTRADA' if mov.get('tipo_movimentacao') == 'SAIDA' else 'SAIDA'
                historico_estorno = f"Estorno da movimentação #{mov.get('id')} / título #{id} - {titulo.get('descricao') or titulo.get('numero_documento')}"
                obs_estorno = f"Motivo: {motivo}"
                if observacao_estorno:
                    obs_estorno += f" | Observação: {observacao_estorno}"

                cur.execute("""
                    INSERT INTO movimentacoes_caixa
                        (empresa_id, conta_caixa_id, titulo_financeiro_id, tipo_movimentacao,
                         data_movimentacao, valor_movimentacao, forma_pagamento, historico,
                         observacao, comprovante_url, status_movimentacao, usuario_criacao_id,
                         estorno_de_movimentacao_id, motivo_estorno)
                    VALUES
                        (%s, %s, %s, %s,
                         %s, %s, %s, %s,
                         %s, NULL, 'Estorno', %s,
                         %s, %s)
                """, (
                    titulo['empresa_id'],
                    mov.get('conta_caixa_id'),
                    id,
                    tipo_inverso,
                    data_estorno,
                    services["converter_decimal"](mov.get('valor_movimentacao')),
                    mov.get('forma_pagamento') or titulo.get('forma_pagamento'),
                    historico_estorno,
                    obs_estorno,
                    usuario_id,
                    mov.get('id'),
                    motivo
                ))

                cur.execute("""
                    UPDATE movimentacoes_caixa
                    SET status_movimentacao = 'Estornada',
                        motivo_estorno = %s
                    WHERE id = %s
                      AND empresa_id = %s
                      AND titulo_financeiro_id = %s
                """, (motivo, mov.get('id'), titulo['empresa_id'], id))

            if destino == 'reabrir':
                novo_status = 'Solicitado' if titulo.get('origem') in ['NF_MOTORISTA', 'SEM_NF_MOTORISTA'] else 'Aberto'
            else:
                novo_status = 'Estornado'

            obs_titulo = (
                f"Baixa estornada em {datetime.now().strftime('%d/%m/%Y %H:%M')}. "
                f"Destino: {'reaberto para nova baixa' if destino == 'reabrir' else 'encerrado como estornado'}. "
            )
            if destino == 'encerrar' and titulo.get('origem') in ['NF_MOTORISTA', 'SEM_NF_MOTORISTA']:
                obs_titulo += "Tratativa pós-estorno pendente. "
            obs_titulo += f"Motivo: {motivo}"
            if observacao_estorno:
                obs_titulo += f". Observação: {observacao_estorno}"

            if destino == 'reabrir':
                cur.execute("""
                    UPDATE titulos_financeiros
                    SET status_titulo = %s,
                        conta_caixa_baixa_id = NULL,
                        data_baixa = NULL,
                        valor_baixado = NULL,
                        usuario_baixa_id = NULL,
                        data_estorno = NOW(),
                        motivo_estorno = %s,
                        usuario_estorno_id = %s,
                        destino_estorno = %s,
                        observacao_baixa = CONCAT(
                            COALESCE(observacao_baixa, ''),
                            CASE WHEN COALESCE(observacao_baixa, '') = '' THEN '' ELSE '\n' END,
                            %s
                        ),
                        updated_at = NOW()
                    WHERE id = %s
                      AND empresa_id = %s
                """, (
                    novo_status,
                    motivo,
                    usuario_id,
                    destino,
                    obs_titulo,
                    id,
                    titulo['empresa_id']
                ))
            else:
                cur.execute("""
                    UPDATE titulos_financeiros
                    SET status_titulo = %s,
                        data_estorno = NOW(),
                        motivo_estorno = %s,
                        usuario_estorno_id = %s,
                        destino_estorno = %s,
                        tratativa_pos_estorno_aplicada = 0,
                        tipo_tratativa_pos_estorno = NULL,
                        data_tratativa_pos_estorno = NULL,
                        usuario_tratativa_pos_estorno_id = NULL,
                        motivo_tratativa_pos_estorno = NULL,
                        observacao_tratativa_pos_estorno = NULL,
                        observacao_baixa = CONCAT(
                            COALESCE(observacao_baixa, ''),
                            CASE WHEN COALESCE(observacao_baixa, '') = '' THEN '' ELSE '\n' END,
                            %s
                        ),
                        updated_at = NOW()
                    WHERE id = %s
                      AND empresa_id = %s
                """, (
                    novo_status,
                    motivo,
                    usuario_id,
                    destino,
                    obs_titulo,
                    id,
                    titulo['empresa_id']
                ))

            cur.execute("""
                INSERT INTO historico_operacoes
                    (empresa_id, tipo_operacao, usuario_id, status_anterior, status_novo, motivo, observacao)
                VALUES
                    (%s, 'TITULO_FINANCEIRO', %s, %s, %s, 'Estorno de baixa financeira', %s)
            """, (
                titulo['empresa_id'],
                usuario_id,
                status_atual,
                novo_status,
                f"Título #{id} estornado. Destino: {destino}. Motivo: {motivo}"
            ))

            if titulo.get('origem') in ['NF_MOTORISTA', 'SEM_NF_MOTORISTA']:
                # Reabrir sincroniza imediatamente. Encerrar coloca NF/rotas
                # em estado seguro até a decisão explícita do Blueprint 12.
                services["aplicar_estorno_em_documento_motorista_e_rotas"](
                    cur,
                    titulo_id=id,
                    empresa_id=titulo['empresa_id'],
                    usuario_id=usuario_id,
                    motivo=motivo,
                    destino=destino,
                    tratativa_pos_estorno='manter_bloqueadas'
                )

            services["registrar_auditoria_financeira"](
                cur,
                empresa_id=titulo['empresa_id'],
                usuario_id=usuario_id,
                acao='ESTORNO_BAIXA_TITULO',
                modulo='ESTORNO_FINANCEIRO',
                entidade_tipo='TITULO_FINANCEIRO',
                entidade_id=id,
                titulo_financeiro_id=id,
                pessoa_id=titulo.get('pessoa_id'),
                status_anterior=status_atual,
                status_novo=novo_status,
                valor_anterior=titulo.get('valor_baixado') or titulo.get('valor_liquido'),
                valor_novo=0,
                motivo=motivo,
                observacao=f'Título #{id} estornado. Destino: {destino}.',
                dados_depois={
                    'destino': destino,
                    'tratativa_pos_estorno': (
                        'pendente'
                        if destino == 'encerrar' and titulo.get('origem') in ['NF_MOTORISTA', 'SEM_NF_MOTORISTA']
                        else None
                    )
                }
            )
            con.commit()
            if destino == 'reabrir':
                flash(f"Baixa do título #{id} estornada com sucesso. O título foi reaberto para nova baixa.", "success")
            else:
                if titulo.get('origem') in ['NF_MOTORISTA', 'SEM_NF_MOTORISTA']:
                    flash(
                        f"Baixa do título #{id} estornada com sucesso. "
                        "O título foi encerrado como Estornado e aguarda tratativa pós-estorno.",
                        "success"
                    )
                else:
                    flash(f"Baixa do título #{id} estornada com sucesso. O título foi encerrado como Estornado.", "success")
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        except Exception as e:
            try:
                con.rollback()
            except Exception as rollback_error:
                print(f"Aviso: não foi possível executar rollback do estorno do título {id}: {rollback_error}")
            print(f"Erro ao estornar baixa do título financeiro {id}: {e}")
            flash("Erro técnico ao estornar baixa financeira.", "danger")
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))
        finally:
            services["fechar_cursor_conexao"](cur, con)

    @financeiro_bp.route("/financeiro/titulos/<int:id>/tratativa-pos-estorno", methods=["POST"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro")
    def tratar_pos_estorno_titulo_financeiro(id):
        empresa_logada_id = session.get('empresa_id')
        usuario_id = session.get('usuario_id')
        is_super_admin = services["usuario_eh_super_admin_global"]()

        tratativa = (request.form.get('tratativa_pos_estorno_manual') or '').strip()
        motivo = (request.form.get('motivo_tratativa_pos_estorno') or '').strip()
        observacao = (request.form.get('observacao_tratativa_pos_estorno') or '').strip()

        tratativas_validas = {
            'manter_bloqueadas': 'Manter rotas bloqueadas para análise',
            'reabrir_mesmo_documento': 'Reaproveitar mesmo documento para nova solicitação',
            'exigir_nova_nf': 'Liberar rotas exigindo novo documento/NF',
            'cancelar_rotas': 'Cancelar rotas definitivamente',
        }

        if tratativa not in tratativas_validas:
            flash('Selecione uma tratativa válida para o pós-estorno.', 'warning')
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        if len(motivo) < 5:
            flash('Informe um motivo com pelo menos 5 caracteres para a tratativa.', 'warning')
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        con = services["obter_conexao"]()
        if con is None:
            flash('Erro de conexão com o banco de dados.', 'danger')
            return redirect(url_for('financeiro.financeiro_titulos'))

        cur = con.cursor(dictionary=True)
        try:
            query = """
                SELECT id, empresa_id, origem, origem_id, status_titulo, numero_documento, descricao,
                       tratativa_pos_estorno_aplicada, tipo_tratativa_pos_estorno,
                       data_tratativa_pos_estorno, usuario_tratativa_pos_estorno_id,
                       motivo_tratativa_pos_estorno, observacao_tratativa_pos_estorno,
                       observacao_baixa
                FROM titulos_financeiros
                WHERE id = %s
            """
            params = [id]
            if not is_super_admin:
                query += " AND empresa_id = %s"
                params.append(empresa_logada_id)
            query += " LIMIT 1"

            cur.execute(query, params)
            titulo = cur.fetchone()

            if not titulo:
                flash('Título financeiro não encontrado ou não pertence à empresa logada.', 'danger')
                return redirect(url_for('financeiro.financeiro_titulos'))

            if titulo.get('status_titulo') != 'Estornado':
                flash('A tratativa pós-estorno só pode ser aplicada em títulos com status Estornado.', 'warning')
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            if titulo.get('origem') not in ['NF_MOTORISTA', 'SEM_NF_MOTORISTA']:
                flash('Este título não possui documento de motorista vinculado para tratativa pós-estorno.', 'warning')
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            tratativa_ja_aplicada = bool(titulo.get('tratativa_pos_estorno_aplicada'))
            if not tratativa_ja_aplicada and titulo.get('observacao_baixa') and 'Tratativa pós-estorno aplicada' in str(titulo.get('observacao_baixa')):
                tratativa_ja_aplicada = True

            if tratativa_ja_aplicada:
                flash('Este título já possui tratativa pós-estorno aplicada. A decisão é final e não pode ser alterada por esta tela.', 'warning')
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            parametros_financeiros = services["carregar_parametros_financeiros_empresa"](titulo['empresa_id'], cur=cur)
            if tratativa == 'reabrir_mesmo_documento' and not services["parametro_bool"](parametros_financeiros.get('documentos.permitir_reaproveitar_pos_estorno', {}).get('valor')):
                flash('Reaproveitar documento após estorno está bloqueado nas configurações financeiras da empresa.', 'warning')
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            texto_tratativa = tratativas_validas.get(tratativa, tratativa)
            obs_titulo = (
                f"Tratativa pós-estorno aplicada em {datetime.now().strftime('%d/%m/%Y %H:%M')}. "
                f"Tratativa: {texto_tratativa}. Motivo: {motivo}"
            )
            if observacao:
                obs_titulo += f". Observação: {observacao}"

            # O estorno definitivo já deixa NF/rotas em estado seguro.
            # Só decisões que alteram esse estado exigem nova sincronização.
            if tratativa != 'manter_bloqueadas':
                services["aplicar_estorno_em_documento_motorista_e_rotas"](
                    cur,
                    titulo_id=id,
                    empresa_id=titulo['empresa_id'],
                    usuario_id=usuario_id,
                    motivo=motivo,
                    destino='encerrar',
                    tratativa_pos_estorno=tratativa
                )

            cur.execute("""
                UPDATE titulos_financeiros
                SET tratativa_pos_estorno_aplicada = 1,
                    tipo_tratativa_pos_estorno = %s,
                    data_tratativa_pos_estorno = NOW(),
                    usuario_tratativa_pos_estorno_id = %s,
                    motivo_tratativa_pos_estorno = %s,
                    observacao_tratativa_pos_estorno = %s,
                    observacao_baixa = CONCAT(
                        COALESCE(observacao_baixa, ''),
                        CASE WHEN COALESCE(observacao_baixa, '') = '' THEN '' ELSE '
    ' END,
                        %s
                    ),
                    updated_at = NOW()
                WHERE id = %s
                  AND empresa_id = %s
                  AND COALESCE(tratativa_pos_estorno_aplicada, 0) = 0
            """, (tratativa, usuario_id, motivo, observacao or None, obs_titulo, id, titulo['empresa_id']))

            if cur.rowcount == 0:
                con.rollback()
                flash('Este título já recebeu uma tratativa pós-estorno. A decisão anterior foi preservada.', 'warning')
                return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

            cur.execute("""
                INSERT INTO historico_operacoes
                    (empresa_id, tipo_operacao, usuario_id, status_anterior, status_novo, motivo, observacao)
                VALUES
                    (%s, 'TRATATIVA_POS_ESTORNO', %s, 'Estornado', 'Estornado', %s, %s)
            """, (
                titulo['empresa_id'],
                usuario_id,
                motivo,
                f"Título #{id}. {obs_titulo}"
            ))

            services["registrar_auditoria_financeira"](
                cur,
                empresa_id=titulo['empresa_id'],
                usuario_id=usuario_id,
                acao='TRATATIVA_POS_ESTORNO_APLICADA',
                modulo='ESTORNO_FINANCEIRO',
                entidade_tipo='TITULO_FINANCEIRO',
                entidade_id=id,
                titulo_financeiro_id=id,
                status_anterior='Estornado',
                status_novo='Estornado',
                motivo=motivo,
                observacao=f'Título #{id}. {obs_titulo}',
                dados_depois={'tratativa': tratativa, 'texto_tratativa': texto_tratativa}
            )
            con.commit()
            flash(f'Tratativa pós-estorno aplicada com sucesso: {texto_tratativa}.', 'success')
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))

        except Exception as e:
            try:
                con.rollback()
            except Exception as rollback_error:
                print(f"Aviso: não foi possível executar rollback da tratativa pós-estorno do título {id}: {rollback_error}")
            print(f"Erro na tratativa pós-estorno do título financeiro {id}: {e}")
            flash('Erro técnico ao aplicar tratativa pós-estorno.', 'danger')
            return redirect(url_for('financeiro.detalhes_titulo_financeiro', id=id))
        finally:
            services["fechar_cursor_conexao"](cur, con)

    @financeiro_bp.route("/financeiro/configuracoes", methods=["GET", "POST"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def financeiro_configuracoes():
        empresa_logada_id = session.get("empresa_id")
        usuario_id = session.get("usuario_id")
        is_super_admin = services["usuario_eh_super_admin_global"]()

        if not empresa_logada_id:
            flash("Empresa não identificada na sessão. Faça login novamente.", "danger")
            return redirect(url_for("logout"))

        con = services["obter_conexao"]()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("financeiro.financeiro_titulos"))

        cur = con.cursor(dictionary=True)
        try:
            defs = services["PARAMETROS_FINANCEIROS_PADRAO"]
            empresa_id_config = (
                (request.values.get("empresa_id") or "").strip()
                if is_super_admin
                else str(empresa_logada_id)
            )
            if not empresa_id_config or not empresa_id_config.isdigit():
                empresa_id_config = str(empresa_logada_id)
            empresa_id_config = int(empresa_id_config)

            if not is_super_admin and empresa_id_config != int(empresa_logada_id):
                flash("Você não tem permissão para alterar configurações de outra empresa.", "danger")
                return redirect(url_for("financeiro.financeiro_configuracoes"))

            cur.execute(
                "SELECT id, nome_fantasia, razao_social FROM empresas WHERE id = %s LIMIT 1",
                (empresa_id_config,),
            )
            empresa_config = cur.fetchone()
            if not empresa_config:
                flash("Empresa não encontrada para configuração.", "danger")
                return redirect(url_for("financeiro.financeiro_titulos"))

            parametros_carregados = services["carregar_parametros_financeiros_empresa"](
                empresa_id_config, cur=cur
            )

            if request.method == "POST":
                dados_antes = {
                    chave: (parametros_carregados.get(chave, {}) or {}).get("valor", base.get("valor", ""))
                    for chave, base in defs.items()
                }
                valores_normalizados = {}

                for chave, base in defs.items():
                    tipo = base.get("tipo")
                    valor = "1" if tipo == "boolean" and request.form.get(chave) == "1" else (
                        "0" if tipo == "boolean" else (request.form.get(chave) or "").strip()
                    )

                    if chave == "titulos.modo_geracao_documento":
                        valor = valor.upper()
                        if valor not in {"AUTOMATICO", "ASSISTIDO"}:
                            valor = "AUTOMATICO"
                    elif chave == "baixa.limite_dias_retroativo":
                        try:
                            valor = str(min(3650, max(0, int(valor or 0))))
                        except Exception:
                            valor = "30"
                    elif chave == "titulos.dias_padrao_vencimento_motorista":
                        try:
                            valor = str(min(365, max(0, int(valor or 0))))
                        except Exception:
                            valor = "5"
                    elif chave == "caixa.forma_pagamento_padrao":
                        if valor not in services["financeiro_base_formas_pagamento"]():
                            valor = "PIX"
                    elif chave == "caixa.conta_padrao_id" and valor:
                        if not valor.isdigit():
                            valor = ""
                        else:
                            cur.execute(
                                """SELECT id FROM contas_caixa
                                   WHERE id = %s AND empresa_id = %s AND status_conta = 'Ativa'
                                   LIMIT 1""",
                                (int(valor), empresa_id_config),
                            )
                            if not cur.fetchone():
                                valor = ""

                    services["salvar_parametro_empresa"](
                        cur, empresa_id_config, chave, valor, usuario_id=usuario_id
                    )
                    valores_normalizados[chave] = valor

                cur.execute(
                    """INSERT INTO historico_operacoes
                       (empresa_id, tipo_operacao, usuario_id, status_anterior, status_novo, motivo, observacao)
                       VALUES (%s, 'CONFIGURACOES_FINANCEIRAS', %s, 'Parâmetros anteriores',
                               'Parâmetros atualizados', 'Atualização de parâmetros financeiros', %s)""",
                    (empresa_id_config, usuario_id,
                     f"Configurações financeiras essenciais atualizadas para a empresa #{empresa_id_config}."),
                )
                services["registrar_auditoria_financeira"](
                    cur,
                    empresa_id=empresa_id_config,
                    usuario_id=usuario_id,
                    acao="CONFIGURACAO_FINANCEIRA_ATUALIZADA",
                    modulo="CONFIGURACOES_FINANCEIRAS",
                    entidade_tipo="EMPRESA_PARAMETROS",
                    entidade_id=empresa_id_config,
                    status_anterior="Parâmetros anteriores",
                    status_novo="Parâmetros atualizados",
                    motivo="Atualização de parâmetros financeiros",
                    observacao=f"Configurações financeiras essenciais atualizadas para a empresa #{empresa_id_config}.",
                    dados_antes=dados_antes,
                    dados_depois=valores_normalizados,
                )
                con.commit()
                flash("Configurações financeiras salvas com sucesso.", "success")
                return redirect(url_for(
                    "financeiro.financeiro_configuracoes",
                    empresa_id=empresa_id_config if is_super_admin else None,
                ))

            parametros = {}
            for chave, base in defs.items():
                atual = (parametros_carregados.get(chave, {}) or {}).get("valor")
                item = dict(base)
                item["valor"] = base.get("valor", "") if atual is None else atual
                parametros[chave] = item

            empresas = []
            if is_super_admin:
                cur.execute("SELECT id, nome_fantasia, razao_social FROM empresas ORDER BY nome_fantasia ASC")
                empresas = cur.fetchall()

            contas_caixa = services["carregar_contas_caixa_financeiro"](
                empresa_id_config, True, somente_ativas=True
            )
            grupos = {
                "baixa": "Baixas",
                "caixa": "Caixa",
                "documentos": "Documentos de prestadores",
                "titulos": "Títulos automáticos",
            }
            return render_template(
                "financeiro_configuracoes.html",
                parametros=parametros,
                grupos=grupos,
                empresa_config=empresa_config,
                empresas=empresas,
                empresa_id_config=empresa_id_config,
                is_super_admin=is_super_admin,
                contas_caixa=contas_caixa,
                formas_pagamento=services["financeiro_base_formas_pagamento"](),
            )
        except Exception as exc:
            try:
                con.rollback()
            except Exception:
                pass
            print(f"Erro ao carregar/salvar configurações financeiras: {exc}")
            flash("Erro técnico ao processar configurações financeiras.", "danger")
            return redirect(url_for("financeiro.financeiro_titulos"))
        finally:
            services["fechar_cursor_conexao"](cur, con)

    return financeiro_bp
