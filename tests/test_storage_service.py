from io import BytesIO
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage

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


def test_armazenar_upload_e_contrato_generico(monkeypatch):
    storage = StorageService("GOOGLE_DRIVE")
    capturado = {}

    def fake_armazenar(cur, **kwargs):
        caminho = Path(kwargs["caminho_local"])
        capturado["existe_durante"] = caminho.exists()
        capturado["conteudo"] = caminho.read_bytes()
        capturado["nome_original"] = kwargs["nome_original"]
        capturado["caminho"] = caminho
        return {"arquivo_sistema_id": 99, "url_interna": "/arquivos/visualizar/99"}

    monkeypatch.setattr(storage, "armazenar_arquivo", fake_armazenar)
    upload = FileStorage(stream=BytesIO(b"conteudo-teste"), filename="comprovante.pdf")
    resultado = storage.armazenar_upload(
        None,
        arquivo=upload,
        empresa_id=2,
        empresa_nome="Empresa Teste",
        categoria="Financeiro",
        subcategoria="Comprovantes",
        pasta_registro="titulo_10",
        origem="COMPROVANTE_BAIXA_TITULO",
        origem_id=10,
        tipo_arquivo="COMPROVANTE",
    )

    assert capturado["existe_durante"] is True
    assert capturado["conteudo"] == b"conteudo-teste"
    assert capturado["nome_original"] == "comprovante.pdf"
    assert not capturado["caminho"].exists()
    assert resultado["arquivo_sistema_id"] == 99


def test_baixar_arquivo_abstrai_provider(monkeypatch):
    monkeypatch.setattr(storage_mod, "baixar_arquivo_google_drive", lambda file_id: b"xml-original")
    resultado = StorageService("GOOGLE_DRIVE").baixar_arquivo({
        "storage_provider": "GOOGLE_DRIVE",
        "drive_file_id": "drive-123",
    })
    assert resultado == b"xml-original"


def test_mensagem_segura_oculta_token_e_caminho():
    mensagem = StorageService._mensagem_segura(
        RuntimeError(r"access_token=segredo C:\Users\Pessoa\token_google_drive.json")
    )
    assert "segredo" not in mensagem
    assert "token_google_drive.json" not in mensagem


def test_compensa_upload_se_registro_no_banco_falhar(monkeypatch, tmp_path):
    arquivo = tmp_path / "nota.xml"
    arquivo.write_text("<xml/>", encoding="utf-8")
    removidos = []

    monkeypatch.setattr(storage_mod, "google_drive_habilitado", lambda: True)
    monkeypatch.setattr(
        storage_mod,
        "upload_arquivo_path_google_drive",
        lambda **kwargs: {"drive_file_id": "drive-orphan", "id": "drive-orphan"},
    )
    monkeypatch.setattr(
        storage_mod,
        "registrar_arquivo_sistema",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("falha banco")),
    )

    storage = StorageService("GOOGLE_DRIVE")
    monkeypatch.setattr(
        storage,
        "_excluir_objeto_provider_silenciosamente",
        lambda drive_file_id: removidos.append(drive_file_id) or True,
    )

    with pytest.raises(StorageServiceError):
        storage.armazenar_arquivo(
            object(),
            caminho_local=str(arquivo),
            empresa_id=2,
            empresa_nome="Empresa Teste",
            categoria="Documentos_Fiscais",
            subcategoria="NFSe_Prestador",
            pasta_registro="nf_10",
            origem="DOCUMENTO_FISCAL",
            origem_id=10,
            tipo_arquivo="XML_FISCAL",
            nome_original="nota.xml",
        )

    assert removidos == ["drive-orphan"]


def test_desfazer_armazenamento_disponivel_para_rollback_do_chamador(monkeypatch):
    storage = StorageService("GOOGLE_DRIVE")
    removidos = []
    monkeypatch.setattr(
        storage,
        "_excluir_objeto_provider_silenciosamente",
        lambda drive_file_id: removidos.append(drive_file_id) or True,
    )

    assert storage.desfazer_armazenamento({"drive_file_id": "drive-rollback"}) is True
    assert removidos == ["drive-rollback"]


def test_falha_upload_real_atualiza_health_indisponivel(monkeypatch, tmp_path):
    arquivo = tmp_path / "nota.xml"
    arquivo.write_text("<xml/>", encoding="utf-8")
    health = []

    monkeypatch.setattr(storage_mod, "google_drive_habilitado", lambda: True)
    monkeypatch.setattr(
        storage_mod,
        "upload_arquivo_path_google_drive",
        lambda **kwargs: (_ for _ in ()).throw(GoogleDriveStorageError("provider fora")),
    )
    monkeypatch.setattr(
        storage_mod,
        "registrar_status_storage",
        lambda **kwargs: health.append(kwargs) or True,
    )

    with pytest.raises(StorageServiceError):
        StorageService("GOOGLE_DRIVE").armazenar_arquivo(
            object(),
            caminho_local=str(arquivo),
            empresa_id=2,
            empresa_nome="Empresa Teste",
            categoria="Documentos_Fiscais",
            subcategoria="NFSe_Prestador",
            pasta_registro="nf_20",
            origem="DOCUMENTO_FISCAL",
            origem_id=20,
            tipo_arquivo="XML_FISCAL",
            nome_original="nota.xml",
        )

    assert health[-1]["status"] == "INDISPONIVEL"
    assert health[-1]["provider"] == "GOOGLE_DRIVE"


def test_storage_desabilitado_atualiza_health_nao_configurado(monkeypatch, tmp_path):
    arquivo = tmp_path / "nota.xml"
    arquivo.write_text("<xml/>", encoding="utf-8")
    health = []

    monkeypatch.setattr(storage_mod, "google_drive_habilitado", lambda: False)
    monkeypatch.setattr(
        storage_mod,
        "registrar_status_storage",
        lambda **kwargs: health.append(kwargs) or True,
    )

    with pytest.raises(StorageServiceError):
        StorageService("GOOGLE_DRIVE").armazenar_arquivo(
            object(),
            caminho_local=str(arquivo),
            empresa_id=2,
            empresa_nome="Empresa Teste",
            categoria="Documentos_Fiscais",
            subcategoria="NFSe_Prestador",
            pasta_registro="nf_21",
            origem="DOCUMENTO_FISCAL",
            origem_id=21,
            tipo_arquivo="XML_FISCAL",
            nome_original="nota.xml",
        )

    assert health[-1]["status"] == "NAO_CONFIGURADO"


def test_falha_download_real_atualiza_health_indisponivel(monkeypatch):
    health = []
    monkeypatch.setattr(
        storage_mod,
        "baixar_arquivo_google_drive",
        lambda file_id: (_ for _ in ()).throw(GoogleDriveStorageError("download indisponivel")),
    )
    monkeypatch.setattr(
        storage_mod,
        "registrar_status_storage",
        lambda **kwargs: health.append(kwargs) or True,
    )

    with pytest.raises(StorageServiceError):
        StorageService("GOOGLE_DRIVE").baixar_arquivo({
            "storage_provider": "GOOGLE_DRIVE",
            "drive_file_id": "drive-erro",
        })

    assert health[-1]["status"] == "INDISPONIVEL"
    assert "download indisponivel" in health[-1]["mensagem"]


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
