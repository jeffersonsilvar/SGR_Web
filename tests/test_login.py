def test_login_sem_usuario_e_senha_redireciona(client):
    resposta = client.post(
        "/login",
        data={"username": "", "password": ""},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_login_exibe_mensagem_para_campos_obrigatorios(client):
    resposta = client.post(
        "/login",
        data={"username": "", "password": ""},
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert "Preencha usuário e senha".encode("utf-8") in resposta.data


def test_login_trata_banco_indisponivel(client, app_module, monkeypatch):
    monkeypatch.setattr(app_module, "obter_conexao", lambda: None)

    resposta = client.post(
        "/login",
        data={"username": "usuario", "password": "senha"},
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert "Erro de conexão com o banco de dados".encode("utf-8") in resposta.data
