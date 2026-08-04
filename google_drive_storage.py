"""
Infraestrutura de armazenamento de arquivos do SGR Web no Google Drive.

Fase 1: este módulo NÃO altera os fluxos atuais de upload.
Ele apenas centraliza as funções que serão usadas nas próximas fases.
"""

import base64
import io
import json
import mimetypes
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload

ROOT_DIR = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except Exception:
    pass


def resolver_caminho_config(valor: Optional[str]) -> Optional[str]:
    if not valor:
        return None
    caminho = Path(valor)
    if caminho.is_absolute():
        return str(caminho)
    return str(ROOT_DIR / caminho)


DEFAULT_SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleDriveStorageError(Exception):
    """Erro controlado de integração com Google Drive."""


def env_bool(nome: str, padrao: bool = False) -> bool:
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return str(valor).strip().lower() in {"1", "true", "sim", "yes", "on"}


def slugify_drive(valor: Any, limite: int = 80) -> str:
    """Gera nomes seguros para pastas/arquivos, mantendo acentos fora do caminho técnico."""
    texto = str(valor or "").strip()
    texto = texto.replace("/", "-").replace("\\", "-")
    texto = re.sub(r"[^A-Za-z0-9À-ÿ._ -]+", "", texto)
    texto = re.sub(r"\s+", "_", texto)
    texto = texto.strip("._- ")
    return (texto or "sem_nome")[:limite]


def escapar_query_drive(valor: str) -> str:
    return str(valor or "").replace("'", "\\'")


def obter_scopes() -> List[str]:
    raw = os.environ.get("GOOGLE_DRIVE_SCOPES")
    if not raw:
        return DEFAULT_SCOPES
    return [item.strip() for item in raw.split(",") if item.strip()]


def _json_from_env_base64(nome_env: str) -> Optional[Dict[str, Any]]:
    raw = os.environ.get(nome_env)
    if not raw:
        return None
    try:
        decoded = base64.b64decode(raw).decode("utf-8")
        return json.loads(decoded)
    except Exception as exc:
        raise GoogleDriveStorageError(f"Variável {nome_env} não contém JSON base64 válido: {exc}") from exc


def carregar_credenciais_google_drive():
    """
    Carrega credenciais por OAuth ou Service Account.

    Variáveis suportadas:
    - GOOGLE_DRIVE_AUTH_MODE=oauth|service_account
    - OAuth:
        GOOGLE_DRIVE_OAUTH_TOKEN_FILE=token_google_drive.json
        ou GOOGLE_DRIVE_OAUTH_TOKEN_JSON_BASE64=<token json em base64>
    - Service account:
        GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=service_account.json
        ou GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON_BASE64=<json em base64>
    """
    modo = os.environ.get("GOOGLE_DRIVE_AUTH_MODE", "oauth").strip().lower()
    scopes = obter_scopes()

    if modo == "service_account":
        info = _json_from_env_base64("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON_BASE64")
        if info:
            return service_account.Credentials.from_service_account_info(info, scopes=scopes)

        arquivo = (
            os.environ.get("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE")
            or os.environ.get("GOOGLE_DRIVE_CREDENTIALS_FILE")
        )
        arquivo = resolver_caminho_config(arquivo)
        if not arquivo:
            raise GoogleDriveStorageError(
                "GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE ou GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON_BASE64 não configurado."
            )
        if not os.path.exists(arquivo):
            raise GoogleDriveStorageError(f"Arquivo da service account não encontrado: {arquivo}")
        return service_account.Credentials.from_service_account_file(arquivo, scopes=scopes)

    if modo != "oauth":
        raise GoogleDriveStorageError("GOOGLE_DRIVE_AUTH_MODE deve ser 'oauth' ou 'service_account'.")

    token_info = _json_from_env_base64("GOOGLE_DRIVE_OAUTH_TOKEN_JSON_BASE64")
    token_file = (
        os.environ.get("GOOGLE_DRIVE_TOKEN_FILE")
        or os.environ.get("GOOGLE_DRIVE_OAUTH_TOKEN_FILE")
        or "instance/token_google_drive.json"
    )
    token_file = resolver_caminho_config(token_file)

    if token_info:
        creds = Credentials.from_authorized_user_info(token_info, scopes)
    elif os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    else:
        raise GoogleDriveStorageError(
            "Token OAuth não encontrado. Rode scripts/google_drive_oauth_setup.py no ambiente local."
        )

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Se veio de arquivo, atualiza o token em disco.
        if not token_info:
            try:
                Path(token_file).write_text(creds.to_json(), encoding="utf-8")
            except Exception:
                pass

    if not creds or not creds.valid:
        raise GoogleDriveStorageError("Credencial OAuth inválida ou expirada sem refresh token.")

    return creds


