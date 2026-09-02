from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def _trecho_visualizar_rotas(source: str) -> str:
    inicio = source.index("def visualizar_rotas():")
    fim = source.index("\n\n\n@app.route('/movimentacao/rotas/divergencias'", inicio)
    return source[inicio:fim]


def test_visualizar_rotas_lista_motoristas_por_vinculo_ativo():
    source = APP.read_text(encoding="utf-8")
    trecho = _trecho_visualizar_rotas(source)

    assert "tipo_vinculo='MOTORISTA'" in trecho
    assert "alias_vinculo='pv_motorista_filtro_rotas'" in trecho
    assert "AND {condicao_motorista_filtro}" in trecho


def test_visualizar_rotas_nao_filtra_lista_motoristas_por_tipo_cadastro_legado():
    source = APP.read_text(encoding="utf-8")
    trecho = _trecho_visualizar_rotas(source)

    legado = "WHERE tipo_cadastro = 'Motorista'"
    assert legado not in trecho


def test_visualizar_rotas_preserva_filtro_multiempresa_na_lista_motoristas():
    source = APP.read_text(encoding="utf-8")
    trecho = _trecho_visualizar_rotas(source)

    assert "filtro_empresa_motorista = filtro_empresa_lista.replace('empresa_id', 'p.empresa_id')" in trecho
    assert "{filtro_empresa_motorista}" in trecho
