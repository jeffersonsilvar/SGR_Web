from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def test_lancamento_rota_valida_motorista_por_vinculo_ativo():
    source = APP.read_text(encoding="utf-8")

    assert "tipo_vinculo='MOTORISTA'" in source
    assert "alias_vinculo='pv_motorista_rota'" in source
    assert "AND {condicao_motorista}" in source


def test_lancamento_rota_nao_valida_motorista_por_tipo_prestador_legado():
    source = APP.read_text(encoding="utf-8")

    trecho_legado = "AND (tipo_cadastro = 'Motorista' OR (tipo_cadastro = 'Prestador de Serviço' AND COALESCE(tipo_prestador, '') IN ('Motorista', 'Motorista e Ajudante'))) LIMIT 1"
    assert trecho_legado not in source
