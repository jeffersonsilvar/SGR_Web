"""
Gera o token OAuth do Google Drive para o SGR Web.

Uso local, com o .venv ativo:
    python scripts/google_drive_oauth_setup.py

Este script lê automaticamente o arquivo .env da raiz do projeto.
Variáveis aceitas:
    GOOGLE_DRIVE_CREDENTIALS_FILE=instance/credentials_google_drive.json
    GOOGLE_DRIVE_TOKEN_FILE=instance/token_google_drive.json

Também aceita os nomes antigos, para compatibilidade:
    GOOGLE_DRIVE_OAUTH_CLIENT_SECRET_FILE=client_secret_google_drive.json
    GOOGLE_DRIVE_OAUTH_TOKEN_FILE=token_google_drive.json
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

from google_auth_oauthlib.flow import InstalledAppFlow


def resolver_caminho(valor: str) -> Path:
    caminho = Path(valor)
    if caminho.is_absolute():
        return caminho
    return ROOT / caminho


SCOPES = [
    item.strip()
    for item in os.environ.get("GOOGLE_DRIVE_SCOPES", "https://www.googleapis.com/auth/drive").split(",")
    if item.strip()
]

CLIENT_SECRET_FILE = (
    os.environ.get("GOOGLE_DRIVE_CREDENTIALS_FILE")
    or os.environ.get("GOOGLE_DRIVE_OAUTH_CLIENT_SECRET_FILE")
    or "instance/credentials_google_drive.json"
)

TOKEN_FILE = (
    os.environ.get("GOOGLE_DRIVE_TOKEN_FILE")
    or os.environ.get("GOOGLE_DRIVE_OAUTH_TOKEN_FILE")
    or "instance/token_google_drive.json"
)

client_secret_path = resolver_caminho(CLIENT_SECRET_FILE)
token_path = resolver_caminho(TOKEN_FILE)

token_path.parent.mkdir(parents=True, exist_ok=True)

if not client_secret_path.exists():
    raise SystemExit(
        "Arquivo client secret não encontrado: "
        f"{client_secret_path}\n\n"
        "Confira se o JSON baixado do Google Cloud está neste caminho, ou ajuste no .env:\n"
        "GOOGLE_DRIVE_CREDENTIALS_FILE=instance/credentials_google_drive.json"
    )

flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
creds = flow.run_local_server(port=0)
token_path.write_text(creds.to_json(), encoding="utf-8")

print("Token gerado com sucesso:", token_path)
print("Guarde esse arquivo com segurança e NÃO envie para repositórios públicos.")
