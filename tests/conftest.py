import importlib
import os
import sys

import pytest


@pytest.fixture(scope="session")
def app_module():
    """
    Importa a aplicação com uma configuração segura de testes.

    O SGR Web ainda cria a instância Flask diretamente em app.py.
    Por isso, as variáveis mínimas precisam existir antes do import.
    """
    os.environ.setdefault("SECRET_KEY", "chave-exclusiva-para-testes")
    os.environ.setdefault("MYSQL_HOST", "localhost")
    os.environ.setdefault("MYSQL_PORT", "3306")
    os.environ.setdefault("MYSQL_USER", "usuario_teste")
    os.environ.setdefault("MYSQL_PASSWORD", "senha_teste")
    os.environ.setdefault("MYSQL_DATABASE", "sgr_web_teste")
    os.environ.setdefault("GOOGLE_DRIVE_ENABLED", "false")

    if "app" in sys.modules:
        module = importlib.reload(sys.modules["app"])
    else:
        module = importlib.import_module("app")

    module.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="chave-exclusiva-para-testes",
    )
    return module


@pytest.fixture()
def app(app_module):
    return app_module.app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
