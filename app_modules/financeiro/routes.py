from datetime import date
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
            return redirect(url_for("financeiro_titulos"))

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
            return redirect(url_for("financeiro_dashboard"))

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
            return redirect(url_for("financeiro_dashboard"))
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

    return financeiro_bp
