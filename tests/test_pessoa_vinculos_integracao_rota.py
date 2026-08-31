from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def _trecho_lancamento_rota():
    source = APP.read_text(encoding="utf-8")
    inicio = source.index("def lancar_rota():")
    fim = source.index("\n@app.route(", inicio)
    return source[inicio:fim]


def test_lancamento_rota_valida_motorista_por_vinculo_ativo():
    trecho = _trecho_lancamento_rota()

    assert "tipo_vinculo='MOTORISTA'" in trecho
    assert "alias_vinculo='pv_motorista_rota'" in trecho
    assert "AND {condicao_motorista}" in trecho


def test_lancamento_rota_nao_valida_motorista_por_tipo_prestador_legado():
    trecho = _trecho_lancamento_rota()

    trecho_legado = "AND (tipo_cadastro = 'Motorista' OR (tipo_cadastro = 'Prestador de Serviço' AND COALESCE(tipo_prestador, '') IN ('Motorista', 'Motorista e Ajudante'))) LIMIT 1"
    assert trecho_legado not in trecho
