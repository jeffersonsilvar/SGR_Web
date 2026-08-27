from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_busca_pessoas_normaliza_cpf_cnpj_sem_mascara():
    fonte = (ROOT / "app_modules" / "documentos" / "busca_pessoas.py").read_text(encoding="utf-8")
    assert "REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(cpf_cnpj" in fonte
    assert "_somente_digitos(termo)" in fonte
    assert 'ROTA_BUSCA_PESSOAS = "/documentos-fiscais/api/pessoas"' in fonte


def test_busca_pessoas_mantem_pesquisa_por_nome():
    fonte = (ROOT / "app_modules" / "documentos" / "busca_pessoas.py").read_text(encoding="utf-8")
    assert "nome_completo LIKE %s" in fonte
    assert "ORDER BY nome_completo" in fonte


def test_blueprint_registra_busca_pessoas_normalizada():
    fonte = (ROOT / "app_modules" / "documentos" / "__init__.py").read_text(encoding="utf-8")
    assert "registrar_busca_pessoas_normalizada" in fonte
