def autenticar(client, empresa_id=10, perfil="Financeiro", super_admin=0):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = empresa_id
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = super_admin


def test_configuracoes_exige_autenticacao(client):
    resposta = client.get(
        "/financeiro/configuracoes",
        follow_redirects=False,
    )
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_configuracoes_endpoint_no_blueprint(app):
    regras = {
        regra.endpoint: regra.rule
        for regra in app.url_map.iter_rules()
    }
    assert (
        regras["financeiro.financeiro_configuracoes"]
        == "/financeiro/configuracoes"
    )
    assert "financeiro_configuracoes" not in {
        endpoint for endpoint in regras if "." not in endpoint
    }


def test_parametros_essenciais_sem_chaves_obsoletas(app_module):
    defs = app_module.PARAMETROS_FINANCEIROS_PADRAO
    esperadas = {
        "baixa.exigir_comprovante",
        "baixa.permitir_data_retroativa",
        "baixa.limite_dias_retroativo",
        "caixa.permitir_saldo_negativo",
        "caixa.conta_padrao_id",
        "caixa.forma_pagamento_padrao",
        "documentos.permitir_sem_nf_pf",
        "documentos.permitir_reaproveitar_pos_estorno",
        "titulos.modo_geracao_documento",
        "titulos.dias_padrao_vencimento_motorista",
    }
    assert set(defs) == esperadas


def test_template_configuracao_mostra_modos(app):
    fonte, _, _ = app.jinja_loader.get_source(
        app.jinja_env,
        "financeiro_configuracoes.html",
    )
    assert "titulos.modo_geracao_documento" in fonte
    assert "AUTOMATICO" in fonte
    assert "ASSISTIDO" in fonte
    assert "estorno.permitir_estorno_baixa" not in fonte
    assert "baixa.permitir_pagamento_parcial" not in fonte


def test_template_nf_respeita_modo_de_geracao(app):
    fonte, _, _ = app.jinja_loader.get_source(
        app.jinja_env,
        "detalhes_nf_motorista.html",
    )
    assert "modo_geracao_titulo == 'ASSISTIDO'" in fonte
    assert "titulos.gerar_automatico_documento_aprovado" not in fonte
    assert "cfg_estorno_permitido" not in fonte


def test_template_titulo_estorno_sem_switch_empresarial(app):
    fonte, _, _ = app.jinja_loader.get_source(
        app.jinja_env,
        "financeiro_titulo_detalhes.html",
    )
    assert "estorno.permitir_estorno_baixa" not in fonte
    assert "estorno.permitir_reabrir_titulo" not in fonte
    assert "estorno.permitir_encerrar_estornado" not in fonte
    assert "estorno.permitir_tratativa_pos_estorno" not in fonte


def test_configuracoes_get_renderiza(client, app, monkeypatch):
    services = app.extensions["financeiro_services"]
    autenticar(client)

    class Cursor:
        def __init__(self):
            self.last = ""

        def execute(self, query, params=None):
            self.last = query

        def fetchone(self):
            if "FROM empresas" in self.last:
                return {
                    "id": 10,
                    "nome_fantasia": "Teste",
                    "razao_social": "Teste LTDA",
                }
            return None

        def fetchall(self):
            return []

    class Conexao:
        def cursor(self, dictionary=False):
            return Cursor()

        def rollback(self):
            pass

    monkeypatch.setitem(
        services,
        "obter_conexao",
        lambda: Conexao(),
    )
    monkeypatch.setitem(
        services,
        "usuario_eh_super_admin_global",
        lambda: False,
    )
    monkeypatch.setitem(
        services,
        "carregar_parametros_financeiros_empresa",
        lambda empresa_id, cur=None: {},
    )
    monkeypatch.setitem(
        services,
        "carregar_contas_caixa_financeiro",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setitem(
        services,
        "fechar_cursor_conexao",
        lambda *args: None,
    )

    resposta = client.get("/financeiro/configuracoes")
    assert resposta.status_code == 200


def test_configuracoes_post_normaliza_e_commita(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]
    autenticar(client)
    salvos = {}
    auditoria = {}

    class Cursor:
        def __init__(self):
            self.last = ""

        def execute(self, query, params=None):
            self.last = query

        def fetchone(self):
            if "FROM empresas" in self.last:
                return {
                    "id": 10,
                    "nome_fantasia": "Teste",
                    "razao_social": "Teste LTDA",
                }
            if "FROM contas_caixa" in self.last:
                return {"id": 3}
            return None

        def fetchall(self):
            return []

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

    monkeypatch.setitem(
        services,
        "obter_conexao",
        lambda: con,
    )
    monkeypatch.setitem(
        services,
        "usuario_eh_super_admin_global",
        lambda: False,
    )
    monkeypatch.setitem(
        services,
        "carregar_parametros_financeiros_empresa",
        lambda empresa_id, cur=None: {},
    )
    monkeypatch.setitem(
        services,
        "salvar_parametro_empresa",
        lambda cur, empresa_id, chave, valor, usuario_id=None:
            salvos.__setitem__(chave, valor),
    )
    monkeypatch.setitem(
        services,
        "registrar_auditoria_financeira",
        lambda cur, **kwargs: auditoria.update(kwargs),
    )
    monkeypatch.setitem(
        services,
        "fechar_cursor_conexao",
        lambda *args: None,
    )

    resposta = client.post(
        "/financeiro/configuracoes",
        data={
            "baixa.exigir_comprovante": "1",
            "baixa.permitir_data_retroativa": "1",
            "baixa.limite_dias_retroativo": "99999",
            "caixa.permitir_saldo_negativo": "1",
            "caixa.conta_padrao_id": "3",
            "caixa.forma_pagamento_padrao": "PIX",
            "documentos.permitir_sem_nf_pf": "1",
            "documentos.permitir_reaproveitar_pos_estorno": "1",
            "titulos.modo_geracao_documento": "AUTOMATICO",
            "titulos.dias_padrao_vencimento_motorista": "8",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert con.commits == 1
    assert salvos["baixa.limite_dias_retroativo"] == "3650"
    assert salvos["titulos.modo_geracao_documento"] == "AUTOMATICO"
    assert salvos["caixa.conta_padrao_id"] == "3"
    assert (
        auditoria["acao"]
        == "CONFIGURACAO_FINANCEIRA_ATUALIZADA"
    )
