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


def test_aplicador_substitui_helper_por_ast_sem_regex_destrutiva():
    fonte = (ROOT / "scripts" / "aplicar_storage_portal_prestador.py").read_text(encoding="utf-8")
    assert "ast.parse" in fonte
    assert 'NOME_FUNCAO = "tentar_enviar_arquivo_google_drive"' in fonte
    assert "armazenar_xml_portal_prestador" in fonte
    assert "re.sub" not in fonte


def test_portal_legado_continua_com_mesma_rota_e_tabela():
    fonte = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "@app.route('/portal-motorista/enviar-nf', methods=['GET', 'POST'])" in fonte
    assert "motorista_notas_fiscais" in fonte
    assert "motorista_nf_rotas" in fonte
