from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

CREATE_OLD = """                        ))\n\n            con.commit()\n\n            flash(\"Cadastro realizado com sucesso!\", \"success\")\n"""

CREATE_NEW = """                        ))\n\n            pessoa_id = cur.lastrowid\n            from app_modules.pessoas.vinculos import sincronizar_vinculos_por_cadastro\n\n            sincronizar_vinculos_por_cadastro(\n                cur,\n                empresa_id=empresa_id_destino,\n                pessoa_id=pessoa_id,\n                tipo_cadastro=tipo_cadastro,\n                tipo_prestador=tipo_prestador,\n                status_cadastro=status_cadastro,\n            )\n\n            con.commit()\n\n            flash(\"Cadastro realizado com sucesso!\", \"success\")\n"""

EDIT_OLD = """            if cur.rowcount == 0:\n                con.rollback()\n                flash(\"Nenhuma alteração realizada ou cadastro não pertence à empresa logada.\", \"warning\")\n                return redirect(url_for('visualizar_pessoas'))\n\n            # Se a troca de empresa foi permitida por não haver movimentação, sincroniza usuário vinculado.\n            if empresa_original != empresa_id_destino:\n                cur.execute(\"UPDATE usuarios SET empresa_id = %s WHERE pessoa_id = %s\", (empresa_id_destino, id))\n\n            con.commit()\n"""

EDIT_NEW = """            if cur.rowcount == 0:\n                con.rollback()\n                flash(\"Nenhuma alteração realizada ou cadastro não pertence à empresa logada.\", \"warning\")\n                return redirect(url_for('visualizar_pessoas'))\n\n            # Se a Pessoa mudou de empresa e a troca foi permitida, os vínculos acompanham\n            # a identidade mestre antes da sincronização dos papéis atuais.\n            if empresa_original != empresa_id_destino:\n                cur.execute(\n                    \"UPDATE pessoa_vinculos SET empresa_id = %s WHERE pessoa_id = %s AND empresa_id = %s\",\n                    (empresa_id_destino, id, empresa_original),\n                )\n                cur.execute(\"UPDATE usuarios SET empresa_id = %s WHERE pessoa_id = %s\", (empresa_id_destino, id))\n\n            from app_modules.pessoas.vinculos import sincronizar_vinculos_por_cadastro\n\n            sincronizar_vinculos_por_cadastro(\n                cur,\n                empresa_id=empresa_id_destino,\n                pessoa_id=id,\n                tipo_cadastro=tipo_cadastro,\n                tipo_prestador=tipo_prestador,\n                status_cadastro=status_cadastro,\n            )\n\n            con.commit()\n"""


def substituir_unico(source: str, old: str, new: str, descricao: str) -> str:
    if new in source:
        return source
    ocorrencias = source.count(old)
    if ocorrencias != 1:
        raise RuntimeError(
            f"Bloco de {descricao} encontrado {ocorrencias} vez(es); nenhuma alteração foi feita."
        )
    return source.replace(old, new, 1)


def main():
    source = APP.read_text(encoding="utf-8")
    atualizado = substituir_unico(source, CREATE_OLD, CREATE_NEW, "cadastro de Pessoa")
    atualizado = substituir_unico(atualizado, EDIT_OLD, EDIT_NEW, "edição de Pessoa")

    if atualizado == source:
        print("Blueprint 17.2B já aplicada em app.py.")
        return

    ast.parse(atualizado, filename=str(APP))
    APP.write_text(atualizado, encoding="utf-8", newline="\n")
    print("Blueprint 17.2B aplicada: cadastro e edição sincronizam pessoa_vinculos.")


if __name__ == "__main__":
    main()