def obter_servico_drive():
    creds = carregar_credenciais_google_drive()
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def buscar_pasta(service, nome: str, parent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    nome_q = escapar_query_drive(nome)
    query = (
        "mimeType = 'application/vnd.google-apps.folder' "
        f"and name = '{nome_q}' and trashed = false"
    )
    if parent_id:
        query += f" and '{parent_id}' in parents"

    resp = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name, webViewLink)",
        pageSize=10,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()
    arquivos = resp.get("files", [])
    return arquivos[0] if arquivos else None


def criar_pasta(service, nome: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
    body = {
        "name": nome,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        body["parents"] = [parent_id]

    return service.files().create(
        body=body,
        fields="id, name, webViewLink",
        supportsAllDrives=True,
    ).execute()


def obter_ou_criar_pasta(service, nome: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
    nome = slugify_drive(nome, limite=100)
    existente = buscar_pasta(service, nome, parent_id)
    if existente:
        return existente
    return criar_pasta(service, nome, parent_id)


def construir_hierarquia_pastas(
    service,
    empresa_id: int,
    empresa_nome: str,
    categoria: str,
    data_referencia: Optional[datetime] = None,
    motorista_id: Optional[int] = None,
    motorista_nome: Optional[str] = None,
    subcategoria: Optional[str] = None,
    pasta_registro: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Correção Bloco 8.2.6 — Árvore geral de arquivos no Google Drive.

    Padrão novo:
    SGR_Web / Empresa_<id>_<nome> / Arquivos / Ano / Mes / Categoria / Subcategoria / Registro

    Regras:
    - O Drive organiza pela natureza do arquivo.
    - A origem real continua registrada no banco em arquivos_sistema.
    - Para comprovantes financeiros, a chamada deve informar:
        subcategoria = Contas_a_Pagar ou Contas_a_Receber
        pasta_registro = titulo_<id>_<pessoa>
    - Para arquivos operacionais sem pasta_registro, mantém agrupamento por prestador
      quando motorista_id for informado.
    """
    data_referencia = data_referencia or datetime.now()

    service = service or obter_servico_drive()
    root_id = os.environ.get("GOOGLE_DRIVE_ROOT_FOLDER_ID")
    root_name = os.environ.get("GOOGLE_DRIVE_ROOT_FOLDER_NAME", "SGR_Web")

    if root_id:
        parent = {"id": root_id, "name": root_name}
    else:
        parent = obter_ou_criar_pasta(service, root_name)

    empresa_pasta_nome = f"Empresa_{empresa_id}_{slugify_drive(empresa_nome or 'empresa')}"
    empresa_pasta = obter_ou_criar_pasta(service, empresa_pasta_nome, parent["id"])

    arquivos_pasta = obter_ou_criar_pasta(service, "Arquivos", empresa_pasta["id"])
    ano_pasta = obter_ou_criar_pasta(service, str(data_referencia.year), arquivos_pasta["id"])
    mes_pasta = obter_ou_criar_pasta(service, f"{data_referencia.month:02d}", ano_pasta["id"])
    categoria_pasta = obter_ou_criar_pasta(service, slugify_drive(categoria), mes_pasta["id"])

    pasta_final = categoria_pasta
    subcategoria_pasta = None
    registro_pasta = None

    if subcategoria:
        subcategoria_pasta = obter_ou_criar_pasta(service, slugify_drive(subcategoria), pasta_final["id"])
        pasta_final = subcategoria_pasta

    if pasta_registro:
        registro_pasta = obter_ou_criar_pasta(service, slugify_drive(pasta_registro), pasta_final["id"])
        pasta_final = registro_pasta
    elif motorista_id:
        # Compatibilidade: se algum upload antigo não informar pasta_registro,
        # ainda assim fica organizado por prestador dentro da categoria correta.
        nome_prestador_pasta = f"prestador_{motorista_id}_{slugify_drive(motorista_nome or 'prestador')}"
        registro_pasta = obter_ou_criar_pasta(service, nome_prestador_pasta, pasta_final["id"])
        pasta_final = registro_pasta

    return {
        "root": parent,
        "empresa": empresa_pasta,
        "arquivos": arquivos_pasta,
        "ano": ano_pasta,
        "mes": mes_pasta,
        "categoria": categoria_pasta,
        "subcategoria": subcategoria_pasta,
        "registro": registro_pasta,
        "final": pasta_final,
    }


def gerar_nome_armazenado(
    empresa_id: int,
    origem: str,
    origem_id: Optional[int] = None,
    motorista_id: Optional[int] = None,
    nome_original: Optional[str] = None,
    extensao: Optional[str] = None,
) -> str:
    agora = datetime.now().strftime("%Y%m%d_%H%M%S")
    origem_slug = slugify_drive(origem, limite=40).lower()
    partes = [f"empresa_{empresa_id}"]
    if motorista_id:
        partes.append(f"motorista_{motorista_id}")
    partes.append(origem_slug)
    if origem_id:
        partes.append(f"id_{origem_id}")
    partes.append(agora)

    if not extensao and nome_original:
        extensao = os.path.splitext(nome_original)[1]
    extensao = (extensao or "").lower()
    if extensao and not extensao.startswith("."):
        extensao = f".{extensao}"

    return "_".join(partes) + extensao


def upload_arquivo_path_google_drive(
    caminho_local: str,
    empresa_id: int,
    empresa_nome: str,
    categoria: str,
    origem: str,
    origem_id: Optional[int] = None,
    motorista_id: Optional[int] = None,
    motorista_nome: Optional[str] = None,
    nome_original: Optional[str] = None,
    mime_type: Optional[str] = None,
    nome_armazenado: Optional[str] = None,
    data_referencia: Optional[datetime] = None,
    subcategoria: Optional[str] = None,
    pasta_registro: Optional[str] = None,
) -> Dict[str, Any]:
    if not os.path.exists(caminho_local):
        raise GoogleDriveStorageError(f"Arquivo local não encontrado: {caminho_local}")

    service = obter_servico_drive()
    nome_original = nome_original or os.path.basename(caminho_local)
    mime_type = mime_type or mimetypes.guess_type(nome_original)[0] or "application/octet-stream"
    nome_armazenado = nome_armazenado or gerar_nome_armazenado(
        empresa_id=empresa_id,
        origem=origem,
        origem_id=origem_id,
        motorista_id=motorista_id,
        nome_original=nome_original,
    )

    pastas = construir_hierarquia_pastas(
        service=service,
        empresa_id=empresa_id,
        empresa_nome=empresa_nome,
        categoria=categoria,
        data_referencia=data_referencia,
        motorista_id=motorista_id,
        motorista_nome=motorista_nome,
        subcategoria=subcategoria,
        pasta_registro=pasta_registro,
    )

    media = MediaFileUpload(caminho_local, mimetype=mime_type, resumable=True)
    body = {
        "name": nome_armazenado,
        "parents": [pastas["final"]["id"]],
    }
    arquivo = service.files().create(
        body=body,
        media_body=media,
        fields="id, name, size, mimeType, webViewLink, webContentLink, parents",
        supportsAllDrives=True,
    ).execute()

    return normalizar_resultado_upload_drive(arquivo, pastas, nome_original, nome_armazenado, mime_type)


def upload_bytes_google_drive(
    conteudo: bytes,
    empresa_id: int,
    empresa_nome: str,
    categoria: str,
    origem: str,
    origem_id: Optional[int] = None,
    motorista_id: Optional[int] = None,
    motorista_nome: Optional[str] = None,
    nome_original: Optional[str] = None,
    mime_type: Optional[str] = None,
    extensao: Optional[str] = None,
    data_referencia: Optional[datetime] = None,
    subcategoria: Optional[str] = None,
    pasta_registro: Optional[str] = None,
) -> Dict[str, Any]:
    service = obter_servico_drive()
    nome_original = nome_original or f"arquivo{extensao or ''}"
    mime_type = mime_type or mimetypes.guess_type(nome_original)[0] or "application/octet-stream"
    nome_armazenado = gerar_nome_armazenado(
        empresa_id=empresa_id,
        origem=origem,
        origem_id=origem_id,
        motorista_id=motorista_id,
        nome_original=nome_original,
        extensao=extensao,
    )

    pastas = construir_hierarquia_pastas(
        service=service,
        empresa_id=empresa_id,
        empresa_nome=empresa_nome,
        categoria=categoria,
        data_referencia=data_referencia,
        motorista_id=motorista_id,
        motorista_nome=motorista_nome,
        subcategoria=subcategoria,
        pasta_registro=pasta_registro,
    )

    media = MediaIoBaseUpload(io.BytesIO(conteudo), mimetype=mime_type, resumable=True)
    body = {
        "name": nome_armazenado,
        "parents": [pastas["final"]["id"]],
    }
    arquivo = service.files().create(
        body=body,
        media_body=media,
        fields="id, name, size, mimeType, webViewLink, webContentLink, parents",
        supportsAllDrives=True,
    ).execute()

    return normalizar_resultado_upload_drive(arquivo, pastas, nome_original, nome_armazenado, mime_type)


def normalizar_resultado_upload_drive(
    arquivo: Dict[str, Any],
    pastas: Dict[str, Any],
    nome_original: str,
    nome_armazenado: str,
    mime_type: str,
) -> Dict[str, Any]:
    file_id = arquivo.get("id")
    view_url = arquivo.get("webViewLink") or (f"https://drive.google.com/file/d/{file_id}/view" if file_id else None)
    download_url = arquivo.get("webContentLink") or (f"https://drive.google.com/uc?id={file_id}&export=download" if file_id else None)
    return {
        "storage_provider": "GOOGLE_DRIVE",
        "drive_file_id": file_id,
        "drive_folder_id": pastas["final"].get("id"),
        "drive_view_url": view_url,
        "drive_download_url": download_url,
        "nome_original": nome_original,
        "nome_armazenado": nome_armazenado,
        "mime_type": arquivo.get("mimeType") or mime_type,
        "tamanho_bytes": int(arquivo.get("size") or 0),
        "pastas": pastas,
    }


def registrar_arquivo_sistema(
    cur,
    *,
    empresa_id: int,
    origem: str,
    origem_id: Optional[int],
    tipo_arquivo: str,
    upload_info: Dict[str, Any],
    pessoa_id: Optional[int] = None,
    motorista_id: Optional[int] = None,
    caminho_local: Optional[str] = None,
    status_arquivo: str = "ATIVO",
    criado_por_usuario_id: Optional[int] = None,
    erro_upload: Optional[str] = None,
) -> int:
    """Insere metadados do arquivo na tabela arquivos_sistema."""
    cur.execute(
        """
        INSERT INTO arquivos_sistema
            (empresa_id, pessoa_id, motorista_id, origem, origem_id, tipo_arquivo,
             nome_original, nome_armazenado, mime_type, tamanho_bytes,
             storage_provider, caminho_local, drive_file_id, drive_folder_id,
             drive_view_url, drive_download_url, status_arquivo, erro_upload,
             criado_por_usuario_id)
        VALUES
            (%s, %s, %s, %s, %s, %s,
             %s, %s, %s, %s,
             %s, %s, %s, %s,
             %s, %s, %s, %s,
             %s)
        """,
        (
            empresa_id,
            pessoa_id,
            motorista_id,
            origem,
            origem_id,
            tipo_arquivo,
            upload_info.get("nome_original"),
            upload_info.get("nome_armazenado"),
            upload_info.get("mime_type"),
            upload_info.get("tamanho_bytes") or 0,
            upload_info.get("storage_provider") or "GOOGLE_DRIVE",
            caminho_local,
            upload_info.get("drive_file_id"),
            upload_info.get("drive_folder_id"),
            upload_info.get("drive_view_url"),
            upload_info.get("drive_download_url"),
            status_arquivo,
            erro_upload,
            criado_por_usuario_id,
        ),
    )
    return int(cur.lastrowid)



def obter_metadados_arquivo_google_drive(file_id: str) -> Dict[str, Any]:
    """Obtém metadados básicos de um arquivo privado no Google Drive."""
    if not file_id:
        raise GoogleDriveStorageError("drive_file_id não informado.")

    service = obter_servico_drive()
    try:
        return service.files().get(
            fileId=file_id,
            fields="id, name, size, mimeType, webViewLink, webContentLink, parents",
            supportsAllDrives=True,
        ).execute()
    except Exception as exc:
        raise GoogleDriveStorageError(f"Erro ao obter metadados do Google Drive: {exc}") from exc


def baixar_arquivo_google_drive(file_id: str) -> bytes:
    """Baixa o conteúdo binário de um arquivo privado no Google Drive.

    Usado pela rota protegida /arquivos/visualizar/<id>.
    O arquivo permanece privado no Drive; o SGR valida permissão e entrega o conteúdo.
    """
    if not file_id:
        raise GoogleDriveStorageError("drive_file_id não informado.")

    service = obter_servico_drive()
    try:
        request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _status, done = downloader.next_chunk()

        buffer.seek(0)
        return buffer.read()
    except Exception as exc:
        raise GoogleDriveStorageError(f"Erro ao baixar arquivo do Google Drive: {exc}") from exc

def google_drive_habilitado() -> bool:
    """
    Retorna se o Google Drive está habilitado para uploads.

    Compatibilidade SGR:
    - Se GOOGLE_DRIVE_ENABLED estiver definido, respeita explicitamente o valor.
    - Se não estiver definido, tenta habilitar automaticamente quando houver credenciais
      configuradas/encontradas. Isso evita fallback local silencioso em ambientes que já
      usam Drive para XML/notas, mas não tinham a flag nova no .env.
    """
    valor_explicitado = os.environ.get("GOOGLE_DRIVE_ENABLED")
    if valor_explicitado is not None:
        return env_bool("GOOGLE_DRIVE_ENABLED", False)

    # Service account via env/base64 ou arquivo
    if os.environ.get("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON_BASE64"):
        return True
    service_file = resolver_caminho_config(
        os.environ.get("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE")
        or os.environ.get("GOOGLE_DRIVE_CREDENTIALS_FILE")
    )
    if service_file and os.path.exists(service_file):
        return True

    # OAuth via env/base64 ou token em arquivo
    if os.environ.get("GOOGLE_DRIVE_OAUTH_TOKEN_JSON_BASE64"):
        return True
    token_file = resolver_caminho_config(
        os.environ.get("GOOGLE_DRIVE_TOKEN_FILE")
        or os.environ.get("GOOGLE_DRIVE_OAUTH_TOKEN_FILE")
        or "instance/token_google_drive.json"
    )
    if token_file and os.path.exists(token_file):
        return True

    return False


def categoria_por_origem(origem: str) -> str:
    origem = str(origem or "").upper().strip()
    mapa = {
        "CHECKIN_SELFIE": "Checkins",
        "JUSTIFICATIVA_AUSENCIA": "Justificativas_Ausencia",
        "XML_MOTORISTA": "XML_Notas",
        "NF_MOTORISTA": "Notas_Fiscais",
        "COMPROVANTE_PAGAMENTO": "Comprovantes_Financeiros",
        "COMPROVANTE_FINANCEIRO": "Comprovantes_Financeiros",
        "COMPROVANTE_BAIXA_TITULO": "Comprovantes_Financeiros",
        "ANEXO_OCORRENCIA": "Ocorrencias",
        "FOTO_ENTREGA": "Fotos_Entrega",
        "ASSINATURA_ENTREGA": "Assinaturas",
    }
    return mapa.get(origem, "Outros")
