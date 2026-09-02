from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

OLD = """cur.execute(f\"\"\"
            SELECT id, nome_completo
            FROM pessoas
            WHERE tipo_cadastro = 'Motorista'
              AND status_cadastro = 'Ativo'
              {filtro_empresa_lista}
            ORDER BY nome_completo ASC
        \"\"\", lista_params)

        motoristas = cur.fetchall()"""

NEW = """from app_modules.pessoas.vinculos import condicao_sql_vinculo_pessoa

        condicao_motorista_filtro = condicao_sql_vinculo_pessoa(
            alias_pessoa='p',
            tipo_vinculo='MOTORISTA',
            alias_vinculo='pv_motorista_filtro_rotas',
        )
        filtro_empresa_motorista = filtro_empresa_lista.replace('empresa_id', 'p.empresa_id')
        cur.execute(f\"\"\"
            SELECT p.id, p.nome_completo
            FROM pessoas p
            WHERE p.status_cadastro = 'Ativo'
              AND {condicao_motorista_filtro}
              {filtro_empresa_motorista}
            ORDER BY p.nome_completo ASC
        \"\"\", lista_params)

        motoristas = cur.fetchall()"""


def localizar_funcao(source: str):
    arvore = ast.parse(source, filename=str(APP))
    for no in arvore.body:
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)) and no.name == "visualizar_rotas":
            return no
    raise RuntimeError("Função visualizar_rotas não encontrada; nenhuma alteração foi feita.")


def main():
    source = APP.read_text(encoding="utf-8")
    no = localizar_funcao(source)
    linhas = source.splitlines(keepends=True)
    inicio = no.lineno - 1
    fim = no.end_lineno
    trecho = "".join(linhas[inicio:fim])

    if NEW in trecho:
        print("Blueprint 17.2H já aplicada em app.py.")
        return

    ocorrencias = trecho.count(OLD)
    if ocorrencias != 1:
        raise RuntimeError(
            f"Bloco esperado do filtro de Motoristas encontrado {ocorrencias} vez(es) dentro de visualizar_rotas; "
            "nenhuma alteração foi feita."
        )

    trecho_atualizado = trecho.replace(OLD, NEW, 1)
    linhas[inicio:fim] = [trecho_atualizado]
    atualizado = "".join(linhas)
    ast.parse(atualizado, filename=str(APP))
    APP.write_text(atualizado, encoding="utf-8", newline="\n")
    print("Blueprint 17.2H aplicada: filtro de rotas lista Motoristas por vínculo MOTORISTA ativo.")


if __name__ == "__main__":
    main()
