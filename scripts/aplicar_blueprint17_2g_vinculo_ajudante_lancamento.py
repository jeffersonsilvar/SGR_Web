from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

POST_OLD = """cur.execute(\"\"\"
                        SELECT id, nome_completo
                        FROM pessoas
                        WHERE id = %s
                          AND empresa_id = %s
                          AND status_cadastro = 'Ativo'
                          AND (tipo_cadastro = 'Ajudante' OR (tipo_cadastro = 'Prestador de Serviço' AND COALESCE(tipo_prestador, '') IN ('Ajudante', 'Motorista e Ajudante'))) LIMIT 1
                        \"\"\", (ajudante_id, empresa_id))"""

POST_NEW = """from app_modules.pessoas.vinculos import condicao_sql_vinculo_pessoa

            condicao_ajudante = condicao_sql_vinculo_pessoa(
                alias_pessoa='p',
                tipo_vinculo='AJUDANTE',
                alias_vinculo='pv_ajudante_lancamento',
            )
            cur.execute(f\"\"\"
                        SELECT p.id, p.nome_completo
                        FROM pessoas p
                        WHERE p.id = %s
                          AND p.empresa_id = %s
                          AND p.status_cadastro = 'Ativo'
                          AND {condicao_ajudante}
                        LIMIT 1
                        \"\"\", (ajudante_id, empresa_id))"""

GET_OLD = """cur.execute(\"\"\"
                    SELECT id, nome_completo
                    FROM pessoas
                    WHERE empresa_id = %s
                      AND tipo_cadastro = 'Ajudante'
                      AND status_cadastro = 'Ativo'
                    ORDER BY nome_completo ASC
                    \"\"\", (empresa_id,))

        ajudantes = cur.fetchall()"""

GET_NEW = """from app_modules.pessoas.vinculos import condicao_sql_vinculo_pessoa

        condicao_ajudante_lista = condicao_sql_vinculo_pessoa(
            alias_pessoa='p',
            tipo_vinculo='AJUDANTE',
            alias_vinculo='pv_ajudante_lista_lancamento',
        )
        cur.execute(f\"\"\"
                    SELECT p.id, p.nome_completo
                    FROM pessoas p
                    WHERE p.empresa_id = %s
                      AND p.status_cadastro = 'Ativo'
                      AND {condicao_ajudante_lista}
                    ORDER BY p.nome_completo ASC
                    \"\"\", (empresa_id,))

        ajudantes = cur.fetchall()"""


def localizar_funcao(source: str):
    arvore = ast.parse(source, filename=str(APP))
    for no in arvore.body:
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)) and no.name == "lancamento_ajudante":
            return no
    raise RuntimeError("Função lancamento_ajudante não encontrada; nenhuma alteração foi feita.")


def substituir_unico(trecho: str, antigo: str, novo: str, descricao: str) -> str:
    if novo in trecho:
        return trecho
    ocorrencias = trecho.count(antigo)
    if ocorrencias != 1:
        raise RuntimeError(
            f"Bloco de {descricao} encontrado {ocorrencias} vez(es) dentro de lancamento_ajudante; "
            "nenhuma alteração foi feita."
        )
    return trecho.replace(antigo, novo, 1)


def main():
    source = APP.read_text(encoding="utf-8")
    no = localizar_funcao(source)
    linhas = source.splitlines(keepends=True)
    inicio = no.lineno - 1
    fim = no.end_lineno
    trecho = "".join(linhas[inicio:fim])

    atualizado = substituir_unico(trecho, POST_OLD, POST_NEW, "validação POST de Ajudante")
    atualizado = substituir_unico(atualizado, GET_OLD, GET_NEW, "listagem GET de Ajudantes")

    if atualizado == trecho:
        print("Blueprint 17.2G já aplicada em app.py.")
        return

    linhas[inicio:fim] = [atualizado]
    source_atualizado = "".join(linhas)
    ast.parse(source_atualizado, filename=str(APP))
    APP.write_text(source_atualizado, encoding="utf-8", newline="\n")
    print("Blueprint 17.2G aplicada: lançamento de ajudante usa vínculo AJUDANTE ativo.")


if __name__ == "__main__":
    main()
