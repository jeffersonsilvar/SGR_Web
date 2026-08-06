from decimal import Decimal


def autenticar(client, empresa_id=10, perfil="Financeiro", super_admin=0):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = empresa_id
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = super_admin


def configurar_get(services, monkeypatch):
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
    monkeypatch.setitem(
        services,
        "carregar_parametros_financeiros_empresa",
        lambda empresa_id: {
            "caixa.conta_padrao_id": {"valor": ""},
            "caixa.forma_pagamento_padrao": {"valor": "PIX"},
        },
    )
    monkeypatch.setitem(services, "carregar_empresas_ativas", lambda: [])


def dados_validos():
    return {
        "tipo_titulo": "PAGAR",
        "pessoa_id": "5",
        "numero_documento": "DOC-100",
        "descricao": "Serviço de teste",
        "historico": "",
        "data_emissao": "2026-08-01",
        "data_competencia": "2026-08-01",
        "data_vencimento": "2026-08-31",
        "forma_pagamento": "PIX",
        "conta_caixa_prevista_id": "",
        "valor_original": "100,00",
        "valor_desconto": "10,00",
        "valor_acrescimo": "5,00",
        "observacao": "Teste automatizado",
    }


def test_novo_titulo_exige_autenticacao(client):
    resposta = client.get(
        "/financeiro/titulos/novo",
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_novo_titulo_registrado(app):
    regras = {
        regra.endpoint: (regra.rule, regra.methods)
        for regra in app.url_map.iter_rules()
    }
    rota, metodos = regras["financeiro.novo_titulo_financeiro"]
    assert rota == "/financeiro/titulos/novo"
    assert {"GET", "POST"}.issubset(metodos)


def test_novo_titulo_sem_empresa_redireciona_logout(client):
    autenticar(client, empresa_id=None)
    resposta = client.get(
        "/financeiro/titulos/novo",
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert "/logout" in resposta.headers["Location"]


def test_novo_titulo_renderiza_formulario(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    configurar_get(services, monkeypatch)
    autenticar(client)

    resposta = client.get("/financeiro/titulos/novo")

    assert resposta.status_code == 200
    assert b"Novo" in resposta.data
    assert b"DOC" in resposta.data


def test_novo_titulo_rejeita_tipo_invalido(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    configurar_get(services, monkeypatch)
    autenticar(client)
    dados = dados_validos()
    dados["tipo_titulo"] = "OUTRO"

    resposta = client.post(
        "/financeiro/titulos/novo",
        data=dados,
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/novo" in resposta.headers["Location"]


def test_novo_titulo_banco_indisponivel(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    configurar_get(services, monkeypatch)
    monkeypatch.setitem(services, "obter_conexao", lambda: None)
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/novo",
        data=dados_validos(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_novo_titulo_cria_e_registra_auditoria(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    configurar_get(services, monkeypatch)
    auditoria = {}
    execucoes = []

    class CursorFalso:
        lastrowid = 77

        def __init__(self):
            self.retorno = None

        def execute(self, query, params=None):
            execucoes.append((query, tuple(params or ())))
            if "FROM empresas" in query:
                self.retorno = {"id": 10}
            elif "FROM pessoas" in query:
                self.retorno = {
                    "id": 5,
                    "nome_completo": "Fornecedor Teste",
                }
            else:
                self.retorno = None

        def fetchone(self):
            return self.retorno

    class ConexaoFalsa:
        def __init__(self):
            self.cursor_obj = CursorFalso()
            self.commits = 0
            self.rollbacks = 0

        def cursor(self, dictionary=False):
            return self.cursor_obj

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.rollbacks += 1

    conexao = ConexaoFalsa()

    monkeypatch.setitem(services, "obter_conexao", lambda: conexao)
    monkeypatch.setitem(
        services,
        "fechar_cursor_conexao",
        lambda cursor, con: None,
    )
    monkeypatch.setitem(
        services,
        "registrar_auditoria_financeira",
        lambda cursor, **kwargs: auditoria.update(kwargs),
    )

    autenticar(client)
    resposta = client.post(
        "/financeiro/titulos/novo",
        data=dados_validos(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/77" in resposta.headers["Location"]
    assert conexao.commits == 1
    assert conexao.rollbacks == 0
    assert auditoria["acao"] == "TITULO_MANUAL_CRIADO"
    assert auditoria["entidade_id"] == 77
    assert auditoria["valor_novo"] == Decimal("95.00")

    insert = next(
        item
        for item in execucoes
        if "INSERT INTO titulos_financeiros" in item[0]
    )
    assert "DOC-100" in insert[1]
    assert Decimal("95.00") in insert[1]


def test_novo_titulo_faz_rollback_em_erro(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    configurar_get(services, monkeypatch)

    class CursorFalso:
        def execute(self, query, params=None):
            if "FROM empresas" in query:
                raise RuntimeError("falha simulada")

        def fetchone(self):
            return None

    class ConexaoFalsa:
        def __init__(self):
            self.rollbacks = 0

        def cursor(self, dictionary=False):
            return CursorFalso()

        def commit(self):
            raise AssertionError("commit não deveria ocorrer")

        def rollback(self):
            self.rollbacks += 1

    conexao = ConexaoFalsa()
    monkeypatch.setitem(services, "obter_conexao", lambda: conexao)
    monkeypatch.setitem(
        services,
        "fechar_cursor_conexao",
        lambda cursor, con: None,
    )

    autenticar(client)
    resposta = client.post(
        "/financeiro/titulos/novo",
        data=dados_validos(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/novo" in resposta.headers["Location"]
    assert conexao.rollbacks == 1
