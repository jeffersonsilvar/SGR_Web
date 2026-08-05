from datetime import date
from decimal import Decimal


def autenticar(client, empresa_id=10, perfil="Financeiro"):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = empresa_id
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = 1


def test_titulos_financeiros_exige_autenticacao(client):
    resposta = client.get(
        "/financeiro/titulos",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_titulos_financeiros_registrado(app):
    regras = {
        regra.endpoint: regra.rule
        for regra in app.url_map.iter_rules()
    }

    assert (
        regras["financeiro.financeiro_titulos"]
        == "/financeiro/titulos"
    )


def test_titulos_sem_empresa_redireciona_logout(client):
    autenticar(client, empresa_id=None)

    resposta = client.get(
        "/financeiro/titulos",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/logout" in resposta.headers["Location"]


def test_titulos_banco_indisponivel(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]
    monkeypatch.setitem(services, "obter_conexao", lambda: None)
    autenticar(client)

    resposta = client.get(
        "/financeiro/titulos",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/" in resposta.headers["Location"]


def test_titulos_renderiza_listagem_e_resumo(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]

    class CursorFalso:
        def __init__(self):
            self.execucoes = []
            self._retorno = []

        def execute(self, query, params=None):
            self.execucoes.append((query, params or []))
            if "FROM titulos_financeiros" in query:
                self._retorno = [
                    {
                        "id": 1,
                        "empresa_id": 10,
                        "tipo_titulo": "RECEBER",
                        "origem": "MANUAL",
                        "numero_documento": "DOC-001",
                        "descricao": "Recebimento teste",
                        "historico": "Teste",
                        "valor_liquido": Decimal("150.00"),
                        "data_emissao": date.today(),
                        "data_vencimento": date.today(),
                        "status_titulo": "Aberto",
                        "pessoa_nome": "Cliente Teste",
                        "pessoa_cpf_cnpj": "00.000.000/0001-00",
                        "conta_caixa_nome": "Conta Principal",
                        "empresa_nome": "Empresa Teste",
                        "empresa_razao_social": "Empresa Teste Ltda",
                    }
                ]
            elif "FROM empresas" in query:
                self._retorno = []

        def fetchall(self):
            return self._retorno

    class ConexaoFalsa:
        def __init__(self):
            self.cursor_obj = CursorFalso()

        def cursor(self, dictionary=False):
            return self.cursor_obj

    conexao = ConexaoFalsa()

    monkeypatch.setitem(
        services,
        "obter_conexao",
        lambda: conexao,
    )
    monkeypatch.setitem(
        services,
        "fechar_cursor_conexao",
        lambda cursor, con: None,
    )
    monkeypatch.setitem(
        services,
        "carregar_pessoas_financeiro",
        lambda empresa_id, is_super_admin: [],
    )
    monkeypatch.setitem(
        services,
        "carregar_contas_caixa_financeiro",
        lambda empresa_id, is_super_admin: [],
    )

    autenticar(client)
    resposta = client.get(
        "/financeiro/titulos"
        "?tipo_titulo=RECEBER"
        "&status_titulo=Aberto"
        "&origem=MANUAL"
        "&pesquisa=Cliente"
    )

    assert resposta.status_code == 200
    assert b"DOC-001" in resposta.data
    assert b"Cliente Teste" in resposta.data


def test_titulos_aplica_filtros(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]
    consultas = []

    class CursorFalso:
        def execute(self, query, params=None):
            consultas.append(
                {
                    "query": query,
                    "params": params or [],
                }
            )

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
        lambda cursor, con: None,
    )
    monkeypatch.setitem(
        services,
        "carregar_pessoas_financeiro",
        lambda empresa_id, is_super_admin: [],
    )
    monkeypatch.setitem(
        services,
        "carregar_contas_caixa_financeiro",
        lambda empresa_id, is_super_admin: [],
    )

    autenticar(client)
    resposta = client.get(
        "/financeiro/titulos"
        "?tipo_titulo=PAGAR"
        "&status_titulo=Aberto"
        "&origem=MANUAL"
        "&pessoa_id=5"
        "&data_inicio=2026-08-01"
        "&data_fim=2026-08-31"
        "&vencimento_inicio=2026-08-01"
        "&vencimento_fim=2026-09-30"
        "&pesquisa=Fornecedor"
        "&empresa_id=10"
    )

    assert resposta.status_code == 200

    consulta_titulos = next(
        item
        for item in consultas
        if "FROM titulos_financeiros" in item["query"]
    )

    params = consulta_titulos["params"]

    assert 10 in params
    assert "PAGAR" in params
    assert "Aberto" in params
    assert "MANUAL" in params
    assert 5 in params
    assert "2026-08-01" in params
    assert "2026-08-31" in params
    assert "2026-09-30" in params
    assert "%Fornecedor%" in params
