from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def _trecho_financeiro_nfs_motoristas(source: str) -> str:
    arvore = ast.parse(source)
    for no in arvore.body:
        if isinstance(no, ast.FunctionDef) and no.name == "financeiro_nfs_motoristas":
            linhas = source.splitlines(keepends=True)
            return "".join(linhas[no.lineno - 1:no.end_lineno])
    raise AssertionError("financeiro_nfs_motoristas não encontrada")


def test_financeiro_nf_filtra_motoristas_por_vinculo_ativo():
    trecho = _trecho_financeiro_nfs_motoristas(APP.read_text(encoding="utf-8"))

    assert "tipo_vinculo='MOTORISTA'" in trecho
    assert "pv_motorista_financeiro_nf" in trecho
    assert "p.status_cadastro = 'Ativo'" in trecho


def test_financeiro_nf_nao_filtra_motoristas_por_tipo_cadastro_legado():
    trecho = _trecho_financeiro_nfs_motoristas(APP.read_text(encoding="utf-8"))

    assert "WHERE tipo_cadastro = 'Motorista'" not in trecho


def test_financeiro_nf_preserva_filtro_multiempresa():
    trecho = _trecho_financeiro_nfs_motoristas(APP.read_text(encoding="utf-8"))

    assert "if is_super_admin:" in trecho
    assert "empresa_id_filtro and empresa_id_filtro.isdigit()" in trecho
    assert "query_motoristas += ' AND p.empresa_id = %s'" in trecho
    assert "params_motoristas.append(empresa_logada_id)" in trecho
