from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

OLD = """        if uso == 'motorista':\n            query += f\" AND {condicao_sql_motorista_prestador('p')}\"\n        elif uso == 'ajudante':\n"""

NEW = """        if uso == 'motorista':\n            from app_modules.pessoas.vinculos import condicao_sql_vinculo_pessoa\n\n            query += \" AND \" + condicao_sql_vinculo_pessoa(\n                alias_pessoa='p',\n                tipo_vinculo='MOTORISTA',\n                alias_vinculo='pv_motorista',\n            )\n        elif uso == 'ajudante':\n"""


def main():
    source = APP.read_text(encoding="utf-8")

    if NEW in source:
        print("Blueprint 17.2 já aplicada em app.py.")
        return

    ocorrencias = source.count(OLD)
    if ocorrencias != 1:
        raise RuntimeError(
            f"Bloco esperado da busca de Motoristas encontrado {ocorrencias} vez(es); "
            "nenhuma alteração foi feita."
        )

    atualizado = source.replace(OLD, NEW, 1)
    ast.parse(atualizado, filename=str(APP))
    APP.write_text(atualizado, encoding="utf-8", newline="\n")
    print("Blueprint 17.2 aplicada: uso=motorista agora consulta pessoa_vinculos.")


if __name__ == "__main__":
    main()
