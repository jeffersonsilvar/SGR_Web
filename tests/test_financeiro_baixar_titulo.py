from decimal import Decimal


def autenticar(client, empresa_id=10, perfil="Financeiro", super_admin=0):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = empresa_id
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = super_admin


def dados_baixa():
    return {
        "conta_caixa_id": "3",
        "data_pagamento": "2026-08-11",
        "forma_pagamento": "PIX",
        "valor_pago": "100.00",
        "observacao_baixa": "Baixa de teste",
    }


def test_baixa_exige_autenticacao(client):
    resposta = client.post(
        "/financeiro/titulos/8/baixar",
        data=dados_baixa(),
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_baixa_registrado_no_blueprint(app):
    regras = {
        regra.endpoint: (regra.rule, regra.methods)
        for regra in app.url_map.iter_rules()
    }
    rota, metodos = regras["financeiro.baixar_titulo_financeiro"]
    assert rota == "/financeiro/titulos/<int:id>/baixar"
    assert "POST" in metodos
    assert "baixar_titulo_financeiro" not in {
        endpoint for endpoint in regras if "." not in endpoint
    }


def test_baixa_rejeita_conta_invalida(client):
    autenticar(client)
    dados = dados_baixa()
    dados["conta_caixa_id"] = ""
    resposta = client.post(
        "/financeiro/titulos/8/baixar",
        data=dados,
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_baixa_rejeita_data_invalida(client):
    autenticar(client)
    dados = dados_baixa()
    dados["data_pagamento"] = "11/08/2026"
    resposta = client.post(
        "/financeiro/titulos/8/baixar",
        data=dados,
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_baixa_rejeita_forma_pagamento_invalida(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    monkeypatch.setitem(services, "financeiro_base_formas_pagamento", lambda: ["PIX"])
    autenticar(client)
    dados = dados_baixa()
    dados["forma_pagamento"] = "CRIPTOMOEDA"
    resposta = client.post(
        "/financeiro/titulos/8/baixar",
        data=dados,
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_baixa_banco_indisponivel(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    monkeypatch.setitem(services, "obter_conexao", lambda: None)
    monkeypatch.setitem(services, "financeiro_base_formas_pagamento", lambda: ["PIX"])
    autenticar(client)
    resposta = client.post(
        "/financeiro/titulos/8/baixar",
        data=dados_baixa(),
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_baixa_titulo_nao_encontrado(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]

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
    monkeypatch.setitem(services, "fechar_cursor_conexao", lambda cur, con: None)
    monkeypatch.setitem(services, "financeiro_base_formas_pagamento", lambda: ["PIX"])
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/999/baixar",
        data=dados_baixa(),
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_baixa_bloqueia_titulo_ja_pago(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]

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
                "status_titulo": "Pago",
            }

    class Conexao:
        def cursor(self, dictionary=False):
            return Cursor()
        def rollback(self):
            pass

    monkeypatch.setitem(services, "obter_conexao", lambda: Conexao())
    monkeypatch.setitem(services, "fechar_cursor_conexao", lambda cur, con: None)
    monkeypatch.setitem(services, "financeiro_base_formas_pagamento", lambda: ["PIX"])
    monkeypatch.setitem(
        services,
        "carregar_parametros_financeiros_empresa",
        lambda empresa_id, cur=None: {
            "baixa.exigir_comprovante": {"valor": "0"},
            "baixa.permitir_pagamento_parcial": {"valor": "0"},
            "baixa.permitir_valor_diferente": {"valor": "0"},
            "caixa.permitir_saldo_negativo": {"valor": "0"},
            "baixa.permitir_data_retroativa": {"valor": "1"},
        },
    )
    monkeypatch.setitem(services, "parametro_bool", lambda valor: str(valor) == "1")
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/baixar",
        data=dados_baixa(),
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]


def test_baixa_receber_insere_movimentacao_atualiza_audita_e_commita(
    client, app, monkeypatch
):
    services = app.extensions["financeiro_services"]
    execucoes = []
    auditoria = {}

    class Cursor:
        def __init__(self):
            self.fetchone_calls = 0

        def execute(self, query, params=None):
            execucoes.append((query, tuple(params or ())))

        def fetchone(self):
            self.fetchone_calls += 1
            if self.fetchone_calls == 1:
                return {
                    "id": 8,
                    "empresa_id": 10,
                    "tipo_titulo": "RECEBER",
                    "origem": "MANUAL",
                    "origem_id": None,
                    "pessoa_id": 5,
                    "numero_documento": "REC-8",
                    "descricao": "Recebimento",
                    "historico": "",
                    "valor_liquido": Decimal("100.00"),
                    "status_titulo": "Aberto",
                }
            if self.fetchone_calls == 2:
                return {"id": 3, "nome_conta": "Banco", "status_conta": "Ativa"}
            return None

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
    monkeypatch.setitem(services, "fechar_cursor_conexao", lambda cur, con: None)
    monkeypatch.setitem(services, "financeiro_base_formas_pagamento", lambda: ["PIX"])
    monkeypatch.setitem(services, "converter_decimal", lambda valor: Decimal(str(valor or 0)))
    monkeypatch.setitem(
        services,
        "carregar_parametros_financeiros_empresa",
        lambda empresa_id, cur=None: {
            "baixa.exigir_comprovante": {"valor": "0"},
            "baixa.permitir_pagamento_parcial": {"valor": "0"},
            "baixa.permitir_valor_diferente": {"valor": "0"},
            "caixa.permitir_saldo_negativo": {"valor": "0"},
            "baixa.permitir_data_retroativa": {"valor": "1"},
        },
    )
    monkeypatch.setitem(services, "parametro_bool", lambda valor: str(valor) == "1")
    monkeypatch.setitem(
        services,
        "buscar_movimentacoes_baixa_nao_estornadas",
        lambda cur, titulo_id, empresa_id: [],
    )
    monkeypatch.setitem(
        services,
        "salvar_comprovante_baixa_titulo",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setitem(
        services,
        "registrar_auditoria_financeira",
        lambda cur, **kwargs: auditoria.update(kwargs),
    )

    autenticar(client)
    resposta = client.post(
        "/financeiro/titulos/8/baixar",
        data=dados_baixa(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]
    assert con.commits == 1
    assert con.rollbacks == 0
    assert any("INSERT INTO movimentacoes_caixa" in q for q, _ in execucoes)
    assert any("UPDATE titulos_financeiros" in q for q, _ in execucoes)
    assert auditoria["acao"] == "BAIXA_TITULO"
    assert auditoria["status_novo"] == "Recebido"


def test_baixa_rollback_em_erro(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]

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
    monkeypatch.setitem(services, "fechar_cursor_conexao", lambda cur, con: None)
    monkeypatch.setitem(services, "financeiro_base_formas_pagamento", lambda: ["PIX"])
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/8/baixar",
        data=dados_baixa(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/8" in resposta.headers["Location"]
    assert con.rollbacks == 1


def test_template_baixa_usa_endpoint_do_blueprint(app):
    fonte, _, _ = app.jinja_loader.get_source(
        app.jinja_env,
        "financeiro_titulo_detalhes.html",
    )
    assert "url_for('financeiro.baixar_titulo_financeiro'" in fonte
    assert "url_for('baixar_titulo_financeiro'" not in fonte
