from __future__ import annotations

from datetime import datetime
import hashlib
import os
import time
from typing import Any, Dict, Optional

from google_drive_storage import (
    GoogleDriveStorageError,
    google_drive_habilitado,
    obter_servico_drive,
    registrar_arquivo_sistema,
    upload_arquivo_path_google_drive,
)


class StorageServiceError(Exception):
    """Erro controlado da camada genérica de armazenamento do SGR."""


class StorageService:
    """Camada genérica de storage.

    O restante da aplicação não deve depender diretamente de Google Drive, S3 etc.
    O provider atual é definido por STORAGE_PROVIDER e, nesta fase, apenas
    GOOGLE_DRIVE está implementado para produção.
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or os.environ.get("STORAGE_PROVIDER") or "GOOGLE_DRIVE").strip().upper()

    def _validar_provider(self) -> None:
        if self.provider != "GOOGLE_DRIVE":
            raise StorageServiceError(f"Provider de armazenamento não suportado: {self.provider}")

    @staticmethod
    def calcular_sha256(caminho_local: str) -> str:
        digest = hashlib.sha256()
        with open(caminho_local, "rb") as arquivo:
            for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
                digest.update(bloco)
        return digest.hexdigest()

    def health_check(self) -> Dict[str, Any]:
        inicio = time.perf_counter()
        retorno = {
            "provider": self.provider,
            "status": "NAO_CONFIGURADO",
            "mensagem": "Armazenamento não configurado.",
            "verificado_em": datetime.now(),
            "latencia_ms": None,
        }

        try:
            self._validar_provider()
            if not google_drive_habilitado():
                retorno["mensagem"] = "Google Drive sem credenciais habilitadas no ambiente."
                return retorno

            retorno["status"] = "AUTENTICANDO"
            retorno["mensagem"] = "Validando autenticação e acesso ao Google Drive."

            service = obter_servico_drive()
            root_id = os.environ.get("GOOGLE_DRIVE_ROOT_FOLDER_ID")
            if root_id:
                service.files().get(
                    fileId=root_id,
                    fields="id,name,trashed",
                    supportsAllDrives=True,
                ).execute()
            else:
                service.about().get(fields="user(displayName)").execute()

            retorno["status"] = "OPERACIONAL"
            retorno["mensagem"] = "Google Drive autenticado e acessível pelo SGR."
            return retorno
        except Exception as exc:
            retorno["status"] = "INDISPONIVEL"
            retorno["mensagem"] = self._mensagem_segura(exc)
            return retorno
        finally:
            retorno["latencia_ms"] = int((time.perf_counter() - inicio) * 1000)
            retorno["verificado_em"] = datetime.now()

    @staticmethod
    def _mensagem_segura(exc: Exception) -> str:
        texto = str(exc or "Falha desconhecida de armazenamento.")
        # Evita propagar JSON/tokens muito longos ou detalhes sensíveis para a interface.
        if len(texto) > 350:
            texto = texto[:350] + "..."
        return texto

    def armazenar_arquivo(
        self,
        cur,
        *,
        caminho_local: str,
        empresa_id: int,
        empresa_nome: str,
        categoria: str,
        subcategoria: Optional[str],
        pasta_registro: str,
        origem: str,
        origem_id: int,
        tipo_arquivo: str,
        nome_original: str,
        pessoa_id: Optional[int] = None,
        criado_por_usuario_id: Optional[int] = None,
        data_referencia: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Armazena arquivo obrigatoriamente no provider configurado.

        Não existe fallback local silencioso. Se o provider falhar, uma exceção é
        lançada para que o fluxo chamador faça rollback da operação documental.
        """
        self._validar_provider()
        if not google_drive_habilitado():
            raise StorageServiceError(
                "Google Drive não está configurado ou habilitado. A operação foi interrompida sem persistir o documento."
            )
        if not caminho_local or not os.path.exists(caminho_local):
            raise StorageServiceError("Arquivo temporário não encontrado para envio ao armazenamento.")

        sha256_hex = self.calcular_sha256(caminho_local)
        try:
            upload_info = upload_arquivo_path_google_drive(
                caminho_local=caminho_local,
                empresa_id=empresa_id,
                empresa_nome=empresa_nome,
                categoria=categoria,
                subcategoria=subcategoria,
                pasta_registro=pasta_registro,
                origem=origem,
                origem_id=origem_id,
                motorista_id=None,
                motorista_nome=None,
                nome_original=nome_original,
                data_referencia=data_referencia,
            )
            arquivo_id = registrar_arquivo_sistema(
                cur,
                empresa_id=empresa_id,
                pessoa_id=pessoa_id,
                motorista_id=None,
                origem=origem,
                origem_id=origem_id,
                tipo_arquivo=tipo_arquivo,
                upload_info=upload_info,
                caminho_local=None,
                status_arquivo="ATIVO",
                criado_por_usuario_id=criado_por_usuario_id,
            )

            # Colunas adicionadas pela migração 16.4B. Mantemos o update separado
            # para reutilizar o registrador legado sem quebrar outros módulos.
            cur.execute(
                """
                UPDATE arquivos_sistema
                SET sha256_hex = %s,
                    versao = 1
                WHERE id = %s
                """,
                (sha256_hex, arquivo_id),
            )

            return {
                **upload_info,
                "arquivo_sistema_id": int(arquivo_id),
                "sha256_hex": sha256_hex,
                "url_interna": f"/arquivos/visualizar/{int(arquivo_id)}",
            }
        except (GoogleDriveStorageError, StorageServiceError):
            raise
        except Exception as exc:
            raise StorageServiceError(f"Falha ao armazenar arquivo no Google Drive: {self._mensagem_segura(exc)}") from exc
