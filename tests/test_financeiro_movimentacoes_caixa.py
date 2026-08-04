from decimal import Decimal


def test_movimentacoes_caixa_exige_autenticacao(client):
    resposta = client.get(
        "/financeiro/movimentacoes-caixa",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_movimentacoes_caixa_registrado(app):
    regras = {
        regra.endpoint: regra.rule
        for regra in app.url_map.iter_rules()
    }

    assert (
        regras["financeiro.financeiro_movimentacoes_caixa"]
        == "/financeiro/movimentacoes-caixa"
    )


def test_movimentacoes_caixa_renderiza_resumo(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]

    class CursorFalso:
        def execute(self, query, params):
            self.query = query
            self.params = params

        def fetchall(self):
            return [
                {
                    "id": 1,
                    "tipo_movimentacao": "ENTRADA",
                    "valor_movimentacao": Decimal("100.00"),
                    "status_movimentacao": "Ativa",
                    "estorno_de_movimentacao_id": None,
                    "historico": "Recebimento",
                },
                {
                    "id": 2,
                    "tipo_movimentacao": "SAIDA",
                    "valor_movimentacao": Decimal("25.00"),
                    "status_movimentacao": "Ativa",
                    "estorno_de_movimentacao_id": None,
                    "historico": "Pagamento",
                },
            ]

    class ConexaoFalsa:
        def cursor(self, dictionary=False):
            return CursorFalso()

    monkeypatch.setitem(
        services,
        "obter_conexao",
        lambda: ConexaoFalsa(),
    )
    monkeypatch.setitem(
        services,
        "fechar_cursor_conexao",
        lambda cursor, conexao: None,
    )
    monkeypatch.setitem(
        services,
        "carregar_contas_caixa_financeiro",
        lambda empresa_id, is_super_admin, somente_ativas=False: [],
    )
    monkeypatch.setitem(
        services,
        "carregar_empresas_ativas",
        lambda: [],
    )

    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = 10
        sessao["perfil_de_acesso"] = "Financeiro"
        sessao["is_super_admin"] = 1

    resposta = client.get("/financeiro/movimentacoes-caixa")

    assert resposta.status_code == 200
    assert b"Recebimento" in resposta.data
    assert b"Pagamento" in resposta.data


def test_movimentacoes_caixa_banco_indisponivel(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]
    monkeypatch.setitem(services, "obter_conexao", lambda: None)

    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = 10
        sessao["perfil_de_acesso"] = "Financeiro"
        sessao["is_super_admin"] = 1

    resposta = client.get(
        "/financeiro/movimentacoes-caixa",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
