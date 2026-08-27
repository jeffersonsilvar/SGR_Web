import importlib
import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# IMPORTANTE: estas variáveis precisam ser definidas durante a importação do
# conftest, antes da fase de coleta dos módulos de teste. Alguns módulos do SGR
# importam infraestrutura de storage no topo do arquivo e essa infraestrutura
# pode carregar o .env da aplicação. Se o ambiente de teste fosse configurado
# apenas dentro da fixture app_module, a coleta já teria ocorrido e os testes
# poderiam acabar apontando para configurações reais da máquina do desenvolvedor.
os.environ["SECRET_KEY"] = "chave-exclusiva-para-testes"
os.environ["MYSQL_HOST"] = "localhost"
os.environ["MYSQL_PORT"] = "3306"
os.environ["MYSQL_USER"] = "usuario_teste"
os.environ["MYSQL_PASSWORD"] = "senha_teste"
os.environ["MYSQL_DATABASE"] = "sgr_web_teste"
os.environ["GOOGLE_DRIVE_ENABLED"] = "false"
os.environ["STORAGE_PROVIDER"] = "GOOGLE_DRIVE"


@pytest.fixture(scope="session")
def app_module():
    """
    Importa a aplicação com uma configuração segura de testes.

    O SGR Web ainda cria a instância Flask diretamente em app.py.
    Por isso, o ambiente mínimo de testes é definido antes da coleta e
    reafirmado aqui antes do import/reload da aplicação.
    """
    os.environ["SECRET_KEY"] = "chave-exclusiva-para-testes"
    os.environ["MYSQL_HOST"] = "localhost"
    os.environ["MYSQL_PORT"] = "3306"
    os.environ["MYSQL_USER"] = "usuario_teste"
    os.environ["MYSQL_PASSWORD"] = "senha_teste"
    os.environ["MYSQL_DATABASE"] = "sgr_web_teste"
    os.environ["GOOGLE_DRIVE_ENABLED"] = "false"
    os.environ["STORAGE_PROVIDER"] = "GOOGLE_DRIVE"

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
