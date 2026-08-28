from pathlib import Path

from flask import Flask, session

from app_modules.integracoes import criar_integracoes_blueprint


ROOT = Path(__file__).resolve().parents[1]


def _app_teste():
    app = Flask(__name__, template_folder=str(ROOT / "templates"))
    app.secret_key = "teste-integracoes-storage"

    @app.get("/")
    def inicio():
        return "inicio"

    services = {
        "login_required": lambda func: func,
        "obter_conexao": lambda: None,
        "usuario_eh_super_admin_global": lambda: bool(session.get("is_super_admin")),
    }
    app.register_blueprint(criar_integracoes_blueprint(services))
    return app


def test_super_admin_acessa_painel_armazenamento():
    app = _app_teste()
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["is_super_admin"] = True
        sess["perfil_de_acesso"] = "Administrador"

    resposta = client.get("/administracao/integracoes/armazenamento")
    assert resposta.status_code == 200


def test_suporte_acessa_painel_armazenamento():
    app = _app_teste()
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["is_super_admin"] = False
        sess["perfil_de_acesso"] = "Suporte"

    resposta = client.get("/administracao/integracoes/armazenamento")
    assert resposta.status_code == 200


def test_administrador_empresa_nao_acessa_painel_tecnico_armazenamento():
    app = _app_teste()
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["is_super_admin"] = False
        sess["perfil_de_acesso"] = "Administrador"

    resposta = client.get("/administracao/integracoes/armazenamento", follow_redirects=False)
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")
