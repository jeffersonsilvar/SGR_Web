from decimal import Decimal

from flask import Blueprint, render_template, session


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

    return financeiro_bp
