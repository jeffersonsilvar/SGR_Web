from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

OLD = """                cur.execute(\"\"\"\n                        SELECT id\n                        FROM pessoas\n                        WHERE id = %s\n                          AND empresa_id = %s\n                          AND status_cadastro = 'Ativo'\n                          AND (tipo_cadastro = 'Motorista' OR (tipo_cadastro = 'Prestador de Serviço' AND COALESCE(tipo_prestador, '') IN ('Motorista', 'Motorista e Ajudante'))) LIMIT 1\n                        \"\"\", (motorista_id, empresa_id))\n\n            if not cur.fetchone():\n"""

NEW = """                from app_modules.pessoas.vinculos import condicao_sql_vinculo_pessoa\n\n                condicao_motorista = condicao_sql_vinculo_pessoa(\n                    alias_pessoa='p',\n                    tipo_vinculo='MOTORISTA',\n                    alias_vinculo='pv_motorista_edicao_rota',\n                )\n                cur.execute(f\"\"\"\n                        SELECT p.id\n                        FROM pessoas p\n                        WHERE p.id = %s\n                          AND p.empresa_id = %s\n                          AND p.status_cadastro = 'Ativo'\n                          AND {condicao_motorista}\n                        LIMIT 1\n                        \"\"\", (motorista_id, empresa_id))\n\n            if not cur.fetchone():\n"""


def main():
    source = APP.read_text(encoding="utf-8")

    if NEW in source:
        print("Blueprint 17.2E já aplicada em app.py.")
        return

    ocorrencias = source.count(OLD)
    if ocorrencias != 1:
        raise RuntimeError(
            f"Bloco esperado da validação de Motorista na edição de rota encontrado {ocorrencias} vez(es); "
            "nenhuma alteração foi feita."
        )

    atualizado = source.replace(OLD, NEW, 1)
    ast.parse(atualizado, filename=str(APP))
    APP.write_text(atualizado, encoding="utf-8", newline="\n")
    print("Blueprint 17.2E aplicada: edição de rota valida vínculo MOTORISTA ativo.")


if __name__ == "__main__":
    main()
