from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cadastro_manual_storage_substitui_rota_legada(app):
    regras = [
        regra
        for regra in app.url_map.iter_rules()
        if regra.rule == "/documentos-fiscais/novo"
    ]
    assert len(regras) == 1
    assert regras[0].endpoint == "documentos.novo_documento_fiscal"


def test_cadastro_manual_usa_storage_service_sem_persistencia_local():
    fonte = (ROOT / "app_modules" / "documentos" / "cadastro_manual_storage.py").read_text(encoding="utf-8")
    assert "StorageService" in fonte
    assert "storage.armazenar_upload" in fonte
    assert "Path(\"uploads\")" not in fonte
    assert "arquivo.save(" not in fonte


def test_cadastro_manual_registra_xml_pdf_em_arquivos_sistema_indiretamente():
    fonte = (ROOT / "app_modules" / "documentos" / "cadastro_manual_storage.py").read_text(encoding="utf-8")
    assert 'tipo_arquivo="XML_FISCAL"' in fonte
    assert 'tipo_arquivo="PDF_FISCAL"' in fonte
    assert 'origem": "DOCUMENTO_FISCAL"' in fonte
    assert 'info_xml.get("url_interna")' in fonte
    assert 'info_pdf.get("url_interna")' in fonte


def test_cadastro_manual_exige_vinculo_com_pessoa():
    fonte = (ROOT / "app_modules" / "documentos" / "cadastro_manual_storage.py").read_text(encoding="utf-8")
    assert "Documentos fiscais finalizados precisam estar vinculados ao cadastro de Pessoas" in fonte
    assert "SELECT id, nome_completo, cpf_cnpj FROM pessoas WHERE id = %s AND empresa_id = %s" in fonte


def test_cadastro_manual_habilita_cte_e_origem_explicita():
    fonte = (ROOT / "app_modules" / "documentos" / "cadastro_manual_storage.py").read_text(encoding="utf-8")
    assert 'setdefault("CTE", "CT-e Transporte")' in fonte
    assert '"CTE": "CTe_Transporte"' in fonte
    assert "'CADASTRO_MANUAL'" in fonte
