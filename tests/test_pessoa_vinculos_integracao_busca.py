from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def test_busca_uso_motorista_consulta_vinculo_ativo():
    source = APP.read_text(encoding="utf-8")

    assert "from app_modules.pessoas.vinculos import condicao_sql_vinculo_pessoa" in source
    assert "tipo_vinculo='MOTORISTA'" in source
    assert "alias_vinculo='pv_motorista'" in source
    assert "query += f\" AND {condicao_sql_motorista_prestador('p')}\"" not in source


def test_migracao_da_busca_nao_remove_legado_de_ajudante():
    source = APP.read_text(encoding="utf-8")

    assert "elif uso == 'ajudante':" in source
    assert "condicao_sql_ajudante_prestador('p')" in source
