"""
Teste rápido de upload no Google Drive.

Uso:
    python scripts/testar_google_drive_upload.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

from google_drive_storage import upload_bytes_google_drive

empresa_id = int(os.environ.get("TESTE_GOOGLE_DRIVE_EMPRESA_ID", "1"))
empresa_nome = os.environ.get("TESTE_GOOGLE_DRIVE_EMPRESA_NOME", "Empresa_Teste")
motorista_id = int(os.environ.get("TESTE_GOOGLE_DRIVE_MOTORISTA_ID", "1"))
motorista_nome = os.environ.get("TESTE_GOOGLE_DRIVE_MOTORISTA_NOME", "Motorista_Teste")

conteudo = (
    "Teste de upload SGR Web\n"
    f"Gerado em: {datetime.now().isoformat()}\n"
).encode("utf-8")

info = upload_bytes_google_drive(
    conteudo=conteudo,
    empresa_id=empresa_id,
    empresa_nome=empresa_nome,
    categoria="Testes",
    origem="TESTE_GOOGLE_DRIVE",
    origem_id=None,
    motorista_id=motorista_id,
    motorista_nome=motorista_nome,
    nome_original="teste_upload_sgr.txt",
    mime_type="text/plain",
    extensao=".txt",
)

print("Upload realizado com sucesso.")
print("File ID:", info.get("drive_file_id"))
print("Pasta ID:", info.get("drive_folder_id"))
print("Link:", info.get("drive_view_url"))
