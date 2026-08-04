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

    return financeiro_bp
