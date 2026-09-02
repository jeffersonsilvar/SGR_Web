from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

OLD = """cur.execute(\"\"\"\n                    SELECT id, nome_completo\n                    FROM pessoas\n                    WHERE empresa_id = %s\n                      AND tipo_cadastro = 'Motorista'\n                      AND status_cadastro = 'Ativo'\n                    ORDER BY nome_completo ASC\n                    \"\"\", (empresa_id,))\n        motoristas = cur.fetchall()"""

NEW = """from app_modules.pessoas.vinculos import condicao_sql_vinculo_pessoa\n\n        condicao_motorista_lista = condicao_sql_vinculo_pessoa(\n            alias_pessoa='p',\n            tipo_vinculo='MOTORISTA',\n            alias_vinculo='pv_motorista_lista_edicao_rota',\n        )\n        cur.execute(f\"\"\"\n                    SELECT p.id, p.nome_completo\n                    FROM pessoas p\n                    WHERE p.empresa_id = %s\n                      AND p.status_cadastro = 'Ativo'\n                      AND {condicao_motorista_lista}\n                    ORDER BY p.nome_completo ASC\n                    \"\"\", (empresa_id,))\n        motoristas = cur.fetchall()"""


def localizar_funcao_editar_rota(source: str):
    arvore = ast.parse(source, filename=str(APP))
    for no in arvore.body:
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)) and no.name == "editar_rota":
            return no
    raise RuntimeError("Função editar_rota não encontrada; nenhuma alteração foi feita.")


def main():
    source = APP.read_text(encoding="utf-8")
    no = localizar_funcao_editar_rota(source)
    linhas = source.splitlines(keepends=True)
    inicio = no.lineno - 1
    fim = no.end_lineno
    trecho = "".join(linhas[inicio:fim])

    if NEW in trecho:
        print("Blueprint 17.2F já aplicada em app.py.")
        return

    ocorrencias = trecho.count(OLD)
    if ocorrencias != 1:
        raise RuntimeError(
            f"Bloco esperado da listagem de Motoristas na edição de rota encontrado {ocorrencias} vez(es) "
            "dentro de editar_rota; nenhuma alteração foi feita."
        )

    trecho_atualizado = trecho.replace(OLD, NEW, 1)
    linhas[inicio:fim] = [trecho_atualizado]
    atualizado = "".join(linhas)
    ast.parse(atualizado, filename=str(APP))
    APP.write_text(atualizado, encoding="utf-8", newline="\n")
    print("Blueprint 17.2F aplicada: edição de rota lista Motoristas por vínculo MOTORISTA ativo.")


if __name__ == "__main__":
    main()
