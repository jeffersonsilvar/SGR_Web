def autenticar(client, empresa_id=10, perfil="Financeiro", super_admin=0):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = empresa_id
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = super_admin


def dados_tratativa(tratativa="manter_bloqueadas"):
    return {
        "tratativa_pos_estorno_manual": tratativa,
        "motivo_tratativa_pos_estorno": "Análise operacional necessária",
        "observacao_tratativa_pos_estorno": "Teste automatizado",
    }


def parametros_liberados():
    return {
        "estorno.permitir_tratativa_pos_estorno": {"valor": "1"},
        "documentos.permitir_reaproveitar_pos_estorno": {"valor": "1"},
    }


def preparar_servicos(app, monkeypatch):
    services = app.extensions["financeiro_services"]
    monkeypatch.setitem(
        services,
        "carregar_parametros_financeiros_empresa",
        lambda empresa_id, cur=None: parametros_liberados(),
    )
    monkeypatch.setitem(
        services,
        "parametro_bool",
        lambda valor: str(valor) in {"1", "true", "True"},
    )
    monkeypatch.setitem(
        services,
        "fechar_cursor_conexao",
        lambda cursor, conexao: None,
    )
    return services


def titulo_estornado(origem="NF_MOTORISTA"):
    return {
        "id": 8,
        "empresa_id": 10,
        "origem": origem,
        "origem_id": 99,
        "status_titulo": "Estornado",
        "numero_documento": "NF-99",
        "descricao": "Pagamento motorista",
        "tratativa_pos_estorno_aplicada": 0,
        "tipo_tratativa_pos_estorno": None,
        "data_tratativa_pos_estorno": None,
        "usuario_tratativa_pos_estorno_id": None,
        "motivo_tratativa_pos_estorno": None,
        "observacao_tratativa_pos_estorno": None,
        "observacao_baixa": "",
    }


