import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configurações da aplicação carregadas por variáveis de ambiente."""

    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "A variável SECRET_KEY não foi configurada. "
            "Copie .env.example para .env e defina uma chave segura."
        )

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "4")) * 1024 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
