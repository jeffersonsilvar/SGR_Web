import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def _trecho_lancamento_ajudante(source: str) -> str:
    arvore = ast.parse(source)
    linhas = source.splitlines(keepends=True)
    for no in arvore.body:
        if isinstance(no, ast.FunctionDef) and no.name == "lancamento_ajudante":
            return "".join(linhas[no.lineno - 1:no.end_lineno])
    raise AssertionError("Função lancamento_ajudante não encontrada.")


def test_lancamento_ajudante_valida_por_vinculo_ativo():
    trecho = _trecho_lancamento_ajudante(APP.read_text(encoding="utf-8"))

    assert "tipo_vinculo='AJUDANTE'" in trecho
    assert "alias_vinculo='pv_ajudante_lancamento'" in trecho
    assert "AND {condicao_ajudante}" in trecho


def test_lancamento_ajudante_lista_por_vinculo_ativo():
    trecho = _trecho_lancamento_ajudante(APP.read_text(encoding="utf-8"))

    assert "alias_vinculo='pv_ajudante_lista_lancamento'" in trecho
    assert "AND {condicao_ajudante_lista}" in trecho
    assert "ORDER BY p.nome_completo ASC" in trecho


def test_lancamento_ajudante_nao_depende_de_tipo_cadastro_legado():
    trecho = _trecho_lancamento_ajudante(APP.read_text(encoding="utf-8"))

    assert "tipo_cadastro = 'Ajudante'" not in trecho
    assert "COALESCE(tipo_prestador, '') IN ('Ajudante', 'Motorista e Ajudante')" not in trecho
