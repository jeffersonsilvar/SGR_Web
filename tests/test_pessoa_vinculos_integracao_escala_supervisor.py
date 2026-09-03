from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def _trecho_carregar_escala_supervisor(source: str) -> str:
    arvore = ast.parse(source)
    for no in arvore.body:
        if isinstance(no, ast.FunctionDef) and no.name == "carregar_escala_supervisor":
            linhas = source.splitlines(keepends=True)
            return "".join(linhas[no.lineno - 1:no.end_lineno])
    raise AssertionError("carregar_escala_supervisor não encontrada")


def test_escala_supervisor_usa_vinculo_motorista_ativo_para_candidatos():
    trecho = _trecho_carregar_escala_supervisor(APP.read_text(encoding="utf-8"))

    assert "tipo_vinculo='MOTORISTA'" in trecho
    assert "pv_motorista_escala_supervisor" in trecho
    assert "mot.status_cadastro = 'Ativo'" in trecho


def test_escala_supervisor_preserva_pessoa_ja_escalada_na_data():
    trecho = _trecho_carregar_escala_supervisor(APP.read_text(encoding="utf-8"))

    assert "OR em.id IS NOT NULL" in trecho


def test_escala_supervisor_nao_depende_de_tipo_cadastro_motorista():
    trecho = _trecho_carregar_escala_supervisor(APP.read_text(encoding="utf-8"))

    assert "mot.tipo_cadastro = 'Motorista'" not in trecho
