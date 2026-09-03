from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

OLD = """query_motoristas = '''
                           SELECT id, nome_completo
                           FROM pessoas
                           WHERE tipo_cadastro = 'Motorista'
                             AND status_cadastro = 'Ativo' \\
                           '''
        params_motoristas = []

        if is_super_admin:
            if empresa_id_filtro and empresa_id_filtro.isdigit():
                query_motoristas += ' AND empresa_id = %s'
                params_motoristas.append(int(empresa_id_filtro))
        else:
            query_motoristas += ' AND empresa_id = %s'
            params_motoristas.append(empresa_logada_id)

        query_motoristas += ' ORDER BY nome_completo ASC'
        cur.execute(query_motoristas, params_motoristas)
        motoristas = cur.fetchall()"""

NEW = """from app_modules.pessoas.vinculos import condicao_sql_vinculo_pessoa

        condicao_motorista_financeiro = condicao_sql_vinculo_pessoa(
            alias_pessoa='p',
            tipo_vinculo='MOTORISTA',
            alias_vinculo='pv_motorista_financeiro_nf',
        )
        query_motoristas = f'''\n                           SELECT p.id, p.nome_completo\n                           FROM pessoas p\n                           WHERE p.status_cadastro = 'Ativo'\n                             AND {condicao_motorista_financeiro} \\\n                           '''
        params_motoristas = []

        if is_super_admin:
            if empresa_id_filtro and empresa_id_filtro.isdigit():
                query_motoristas += ' AND p.empresa_id = %s'
                params_motoristas.append(int(empresa_id_filtro))
        else:
            query_motoristas += ' AND p.empresa_id = %s'
            params_motoristas.append(empresa_logada_id)

        query_motoristas += ' ORDER BY p.nome_completo ASC'
        cur.execute(query_motoristas, params_motoristas)
        motoristas = cur.fetchall()"""


def localizar_funcao(source: str):
    arvore = ast.parse(source, filename=str(APP))
    for no in arvore.body:
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)) and no.name == "financeiro_nfs_motoristas":
            return no
    raise RuntimeError("Função financeiro_nfs_motoristas não encontrada; nenhuma alteração foi feita.")


def main():
    source = APP.read_text(encoding="utf-8")
    no = localizar_funcao(source)
    linhas = source.splitlines(keepends=True)
    inicio = no.lineno - 1
    fim = no.end_lineno
    trecho = "".join(linhas[inicio:fim])

    if NEW in trecho:
        print("Blueprint 17.3A já aplicada em app.py.")
        return

    ocorrencias = trecho.count(OLD)
    if ocorrencias != 1:
        raise RuntimeError(
            f"Bloco esperado do filtro de Motoristas encontrado {ocorrencias} vez(es) dentro de financeiro_nfs_motoristas; "
            "nenhuma alteração foi feita."
        )

    trecho_atualizado = trecho.replace(OLD, NEW, 1)
    linhas[inicio:fim] = [trecho_atualizado]
    atualizado = "".join(linhas)
    ast.parse(atualizado, filename=str(APP))
    APP.write_text(atualizado, encoding="utf-8", newline="\n")
    print("Blueprint 17.3A aplicada: painel financeiro lista Motoristas por vínculo MOTORISTA ativo.")


if __name__ == "__main__":
    main()
