from decimal import Decimal


def autenticar(client, perfil="Financeiro"):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = 10
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = 1


def test_conciliacao_caixa_exige_autenticacao(client):
    resposta = client.get(
        "/financeiro/conciliacao-caixa",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_conciliacao_caixa_registrado(app):
    regras = {
        regra.endpoint: regra.rule
        for regra in app.url_map.iter_rules()
    }

    assert (
        regras["financeiro.financeiro_conciliacao_caixa"]
        == "/financeiro/conciliacao-caixa"
    )


def test_conciliacao_caixa_renderiza_movimentacoes(
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
                    "id": 101,
                    "tipo_movimentacao": "ENTRADA",
                    "valor_movimentacao": Decimal("100.00"),
                    "status_conciliacao_view": "Conciliada",
                    "status_movimentacao_view": "Ativa",
                    "historico": "Recebimento conciliado",
                    "conta_caixa_nome": "Conta Principal",
                },
                {
                    "id": 102,
                    "tipo_movimentacao": "SAIDA",
                    "valor_movimentacao": Decimal("25.00"),
                    "status_conciliacao_view": "Pendente",
                    "status_movimentacao_view": "Ativa",
                    "historico": "Pagamento pendente",
                    "conta_caixa_nome": "Conta Principal",
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

    autenticar(client)
    resposta = client.get(
        "/financeiro/conciliacao-caixa"
        "?data_inicio=2026-08-01&data_fim=2026-08-31"
    )

    assert resposta.status_code == 200
    assert b"Recebimento conciliado" in resposta.data
    assert b"Pagamento pendente" in resposta.data


def test_conciliacao_caixa_aplica_filtros(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]
    consulta = {}

    class CursorFalso:
        def execute(self, query, params):
            consulta["query"] = query
            consulta["params"] = params

        def fetchall(self):
            return []

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

    autenticar(client)
    resposta = client.get(
        "/financeiro/conciliacao-caixa"
        "?conta_caixa_id=3"
        "&status_conciliacao=Divergente"
        "&status_movimentacao=Ativa"
        "&tipo_movimentacao=ENTRADA"
        "&data_inicio=2026-08-01"
        "&data_fim=2026-08-31"
        "&pesquisa=cliente"
        "&empresa_id=10"
    )

    assert resposta.status_code == 200
    assert 10 in consulta["params"]
    assert 3 in consulta["params"]
    assert "Divergente" in consulta["params"]
    assert "Ativa" in consulta["params"]
    assert "ENTRADA" in consulta["params"]
    assert "%cliente%" in consulta["params"]


def test_conciliacao_caixa_banco_indisponivel(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]
    monkeypatch.setitem(services, "obter_conexao", lambda: None)

    autenticar(client)
    resposta = client.get(
        "/financeiro/conciliacao-caixa",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro" in resposta.headers["Location"]
