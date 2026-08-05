def autenticar(client, perfil="Financeiro", super_admin=True):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 7
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = 10
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = 1 if super_admin else 0


class CursorFalso:
    def __init__(self, rowcount=2, falhar=False):
        self.rowcount = rowcount
        self.falhar = falhar
        self.query = None
        self.params = None

    def execute(self, query, params):
        self.query = query
        self.params = params
        if self.falhar:
            raise RuntimeError("falha simulada")


class ConexaoFalsa:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.commits = 0
        self.rollbacks = 0

    def cursor(self, dictionary=False):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def configurar_services(app, monkeypatch, conexao, auditorias):
    services = app.extensions["financeiro_services"]
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
        lambda cursor, **kwargs: auditorias.append(kwargs),
    )


def test_acao_conciliacao_exige_autenticacao(client):
    resposta = client.post(
        "/financeiro/conciliacao-caixa/acao",
        data={"movimentacao_ids": ["1"], "acao": "conciliar"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_acao_conciliacao_registrado(app):
    regras = {
        (regra.endpoint, tuple(sorted(regra.methods))): regra.rule
        for regra in app.url_map.iter_rules()
    }

    assert any(
        endpoint
        == "financeiro.financeiro_conciliacao_caixa_acao"
        and regra
        == "/financeiro/conciliacao-caixa/acao"
        and "POST" in metodos
        for (endpoint, metodos), regra in regras.items()
    )


def test_acao_conciliacao_exige_ids(client):
    autenticar(client)

    resposta = client.post(
        "/financeiro/conciliacao-caixa/acao",
        data={"acao": "conciliar"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/conciliacao-caixa" in resposta.headers["Location"]


def test_acao_conciliacao_rejeita_acao_invalida(client):
    autenticar(client)

    resposta = client.post(
        "/financeiro/conciliacao-caixa/acao",
        data={
            "movimentacao_ids": ["1"],
            "acao": "acao_inexistente",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302


def test_divergente_exige_observacao(client):
    autenticar(client)

    resposta = client.post(
        "/financeiro/conciliacao-caixa/acao",
        data={
            "movimentacao_ids": ["1"],
            "acao": "divergente",
            "observacao_conciliacao": "",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302


def test_acao_conciliar_faz_commit_e_auditoria(
    client,
    app,
    monkeypatch,
):
    cursor = CursorFalso(rowcount=2)
    conexao = ConexaoFalsa(cursor)
    auditorias = []
    configurar_services(app, monkeypatch, conexao, auditorias)
    autenticar(client, super_admin=False)

    resposta = client.post(
        "/financeiro/conciliacao-caixa/acao",
        data={
            "movimentacao_ids": ["11", "12", "invalido"],
            "acao": "conciliar",
            "filtro_data_inicio": "2026-08-01",
            "filtro_data_fim": "2026-08-31",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert conexao.commits == 1
    assert conexao.rollbacks == 0
    assert len(auditorias) == 1
    assert auditorias[0]["status_novo"] == "Conciliada"
    assert auditorias[0]["dados_depois"]["ids"] == [11, 12]
    assert "empresa_id = %s" in cursor.query
    assert cursor.params[-1] == 10
    assert "data_inicio=2026-08-01" in resposta.headers["Location"]


def test_acao_pendente_limpa_dados_conciliacao(
    client,
    app,
    monkeypatch,
):
    cursor = CursorFalso(rowcount=1)
    conexao = ConexaoFalsa(cursor)
    auditorias = []
    configurar_services(app, monkeypatch, conexao, auditorias)
    autenticar(client)

    resposta = client.post(
        "/financeiro/conciliacao-caixa/acao",
        data={
            "movimentacao_ids": ["5"],
            "acao": "pendente",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert conexao.commits == 1
    assert "data_conciliacao = NULL" in cursor.query
    assert "usuario_conciliacao_id = NULL" in cursor.query
    assert auditorias[0]["status_novo"] == "Pendente"


def test_acao_nao_conciliavel_com_observacao(
    client,
    app,
    monkeypatch,
):
    cursor = CursorFalso(rowcount=1)
    conexao = ConexaoFalsa(cursor)
    auditorias = []
    configurar_services(app, monkeypatch, conexao, auditorias)
    autenticar(client)

    resposta = client.post(
        "/financeiro/conciliacao-caixa/acao",
        data={
            "movimentacao_ids": ["8"],
            "acao": "nao_conciliavel",
            "observacao_conciliacao": "Tarifa bancária",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert conexao.commits == 1
    assert auditorias[0]["status_novo"] == "Nao conciliavel"
    assert auditorias[0]["observacao"] == "Tarifa bancária"


def test_acao_conciliacao_faz_rollback_em_erro(
    client,
    app,
    monkeypatch,
):
    cursor = CursorFalso(falhar=True)
    conexao = ConexaoFalsa(cursor)
    auditorias = []
    configurar_services(app, monkeypatch, conexao, auditorias)
    autenticar(client)

    resposta = client.post(
        "/financeiro/conciliacao-caixa/acao",
        data={
            "movimentacao_ids": ["1"],
            "acao": "conciliar",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert conexao.commits == 0
    assert conexao.rollbacks == 1
    assert auditorias == []


def test_acao_conciliacao_banco_indisponivel(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]
    monkeypatch.setitem(services, "obter_conexao", lambda: None)
    autenticar(client)

    resposta = client.post(
        "/financeiro/conciliacao-caixa/acao",
        data={
            "movimentacao_ids": ["1"],
            "acao": "conciliar",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
