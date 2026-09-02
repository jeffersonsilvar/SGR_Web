from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def _trecho_editar_rota(source: str) -> str:
    inicio = source.index("def editar_rota(id):")
    fim = source.index("\n\n@app.route('/movimentacao/excluir/<int:id>'", inicio)
    return source[inicio:fim]


def test_edicao_rota_lista_motoristas_por_vinculo_ativo():
    source = APP.read_text(encoding="utf-8")
    trecho = _trecho_editar_rota(source)

    assert "tipo_vinculo='MOTORISTA'" in trecho
    assert "alias_vinculo='pv_motorista_lista_edicao_rota'" in trecho
    assert "AND {condicao_motorista_lista}" in trecho


def test_edicao_rota_nao_lista_motoristas_por_tipo_cadastro_legado():
    source = APP.read_text(encoding="utf-8")
    trecho = _trecho_editar_rota(source)

    legado = "AND tipo_cadastro = 'Motorista'"
    assert legado not in trecho
