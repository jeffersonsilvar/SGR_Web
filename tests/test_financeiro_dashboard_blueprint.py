def autenticar(client, empresa_id=10, perfil="Financeiro"):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = empresa_id
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = 1


def test_dashboard_financeiro_exige_autenticacao(client):
    resposta = client.get(
        "/financeiro/dashboard",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_endpoint_dashboard_financeiro_registrado(app):
    regras = {
        regra.endpoint: regra.rule
        for regra in app.url_map.iter_rules()
    }

    assert (
        regras["financeiro.financeiro_dashboard"]
        == "/financeiro/dashboard"
    )


def test_dashboard_sem_empresa_redireciona_logout(client):
    autenticar(client, empresa_id=None)

    resposta = client.get(
        "/financeiro/dashboard",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/logout" in resposta.headers["Location"]


def test_dashboard_banco_indisponivel(
    client,
    app,
    monkeypatch,
):
    services = app.extensions["financeiro_services"]
    monkeypatch.setitem(services, "obter_conexao", lambda: None)
    autenticar(client)

    resposta = client.get(
        "/financeiro/dashboard",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos" in resposta.headers["Location"]


def test_template_dashboard_financeiro_compila(app):
    template = app.jinja_env.get_template(
        "financeiro_dashboard.html"
    )
    assert template is not None
