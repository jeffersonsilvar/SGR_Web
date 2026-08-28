from __future__ import annotations

from datetime import datetime
import hashlib
import os
import re
import tempfile
import time
from typing import Any, Dict, Optional

from google_drive_storage import (
    GoogleDriveStorageError,
    baixar_arquivo_google_drive,
    google_drive_habilitado,
    obter_servico_drive,
    registrar_arquivo_sistema,
    upload_arquivo_path_google_drive,
)


class StorageServiceError(Exception):
    """Erro controlado da camada genérica de armazenamento do SGR."""


class StorageService:
    """Camada genérica de armazenamento de arquivos do SGR.

    Os módulos de negócio não devem depender diretamente de Google Drive, S3,
    Azure etc. O provider é resolvido aqui. Nesta fase, GOOGLE_DRIVE é o adapter
    implementado para produção e não existe fallback local silencioso.
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
        texto = re.sub(r"[A-Za-z]:\\[^\r\n,;]+", "[caminho local ocultado]", texto)
        texto = re.sub(r"/(?:home|Users)/[^\r\n,;]+", "[caminho local ocultado]", texto)
        texto = re.sub(
            r"(?i)(access_token|refresh_token|client_secret|authorization)\s*[:=]\s*[^\s,;]+",
            r"\1=[ocultado]",
            texto,
        )
        if len(texto) > 350:
            texto = texto[:350] + "..."
        return texto

    def _excluir_objeto_provider_silenciosamente(self, drive_file_id: Optional[str]) -> bool:
        """Compensa um upload externo quando a persistência local falha.

        Esta rotina é deliberadamente best-effort: nunca mascara a exceção
        original do fluxo. Retorna True apenas quando a exclusão foi confirmada.
        """
        if not drive_file_id:
            return False
        try:
            self._validar_provider()
            service = obter_servico_drive()
            service.files().delete(
                fileId=str(drive_file_id),
                supportsAllDrives=True,
            ).execute()
            return True
        except Exception:
            return False

    def desfazer_armazenamento(self, arquivo: Optional[Dict[str, Any]]) -> bool:
        """Remove do provider um arquivo recém-enviado após rollback do chamador.

        O método permite que fluxos transacionais maiores compensem o objeto
        externo caso uma etapa posterior ao StorageService falhe antes do commit.
        """
        if not arquivo:
            return False
        drive_file_id = arquivo.get("drive_file_id") or arquivo.get("id")
        return self._excluir_objeto_provider_silenciosamente(drive_file_id)

    def armazenar_upload(self, cur, *, arquivo, **kwargs) -> Optional[Dict[str, Any]]:
        """Entrada padrão para FileStorage/objetos de upload da aplicação.

        O arquivo fica localmente apenas durante o processamento e é removido em
        seguida. Este método é o contrato indicado para os demais módulos do SGR.
        """
        if not arquivo or not getattr(arquivo, "filename", None):
            return None

        nome_original = kwargs.pop("nome_original", None) or os.path.basename(str(arquivo.filename))
        extensao = os.path.splitext(nome_original)[1]
        caminho_temporario = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as temporario:
                caminho_temporario = temporario.name

            if hasattr(arquivo, "save"):
                arquivo.save(caminho_temporario)
            else:
                conteudo = arquivo.read()
                with open(caminho_temporario, "wb") as destino:
                    destino.write(conteudo)

            return self.armazenar_arquivo(
                cur,
                caminho_local=caminho_temporario,
                nome_original=nome_original,
                **kwargs,
            )
        finally:
            if caminho_temporario:
                try:
                    os.remove(caminho_temporario)
                except OSError:
                    pass

    def baixar_arquivo(self, arquivo: Dict[str, Any]) -> bytes:
        """Lê bytes de um arquivo privado através do provider configurado."""
        if not arquivo:
            raise StorageServiceError("Metadados do arquivo não informados.")

        provider_arquivo = str(arquivo.get("storage_provider") or self.provider).strip().upper()
        if provider_arquivo != self.provider:
            raise StorageServiceError("Provider do arquivo difere do provider solicitado.")

        self._validar_provider()
        drive_file_id = arquivo.get("drive_file_id")
        if not drive_file_id:
            raise StorageServiceError("Arquivo sem identificador válido no armazenamento externo.")

        try:
            return baixar_arquivo_google_drive(str(drive_file_id))
        except GoogleDriveStorageError as exc:
            raise StorageServiceError(
                f"Google Drive indisponível: {self._mensagem_segura(exc)}"
            ) from exc
        except Exception as exc:
            raise StorageServiceError(
                f"Falha ao ler arquivo no armazenamento: {self._mensagem_segura(exc)}"
            ) from exc

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
        Se o upload externo já tiver ocorrido e a persistência em arquivos_sistema
        falhar, o objeto recém-criado é removido do provider como compensação.
        """
        self._validar_provider()
        if not google_drive_habilitado():
            raise StorageServiceError(
                "Google Drive não está configurado ou habilitado. A operação foi interrompida sem persistir o documento."
            )
        if not caminho_local or not os.path.exists(caminho_local):
            raise StorageServiceError("Arquivo temporário não encontrado para envio ao armazenamento.")

        sha256_hex = self.calcular_sha256(caminho_local)
        upload_info = None
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
        except StorageServiceError:
            if upload_info:
                self.desfazer_armazenamento(upload_info)
            raise
        except GoogleDriveStorageError as exc:
            if upload_info:
                self.desfazer_armazenamento(upload_info)
            raise StorageServiceError(
                f"Google Drive indisponível: {self._mensagem_segura(exc)}"
            ) from exc
        except Exception as exc:
            if upload_info:
                self.desfazer_armazenamento(upload_info)
            raise StorageServiceError(
                f"Falha ao armazenar arquivo no Google Drive: {self._mensagem_segura(exc)}"
            ) from exc
