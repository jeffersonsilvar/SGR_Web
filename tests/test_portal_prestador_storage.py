from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_adapter_portal_prestador_usa_storage_service_sem_fallback_local():
    fonte = (ROOT / "app_modules" / "storage" / "portal_prestador.py").read_text(encoding="utf-8")
    assert "StorageService" in fonte
    assert "storage.armazenar_arquivo" in fonte
    assert 'subcategoria="NFSe_Prestador"' in fonte
    assert 'origem="XML_MOTORISTA"' in fonte
    assert 'tipo_arquivo="XML_NF_MOTORISTA"' in fonte
    assert "os.remove(caminho_absoluto)" in fonte
    assert "fallback" in fonte.lower()


def test_portal_prestador_adota_pessoa_como_identidade_principal():
    fonte = (ROOT / "app_modules" / "storage" / "portal_prestador.py").read_text(encoding="utf-8")
    assert "def _resolver_pessoa_prestador" in fonte
    assert "pessoa_id=None" in fonte
    assert "motorista_id=None" in fonte
    assert "pessoa_id=pessoa_id_resolvida" in fonte
    assert "FROM pessoas" in fonte
    assert "AND empresa_id = %s" in fonte


def test_motorista_id_permanece_apenas_alias_legado_no_adapter():
    fonte = (ROOT / "app_modules" / "storage" / "portal_prestador.py").read_text(encoding="utf-8")
    assert "pessoa_id if pessoa_id is not None else motorista_id" in fonte
    assert "alias legado" in fonte
    storage = (ROOT / "app_modules" / "storage" / "service.py").read_text(encoding="utf-8")
    assert "pessoa_id=pessoa_id" in storage
    assert "motorista_id=None" in storage


def test_app_consolidado_encaminha_xml_motorista_para_storage_service():
    fonte = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'if origem != \'XML_MOTORISTA\':' in fonte
    assert "from app_modules.storage.portal_prestador import armazenar_xml_portal_prestador" in fonte
    assert "return armazenar_xml_portal_prestador(" in fonte
    assert "Usando fallback local" not in fonte


def test_portal_legado_continua_com_mesma_rota_e_tabela():
    fonte = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "@app.route('/portal-motorista/enviar-nf', methods=['GET', 'POST'])" in fonte
    assert "motorista_notas_fiscais" in fonte
    assert "motorista_nf_rotas" in fonte
