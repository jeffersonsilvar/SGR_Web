def autenticar(client, empresa_id=10, perfil="Financeiro", super_admin=0):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = empresa_id
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = super_admin


def test_cancelar_titulo_exige_autenticacao(client):
    resposta = client.post(
        "/financeiro/titulos/8/cancelar",
        data={"motivo_cancelamento": "Motivo válido"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_cancelar_titulo_registrado(app):
    regras = {
        regra.endpoint: (regra.rule, regra.methods)
        for regra in app.url_map.iter_rules()
    }

    rota, metodos = regras["financeiro.cancelar_titulo_financeiro"]

    assert rota == "/financeiro/titulos/<int:id>/cancelar"
    assert "POST" in metodos


def test_cancelar_titulo_rejeita_motivo_curto(client):
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/cancelar",
        data={"motivo_cancelamento": "abc"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_cancelar_titulo_banco_indisponivel(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    monkeypatch.setitem(services, "obter_conexao", lambda: None)
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/cancelar",
        data={"motivo_cancelamento": "Cancelamento de teste"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_cancelar_titulo_nao_encontrado(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]

    class CursorFalso:
        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return None

    class ConexaoFalsa:
        def cursor(self, dictionary=False):
            return CursorFalso()

        def rollback(self):
            pass

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

    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/cancelar",
        data={"motivo_cancelamento": "Cancelamento de teste"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_cancelar_titulo_rejeita_status_final(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]

    class CursorFalso:
        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return {
                "id": 8,
                "empresa_id": 10,
                "status_titulo": "Pago",
            }

    class ConexaoFalsa:
        def cursor(self, dictionary=False):
            return CursorFalso()

        def rollback(self):
            pass

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

    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/cancelar",
        data={"motivo_cancelamento": "Cancelamento de teste"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_cancelar_titulo_atualiza_audita_e_commita(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]
    execucoes = []
    auditoria = {}

    class CursorFalso:
        def __init__(self):
            self._titulo = {
                "id": 8,
                "empresa_id": 10,
                "status_titulo": "Aberto",
            }

        def execute(self, query, params=None):
            execucoes.append((query, tuple(params or ())))

        def fetchone(self):
            return self._titulo

    class ConexaoFalsa:
        def __init__(self):
            self.commits = 0
            self.rollbacks = 0

        def cursor(self, dictionary=False):
            return CursorFalso()

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.rollbacks += 1

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
        "registrar_auditoria_financeira",
        lambda cursor, **kwargs: auditoria.update(kwargs),
    )

    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/cancelar",
        data={"motivo_cancelamento": "Documento lançado incorretamente"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]
    assert conexao.commits == 1
    assert conexao.rollbacks == 0

    update = next(
        item
        for item in execucoes
        if "UPDATE titulos_financeiros" in item[0]
    )

    assert "Documento lançado incorretamente" in update[1]
    assert auditoria["acao"] == "TITULO_CANCELADO"
    assert auditoria["entidade_id"] == 8
    assert auditoria["status_anterior"] == "Aberto"
    assert auditoria["status_novo"] == "Cancelado"


def test_cancelar_titulo_faz_rollback_em_erro(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]

    class CursorFalso:
        def __init__(self):
            self.chamadas = 0

        def execute(self, query, params=None):
            self.chamadas += 1
            if self.chamadas > 1:
                raise RuntimeError("falha simulada")

        def fetchone(self):
            return {
                "id": 8,
                "empresa_id": 10,
                "status_titulo": "Aberto",
            }

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

    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/cancelar",
        data={"motivo_cancelamento": "Documento lançado incorretamente"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]
    assert conexao.rollbacks == 1
