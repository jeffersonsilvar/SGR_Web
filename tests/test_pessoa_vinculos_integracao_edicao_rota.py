from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def _trecho_editar_rota(source: str) -> str:
    inicio = source.index("def editar_rota(id):")
    fim = source.find("\n@app.", inicio)
    if fim == -1:
        fim = len(source)
    return source[inicio:fim]


def test_edicao_rota_valida_motorista_por_vinculo_ativo():
    source = APP.read_text(encoding="utf-8")
    trecho = _trecho_editar_rota(source)

    assert "tipo_vinculo='MOTORISTA'" in trecho
    assert "alias_vinculo='pv_motorista_edicao_rota'" in trecho
    assert "AND {condicao_motorista}" in trecho


def test_edicao_rota_nao_valida_motorista_por_tipo_prestador_legado():
    source = APP.read_text(encoding="utf-8")
    trecho = _trecho_editar_rota(source)

    legado = "AND (tipo_cadastro = 'Motorista' OR (tipo_cadastro = 'Prestador de Serviço' AND COALESCE(tipo_prestador, '') IN ('Motorista', 'Motorista e Ajudante'))) LIMIT 1"
    assert legado not in trecho
