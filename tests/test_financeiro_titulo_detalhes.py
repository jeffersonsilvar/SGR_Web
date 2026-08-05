from datetime import date
from decimal import Decimal


def autenticar(client, empresa_id=10, perfil="Financeiro", super_admin=1):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = empresa_id
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = super_admin


def test_detalhes_titulo_exige_autenticacao(client):
    resposta = client.get("/financeiro/titulos/1", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_detalhes_titulo_registrado(app):
    regras = {regra.endpoint: regra.rule for regra in app.url_map.iter_rules()}
    assert regras["financeiro.detalhes_titulo_financeiro"] == "/financeiro/titulos/<int:id>"


def test_detalhes_titulo_banco_indisponivel(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    monkeypatch.setitem(services, "obter_conexao", lambda: None)
    autenticar(client)
    resposta = client.get("/financeiro/titulos/1", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_detalhes_titulo_nao_encontrado(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]

    class CursorFalso:
        def execute(self, query, params=None):
            pass
        def fetchone(self):
            return None
        def fetchall(self):
            return []

    class ConexaoFalsa:
        def cursor(self, dictionary=False):
            return CursorFalso()

    monkeypatch.setitem(services, "obter_conexao", lambda: ConexaoFalsa())
    monkeypatch.setitem(services, "fechar_cursor_conexao", lambda cursor, con: None)
    autenticar(client)
    resposta = client.get("/financeiro/titulos/999", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_detalhes_titulo_restringe_empresa_usuario_comum(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    capturado = {}

    class CursorFalso:
        def execute(self, query, params=None):
            capturado["query"] = query
            capturado["params"] = list(params or [])
        def fetchone(self):
            return None
        def fetchall(self):
            return []

    class ConexaoFalsa:
        def cursor(self, dictionary=False):
            return CursorFalso()

    monkeypatch.setitem(services, "obter_conexao", lambda: ConexaoFalsa())
    monkeypatch.setitem(services, "fechar_cursor_conexao", lambda cursor, con: None)
    autenticar(client, empresa_id=10, super_admin=0)
    resposta = client.get("/financeiro/titulos/7", follow_redirects=False)
    assert resposta.status_code == 302
    assert "AND t.empresa_id = %s" in capturado["query"]
    assert capturado["params"] == [7, 10]


def test_detalhes_titulo_renderiza(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    execucoes = []

    titulo = {
        "id": 1,
        "empresa_id": 10,
        "tipo_titulo": "RECEBER",
        "status_titulo": "Aberto",
        "numero_documento": "DOC-001",
        "descricao": "Recebimento teste",
        "valor_liquido": Decimal("150.00"),
        "forma_pagamento": "PIX",
        "data_vencimento": date.today(),
        "pessoa_nome": "Cliente Teste",
        "pessoa_cpf_cnpj": "00.000.000/0001-00",
        "empresa_nome": "Empresa Teste",
    }

    class CursorFalso:
        def __init__(self):
            self.retorno_um = None
            self.retorno_varios = []
        def execute(self, query, params=None):
            execucoes.append((query, list(params or [])))
            if "FROM titulos_financeiros t" in query:
                self.retorno_um = titulo
                self.retorno_varios = []
            elif "FROM titulos_financeiros_vinculos" in query:
                self.retorno_um = None
                self.retorno_varios = []
            elif "FROM movimentacoes_caixa m" in query:
                self.retorno_um = None
                self.retorno_varios = []
            elif "FROM contas_caixa" in query:
                self.retorno_um = None
                self.retorno_varios = []
        def fetchone(self):
            return self.retorno_um
        def fetchall(self):
            return self.retorno_varios

    class ConexaoFalsa:
        def __init__(self):
            self.cursor_obj = CursorFalso()
        def cursor(self, dictionary=False):
            return self.cursor_obj

    monkeypatch.setitem(services, "obter_conexao", lambda: ConexaoFalsa())
    monkeypatch.setitem(services, "fechar_cursor_conexao", lambda cursor, con: None)
    monkeypatch.setitem(
        services,
        "carregar_parametros_financeiros_empresa",
        lambda empresa_id, cur=None: {
            "caixa.conta_padrao_id": {"valor": ""},
            "caixa.forma_pagamento_padrao": {"valor": "PIX"},
        },
    )
    monkeypatch.setitem(
        services,
        "calcular_saldo_conta_caixa",
        lambda cursor, conta_id, empresa_id: {"saldo_atual": Decimal("0.00")},
    )
    autenticar(client)
    resposta = client.get("/financeiro/titulos/1")
    assert resposta.status_code == 200
    assert b"DOC-001" in resposta.data
    assert b"Cliente Teste" in resposta.data
