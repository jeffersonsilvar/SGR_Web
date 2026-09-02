from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

OLD = """cur.execute(\"\"\"
                    SELECT id, nome_completo
                    FROM pessoas
                    WHERE empresa_id = %s
                      AND status_cadastro = 'Ativo'
                      AND (tipo_cadastro = 'Motorista' OR (tipo_cadastro = 'Prestador de Serviço' AND COALESCE(tipo_prestador, '') IN ('Motorista', 'Motorista e Ajudante')))
                    ORDER BY nome_completo ASC
                    \"\"\", (empresa_id,))
        motoristas = cur.fetchall()"""

NEW = """from app_modules.pessoas.vinculos import condicao_sql_vinculo_pessoa

        condicao_motorista_lista = condicao_sql_vinculo_pessoa(
            alias_pessoa='p',
            tipo_vinculo='MOTORISTA',
            alias_vinculo='pv_motorista_lista_lancar_rota',
        )
        cur.execute(f\"\"\"
                    SELECT p.id, p.nome_completo
                    FROM pessoas p
                    WHERE p.empresa_id = %s
                      AND p.status_cadastro = 'Ativo'
                      AND {condicao_motorista_lista}
                    ORDER BY p.nome_completo ASC
                    \"\"\", (empresa_id,))
        motoristas = cur.fetchall()"""


def localizar_funcao(source: str):
    arvore = ast.parse(source, filename=str(APP))
    for no in arvore.body:
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)) and no.name == "lancar_rota":
            return no
    raise RuntimeError("Função lancar_rota não encontrada; nenhuma alteração foi feita.")


def main():
    source = APP.read_text(encoding="utf-8")
    no = localizar_funcao(source)
    linhas = source.splitlines(keepends=True)
    inicio = no.lineno - 1
    fim = no.end_lineno
    trecho = "".join(linhas[inicio:fim])

    if NEW in trecho:
        print("Blueprint 17.2I já aplicada em app.py.")
        return

    ocorrencias = trecho.count(OLD)
    if ocorrencias != 1:
        raise RuntimeError(
            f"Bloco esperado da listagem de Motoristas encontrado {ocorrencias} vez(es) dentro de lancar_rota; "
            "nenhuma alteração foi feita."
        )

    trecho_atualizado = trecho.replace(OLD, NEW, 1)
    linhas[inicio:fim] = [trecho_atualizado]
    atualizado = "".join(linhas)
    ast.parse(atualizado, filename=str(APP))
    APP.write_text(atualizado, encoding="utf-8", newline="\n")
    print("Blueprint 17.2I aplicada: lançamento de rota lista Motoristas por vínculo MOTORISTA ativo.")


if __name__ == "__main__":
    main()
