def test_aplicacao_foi_criada(app):
    assert app is not None
    assert app.testing is True


def test_rota_login_responde_com_sucesso(client):
    resposta = client.get("/login")

    assert resposta.status_code == 200
    assert b"SGR" in resposta.data


def test_raiz_redireciona_usuario_nao_autenticado(client):
    resposta = client.get("/", follow_redirects=False)

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_logout_limpa_sessao_e_redireciona(client):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 123
        sessao["usuario_nome"] = "Usuário de teste"

    resposta = client.get("/logout", follow_redirects=False)

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

    with client.session_transaction() as sessao:
        assert "usuario_id" not in sessao
