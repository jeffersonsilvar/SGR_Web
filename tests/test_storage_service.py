from pathlib import Path

import pytest

import app_modules.storage.service as storage_mod
from app_modules.storage import StorageService, StorageServiceError


ROOT = Path(__file__).resolve().parents[1]


class _FakeFiles:
    def get(self, **kwargs):
        class _Req:
            def execute(self):
                return {"id": kwargs.get("fileId"), "name": "SGR_Web", "trashed": False}
        return _Req()


class _FakeAbout:
    def get(self, **kwargs):
        class _Req:
            def execute(self):
                return {"user": {"displayName": "SGR"}}
        return _Req()


class _FakeService:
    def files(self):
        return _FakeFiles()

    def about(self):
        return _FakeAbout()


def test_health_check_operacional(monkeypatch):
    monkeypatch.setattr(storage_mod, "google_drive_habilitado", lambda: True)
    monkeypatch.setattr(storage_mod, "obter_servico_drive", lambda: _FakeService())
    resultado = StorageService("GOOGLE_DRIVE").health_check()
    assert resultado["status"] == "OPERACIONAL"
    assert resultado["provider"] == "GOOGLE_DRIVE"
    assert resultado["latencia_ms"] >= 0


def test_health_check_nao_configurado(monkeypatch):
    monkeypatch.setattr(storage_mod, "google_drive_habilitado", lambda: False)
    resultado = StorageService("GOOGLE_DRIVE").health_check()
    assert resultado["status"] == "NAO_CONFIGURADO"
    assert "credenciais" in resultado["mensagem"].lower()


def test_storage_obrigatorio_nao_faz_fallback_local(monkeypatch, tmp_path):
    arquivo = tmp_path / "nota.xml"
    arquivo.write_text("<xml/>", encoding="utf-8")
    monkeypatch.setattr(storage_mod, "google_drive_habilitado", lambda: False)

    with pytest.raises(StorageServiceError):
        StorageService("GOOGLE_DRIVE").armazenar_arquivo(
            None,
            caminho_local=str(arquivo),
            empresa_id=2,
            empresa_nome="Empresa Teste",
            categoria="Documentos_Fiscais",
            subcategoria="NFe_Uso_Consumo",
            pasta_registro="documento_1_fornecedor",
            origem="DOCUMENTO_FISCAL",
            origem_id=1,
            tipo_arquivo="XML_FISCAL",
            nome_original="nota.xml",
        )


def test_importacao_documental_usa_storage_service_sem_persistencia_local():
    fonte = (ROOT / "app_modules" / "documentos" / "importacao_xml.py").read_text(encoding="utf-8")
    assert "StorageService" in fonte
    assert "storage.armazenar_arquivo" in fonte
    assert "_mover_para_documento" not in fonte
    assert 'caminho_local=None' in (ROOT / "app_modules" / "storage" / "service.py").read_text(encoding="utf-8")
    assert '"url_interna": f"/arquivos/visualizar/' in (ROOT / "app_modules" / "storage" / "service.py").read_text(encoding="utf-8")


def test_migracao_storage_adiciona_hash_versao_e_health():
    migration = (ROOT / "database" / "migrations" / "20260827_blueprint16_4b_storage_service.sql").read_text(encoding="utf-8")
    assert "sha256_hex" in migration
    assert "versao" in migration
    assert "arquivo_anterior_id" in migration
    assert "storage_health_status" in migration
