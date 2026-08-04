from decimal import Decimal


def test_contas_caixa_exige_autenticacao(client):
    resposta = client.get("/financeiro/contas-caixa", follow_redirects=False)

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_do_blueprint_foi_registrado(app):
    regras = {regra.endpoint: regra.rule for regra in app.url_map.iter_rules()}

    assert (
        regras["financeiro.financeiro_contas_caixa"]
        == "/financeiro/contas-caixa"
    )


def test_contas_caixa_renderiza_resumo(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]

    monkeypatch.setitem(
        services,
        "carregar_contas_caixa_financeiro",
        lambda empresa_id, is_super_admin, somente_ativas=False: [
            {
                "id": 1,
                "empresa_id": 10,
                "nome_conta": "Conta principal",
                "status_conta": "Ativa",
                "saldo_inicial": Decimal("100.00"),
            },
            {
                "id": 2,
                "empresa_id": 10,
                "nome_conta": "Conta secundária",
                "status_conta": "Inativa",
                "saldo_inicial": Decimal("50.00"),
            },
        ],
    )
    monkeypatch.setitem(services, "obter_conexao", lambda: None)

    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = 10
        sessao["perfil_de_acesso"] = "Financeiro"
        sessao["is_super_admin"] = 1

    resposta = client.get("/financeiro/contas-caixa")

    assert resposta.status_code == 200
    assert b"Conta principal" in resposta.data
    assert "Conta secundária".encode("utf-8") in resposta.data
