from decimal import Decimal


def autenticar(client, empresa_id=10, perfil="Financeiro", super_admin=0):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = empresa_id
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = super_admin


def dados_estorno(destino="reabrir"):
    return {
        "motivo_estorno": "Baixa registrada incorretamente",
        "data_estorno": "2026-08-16",
        "destino_estorno": destino,
        "observacao_estorno": "Estorno de teste",
    }


def parametros_estorno_liberado():
    return {
        "documentos.permitir_reaproveitar_pos_estorno": {"valor": "1"},
    }


def preparar_servicos_basicos(app, monkeypatch):
    services = app.extensions["financeiro_services"]
    monkeypatch.setitem(
        services,
        "carregar_parametros_financeiros_empresa",
        lambda empresa_id, cur=None: parametros_estorno_liberado(),
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


def test_estorno_exige_autenticacao(client):
    resposta = client.post(
        "/financeiro/titulos/8/estornar",
        data=dados_estorno(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_estorno_registrado_no_blueprint(app):
    regras = {
        regra.endpoint: (regra.rule, regra.methods)
        for regra in app.url_map.iter_rules()
    }

    rota, metodos = regras["financeiro.estornar_baixa_titulo_financeiro"]

    assert rota == "/financeiro/titulos/<int:id>/estornar"
    assert "POST" in metodos
    assert "estornar_baixa_titulo_financeiro" not in {
        endpoint for endpoint in regras if "." not in endpoint
    }


def test_estorno_rejeita_motivo_curto(client):
    autenticar(client)
    dados = dados_estorno()
    dados["motivo_estorno"] = "abc"

    resposta = client.post(
        "/financeiro/titulos/8/estornar",
        data=dados,
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_estorno_rejeita_data_invalida(client):
    autenticar(client)
    dados = dados_estorno()
    dados["data_estorno"] = "16/08/2026"

    resposta = client.post(
        "/financeiro/titulos/8/estornar",
        data=dados,
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_estorno_rejeita_destino_invalido(client):
    autenticar(client)
    dados = dados_estorno()
    dados["destino_estorno"] = "outro"

    resposta = client.post(
        "/financeiro/titulos/8/estornar",
        data=dados,
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_estorno_banco_indisponivel(client, app, monkeypatch):
    services = preparar_servicos_basicos(app, monkeypatch)
    monkeypatch.setitem(services, "obter_conexao", lambda: None)
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/estornar",
        data=dados_estorno(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_estorno_titulo_nao_encontrado(client, app, monkeypatch):
    services = preparar_servicos_basicos(app, monkeypatch)

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
        "/financeiro/titulos/999/estornar",
        data=dados_estorno(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_estorno_bloqueia_titulo_aberto(client, app, monkeypatch):
    services = preparar_servicos_basicos(app, monkeypatch)

    class Cursor:
        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return {
                "id": 8,
                "empresa_id": 10,
                "tipo_titulo": "PAGAR",
                "origem": "MANUAL",
                "origem_id": None,
                "pessoa_id": 5,
                "numero_documento": "DOC-8",
                "descricao": "Teste",
                "historico": "",
                "valor_liquido": Decimal("100.00"),
                "status_titulo": "Aberto",
                "data_baixa": None,
                "valor_baixado": None,
            }

    class Conexao:
        def cursor(self, dictionary=False):
            return Cursor()

        def rollback(self):
            pass

    monkeypatch.setitem(services, "obter_conexao", lambda: Conexao())
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/estornar",
        data=dados_estorno(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_estorno_reabrir_cria_movimento_inverso_e_reabre_titulo(
    client, app, monkeypatch
):
    services = preparar_servicos_basicos(app, monkeypatch)
    execucoes = []
    auditoria = {}

    titulo = {
        "id": 8,
        "empresa_id": 10,
        "tipo_titulo": "PAGAR",
        "origem": "MANUAL",
        "origem_id": None,
        "pessoa_id": 5,
        "numero_documento": "DOC-8",
        "descricao": "Despesa teste",
        "historico": "",
        "valor_liquido": Decimal("100.00"),
        "status_titulo": "Pago",
        "data_baixa": "2026-08-16",
        "valor_baixado": Decimal("100.00"),
    }

    class Cursor:
        def execute(self, query, params=None):
            execucoes.append((query, tuple(params or ())))

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
        "buscar_movimentacoes_baixa_nao_estornadas",
        lambda cur, titulo_id, empresa_id: [{
            "id": 50,
            "conta_caixa_id": 3,
            "tipo_movimentacao": "SAIDA",
            "valor_movimentacao": Decimal("100.00"),
            "forma_pagamento": "PIX",
        }],
    )
    monkeypatch.setitem(
        services,
        "registrar_auditoria_financeira",
        lambda cur, **kwargs: auditoria.update(kwargs),
    )
    monkeypatch.setitem(
        services,
        "converter_decimal",
        lambda valor: Decimal(str(valor or 0)),
    )

    autenticar(client)
    resposta = client.post(
        "/financeiro/titulos/8/estornar",
        data=dados_estorno("reabrir"),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]
    assert con.commits == 1
    assert con.rollbacks == 0

    insert_estorno = next(
        item for item in execucoes
        if "INSERT INTO movimentacoes_caixa" in item[0]
    )
    assert "ENTRADA" in insert_estorno[1]

    update_titulo = next(
        item for item in execucoes
        if "UPDATE titulos_financeiros" in item[0]
    )
    assert "Aberto" in update_titulo[1]

    assert auditoria["acao"] == "ESTORNO_BAIXA_TITULO"
    assert auditoria["status_anterior"] == "Pago"
    assert auditoria["status_novo"] == "Aberto"


def test_estorno_encerrar_define_status_estornado(client, app, monkeypatch):
    services = preparar_servicos_basicos(app, monkeypatch)
    execucoes = []

    titulo = {
        "id": 8,
        "empresa_id": 10,
        "tipo_titulo": "RECEBER",
        "origem": "MANUAL",
        "origem_id": None,
        "pessoa_id": 5,
        "numero_documento": "REC-8",
        "descricao": "Receita teste",
        "historico": "",
        "valor_liquido": Decimal("200.00"),
        "status_titulo": "Recebido",
        "data_baixa": "2026-08-16",
        "valor_baixado": Decimal("200.00"),
    }

    class Cursor:
        def execute(self, query, params=None):
            execucoes.append((query, tuple(params or ())))

        def fetchone(self):
            return titulo

    class Conexao:
        def __init__(self):
            self.commits = 0

        def cursor(self, dictionary=False):
            return Cursor()

        def commit(self):
            self.commits += 1

        def rollback(self):
            pass

    con = Conexao()

    monkeypatch.setitem(services, "obter_conexao", lambda: con)
    monkeypatch.setitem(
        services,
        "buscar_movimentacoes_baixa_nao_estornadas",
        lambda cur, titulo_id, empresa_id: [{
            "id": 60,
            "conta_caixa_id": 3,
            "tipo_movimentacao": "ENTRADA",
            "valor_movimentacao": Decimal("200.00"),
            "forma_pagamento": "PIX",
        }],
    )
    monkeypatch.setitem(
        services,
        "registrar_auditoria_financeira",
        lambda cur, **kwargs: None,
    )
    monkeypatch.setitem(
        services,
        "converter_decimal",
        lambda valor: Decimal(str(valor or 0)),
    )

    autenticar(client)
    resposta = client.post(
        "/financeiro/titulos/8/estornar",
        data=dados_estorno("encerrar"),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert con.commits == 1

    update_titulo = next(
        item for item in execucoes
        if "UPDATE titulos_financeiros" in item[0]
    )
    assert "Estornado" in update_titulo[1]


def test_estorno_motorista_reabrir_sincroniza_imediatamente(
    client, app, monkeypatch
):
    services = preparar_servicos_basicos(app, monkeypatch)
    chamadas = []
    titulo = {
        "id": 8, "empresa_id": 10, "tipo_titulo": "PAGAR",
        "origem": "NF_MOTORISTA", "origem_id": 99, "pessoa_id": 5,
        "numero_documento": "NF-99", "descricao": "Pagamento motorista",
        "historico": "", "valor_liquido": Decimal("300.00"),
        "status_titulo": "Pago", "data_baixa": "2026-08-16",
        "valor_baixado": Decimal("300.00"),
    }

    class Cursor:
        def execute(self, query, params=None):
            pass
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
        services, "buscar_movimentacoes_baixa_nao_estornadas",
        lambda cur, titulo_id, empresa_id: [{
            "id": 70, "conta_caixa_id": 3, "tipo_movimentacao": "SAIDA",
            "valor_movimentacao": Decimal("300.00"), "forma_pagamento": "PIX",
        }],
    )
    monkeypatch.setitem(
        services, "aplicar_estorno_em_documento_motorista_e_rotas",
        lambda cur, **kwargs: chamadas.append(kwargs),
    )
    monkeypatch.setitem(
        services, "registrar_auditoria_financeira", lambda cur, **kwargs: None,
    )
    monkeypatch.setitem(
        services, "converter_decimal", lambda valor: Decimal(str(valor or 0)),
    )

    autenticar(client)
    resposta = client.post(
        "/financeiro/titulos/8/estornar",
        data=dados_estorno("reabrir"),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert len(chamadas) == 1
    assert chamadas[0]["destino"] == "reabrir"
    assert chamadas[0]["tratativa_pos_estorno"] == "manter_bloqueadas"


def test_estorno_motorista_encerrar_deixa_tratativa_pendente(
    client, app, monkeypatch
):
    services = preparar_servicos_basicos(app, monkeypatch)
    chamadas = []
    execucoes = []
    auditoria = {}
    titulo = {
        "id": 8, "empresa_id": 10, "tipo_titulo": "PAGAR",
        "origem": "NF_MOTORISTA", "origem_id": 99, "pessoa_id": 5,
        "numero_documento": "NF-99", "descricao": "Pagamento motorista",
        "historico": "", "valor_liquido": Decimal("300.00"),
        "status_titulo": "Pago", "data_baixa": "2026-08-16",
        "valor_baixado": Decimal("300.00"),
    }

    class Cursor:
        def execute(self, query, params=None):
            execucoes.append((query, tuple(params or ())))
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
        services, "buscar_movimentacoes_baixa_nao_estornadas",
        lambda cur, titulo_id, empresa_id: [{
            "id": 70, "conta_caixa_id": 3, "tipo_movimentacao": "SAIDA",
            "valor_movimentacao": Decimal("300.00"), "forma_pagamento": "PIX",
        }],
    )
    monkeypatch.setitem(
        services, "aplicar_estorno_em_documento_motorista_e_rotas",
        lambda cur, **kwargs: chamadas.append(kwargs),
    )
    monkeypatch.setitem(
        services, "registrar_auditoria_financeira",
        lambda cur, **kwargs: auditoria.update(kwargs),
    )
    monkeypatch.setitem(
        services, "converter_decimal", lambda valor: Decimal(str(valor or 0)),
    )

    autenticar(client)
    resposta = client.post(
        "/financeiro/titulos/8/estornar",
        data=dados_estorno("encerrar"),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert len(chamadas) == 1
    assert chamadas[0]["destino"] == "encerrar"
    assert chamadas[0]["tratativa_pos_estorno"] == "manter_bloqueadas"

    update_titulo = next(
        item for item in execucoes if "UPDATE titulos_financeiros" in item[0]
    )
    assert "tratativa_pos_estorno_aplicada = 0" in update_titulo[0]
    assert "tipo_tratativa_pos_estorno = NULL" in update_titulo[0]
    assert auditoria["dados_depois"]["tratativa_pos_estorno"] == "pendente"


def test_estorno_faz_rollback_em_erro(client, app, monkeypatch):
    services = preparar_servicos_basicos(app, monkeypatch)

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
        "/financeiro/titulos/8/estornar",
        data=dados_estorno(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]
    assert con.rollbacks == 1


def test_template_estorno_usa_endpoint_do_blueprint(app):
    fonte, _, _ = app.jinja_loader.get_source(
        app.jinja_env,
        "financeiro_titulo_detalhes.html",
    )

    assert "url_for('financeiro.estornar_baixa_titulo_financeiro'" in fonte
    assert "url_for('estornar_baixa_titulo_financeiro'" not in fonte
    assert 'name="tratativa_pos_estorno"' not in fonte
