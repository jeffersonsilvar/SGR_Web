from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def _trecho_lancar_rota(source: str) -> str:
    inicio = source.index("def lancar_rota():")
    fim = source.index("\ndef carregar_pessoas_por_tipo", inicio)
    return source[inicio:fim]


def test_lancamento_rota_lista_motoristas_por_vinculo_ativo():
    source = APP.read_text(encoding="utf-8")
    trecho = _trecho_lancar_rota(source)

    assert "tipo_vinculo='MOTORISTA'" in trecho
    assert "alias_vinculo='pv_motorista_lista_lancar_rota'" in trecho
    assert "AND {condicao_motorista_lista}" in trecho


def test_lancamento_rota_lista_nao_depende_de_tipo_prestador_legado():
    source = APP.read_text(encoding="utf-8")
    trecho = _trecho_lancar_rota(source)

    legado = "AND (tipo_cadastro = 'Motorista' OR (tipo_cadastro = 'Prestador de Serviço' AND COALESCE(tipo_prestador, '') IN ('Motorista', 'Motorista e Ajudante')))"
    assert legado not in trecho