def test_tratativa_exige_autenticacao(client):
    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados_tratativa(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_tratativa_registrado_no_blueprint(app):
    regras = {
        regra.endpoint: (regra.rule, regra.methods)
        for regra in app.url_map.iter_rules()
    }

    rota, metodos = regras[
        "financeiro.tratar_pos_estorno_titulo_financeiro"
    ]

    assert rota == "/financeiro/titulos/<int:id>/tratativa-pos-estorno"
    assert "POST" in metodos
    assert "tratar_pos_estorno_titulo_financeiro" not in {
        endpoint for endpoint in regras if "." not in endpoint
    }


def test_tratativa_rejeita_opcao_invalida(client):
    autenticar(client)
    dados = dados_tratativa("invalida")

    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados,
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_tratativa_rejeita_motivo_curto(client):
    autenticar(client)
    dados = dados_tratativa()
    dados["motivo_tratativa_pos_estorno"] = "abc"

    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados,
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_tratativa_banco_indisponivel(client, app, monkeypatch):
    services = preparar_servicos(app, monkeypatch)
    monkeypatch.setitem(services, "obter_conexao", lambda: None)
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados_tratativa(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_tratativa_titulo_nao_encontrado(client, app, monkeypatch):
    services = preparar_servicos(app, monkeypatch)

    class Cursor:
        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return None

    class Conexao:
        def cursor(self, dictionary=False):
            return Cursor()

        def rollback(self):
            pass

    monkeypatch.setitem(services, "obter_conexao", lambda: Conexao())
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/999/tratativa-pos-estorno",
        data=dados_tratativa(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_tratativa_exige_status_estornado(client, app, monkeypatch):
    services = preparar_servicos(app, monkeypatch)
    titulo = titulo_estornado()
    titulo["status_titulo"] = "Aberto"

    class Cursor:
        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return titulo

    class Conexao:
        def cursor(self, dictionary=False):
            return Cursor()

        def rollback(self):
            pass

    monkeypatch.setitem(services, "obter_conexao", lambda: Conexao())
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados_tratativa(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_tratativa_exige_origem_motorista(client, app, monkeypatch):
    services = preparar_servicos(app, monkeypatch)
    titulo = titulo_estornado(origem="MANUAL")

    class Cursor:
        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return titulo

    class Conexao:
        def cursor(self, dictionary=False):
            return Cursor()

        def rollback(self):
            pass

    monkeypatch.setitem(services, "obter_conexao", lambda: Conexao())
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados_tratativa(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_tratativa_bloqueia_reaplicacao(client, app, monkeypatch):
    services = preparar_servicos(app, monkeypatch)
    titulo = titulo_estornado()
    titulo["tratativa_pos_estorno_aplicada"] = 1

    class Cursor:
        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return titulo

    class Conexao:
        def cursor(self, dictionary=False):
            return Cursor()

        def rollback(self):
            pass

    monkeypatch.setitem(services, "obter_conexao", lambda: Conexao())
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados_tratativa(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_tratativa_respeita_configuracao_bloqueada(
    client, app, monkeypatch
):
    services = preparar_servicos(app, monkeypatch)
    titulo = titulo_estornado()

    class Cursor:
        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return titulo

    class Conexao:
        def cursor(self, dictionary=False):
            return Cursor()

        def rollback(self):
            pass

    monkeypatch.setitem(services, "obter_conexao", lambda: Conexao())
    monkeypatch.setitem(
        services,
        "carregar_parametros_financeiros_empresa",
        lambda empresa_id, cur=None: {
            "estorno.permitir_tratativa_pos_estorno": {"valor": "0"},
            "documentos.permitir_reaproveitar_pos_estorno": {"valor": "1"},
        },
    )
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados_tratativa(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_tratativa_reaproveitar_respeita_configuracao(
    client, app, monkeypatch
):
    services = preparar_servicos(app, monkeypatch)
    titulo = titulo_estornado()

    class Cursor:
        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return titulo

    class Conexao:
        def cursor(self, dictionary=False):
            return Cursor()

        def rollback(self):
            pass

    monkeypatch.setitem(services, "obter_conexao", lambda: Conexao())
    monkeypatch.setitem(
        services,
        "carregar_parametros_financeiros_empresa",
        lambda empresa_id, cur=None: {
            "estorno.permitir_tratativa_pos_estorno": {"valor": "1"},
            "documentos.permitir_reaproveitar_pos_estorno": {"valor": "0"},
        },
    )
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados_tratativa("reabrir_mesmo_documento"),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_tratativa_aplica_sincroniza_audita_e_commita(
    client, app, monkeypatch
):
    services = preparar_servicos(app, monkeypatch)
    titulo = titulo_estornado()
    execucoes = []
    sincronizacoes = []
    auditoria = {}

    class Cursor:
        def __init__(self):
            self.rowcount = 1

        def execute(self, query, params=None):
            execucoes.append((query, tuple(params or ())))
            self.rowcount = 1

        def fetchone(self):
            return titulo

    class Conexao:
        def __init__(self):
            self.commits = 0
            self.rollbacks = 0

        def cursor(self, dictionary=False):
            return Cursor()

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.rollbacks += 1

    con = Conexao()

    monkeypatch.setitem(services, "obter_conexao", lambda: con)
    monkeypatch.setitem(
        services,
        "aplicar_estorno_em_documento_motorista_e_rotas",
        lambda cur, **kwargs: sincronizacoes.append(kwargs),
    )
    monkeypatch.setitem(
        services,
        "registrar_auditoria_financeira",
        lambda cur, **kwargs: auditoria.update(kwargs),
    )

    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados_tratativa("exigir_nova_nf"),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]
    assert con.commits == 1
    assert con.rollbacks == 0

    assert len(sincronizacoes) == 1
    assert sincronizacoes[0]["titulo_id"] == 8
    assert sincronizacoes[0]["destino"] == "encerrar"
    assert sincronizacoes[0]["tratativa_pos_estorno"] == "exigir_nova_nf"

    assert any(
        "UPDATE titulos_financeiros" in query
        for query, _ in execucoes
    )
    assert any(
        "INSERT INTO historico_operacoes" in query
        for query, _ in execucoes
    )

    assert auditoria["acao"] == "TRATATIVA_POS_ESTORNO_APLICADA"
    assert auditoria["status_anterior"] == "Estornado"
    assert auditoria["status_novo"] == "Estornado"


def test_tratativa_faz_rollback_em_erro(client, app, monkeypatch):
    services = preparar_servicos(app, monkeypatch)

    class Cursor:
        def execute(self, query, params=None):
            raise RuntimeError("falha simulada")

        def fetchone(self):
            return None

    class Conexao:
        def __init__(self):
            self.rollbacks = 0

        def cursor(self, dictionary=False):
            return Cursor()

        def rollback(self):
            self.rollbacks += 1

    con = Conexao()

    monkeypatch.setitem(services, "obter_conexao", lambda: con)
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados_tratativa(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]
    assert con.rollbacks == 1


def test_template_tratativa_usa_endpoint_do_blueprint(app):
    fonte, _, _ = app.jinja_loader.get_source(
        app.jinja_env,
        "financeiro_titulo_detalhes.html",
    )

    assert (
        "url_for('financeiro.tratar_pos_estorno_titulo_financeiro'"
        in fonte
    )
    assert "url_for('tratar_pos_estorno_titulo_financeiro'" not in fonte


def test_tratativa_manter_bloqueadas_nao_repete_sincronizacao(
    client, app, monkeypatch
):
    services = preparar_servicos(app, monkeypatch)
    titulo = titulo_estornado()
    chamadas = []

    class Cursor:
        def __init__(self):
            self.rowcount = 1
        def execute(self, query, params=None):
            self.rowcount = 1
        def fetchone(self):
            return titulo

    class Conexao:
        def cursor(self, dictionary=False):
            return Cursor()
        def commit(self):
            pass
        def rollback(self):
            pass

    monkeypatch.setitem(services, "obter_conexao", lambda: Conexao())
    monkeypatch.setitem(
        services, "aplicar_estorno_em_documento_motorista_e_rotas",
        lambda cur, **kwargs: chamadas.append(kwargs),
    )
    monkeypatch.setitem(
        services, "registrar_auditoria_financeira", lambda cur, **kwargs: None,
    )

    autenticar(client)
    resposta = client.post(
        "/financeiro/titulos/8/tratativa-pos-estorno",
        data=dados_tratativa("manter_bloqueadas"),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert chamadas == []


def test_template_exibe_tratativa_pendente_separada(app):
    fonte, _, _ = app.jinja_loader.get_source(
        app.jinja_env,
        "financeiro_titulo_detalhes.html",
    )
    assert "Tratativa pendente." in fonte
    assert (
        "url_for('financeiro.tratar_pos_estorno_titulo_financeiro'"
        in fonte
    )
