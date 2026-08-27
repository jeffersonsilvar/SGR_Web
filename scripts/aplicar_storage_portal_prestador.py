from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
BACKUP = ROOT / "app.py.portal-prestador-storage-backup"
NOME_FUNCAO = "tentar_enviar_arquivo_google_drive"


NOVO_HELPER = '''def tentar_enviar_arquivo_google_drive(\n    cur,\n    caminho_absoluto,\n    caminho_relativo,\n    *,\n    empresa_id,\n    motorista_id=None,\n    origem,\n    origem_id=None,\n    tipo_arquivo,\n    nome_original=None,\n    mime_type=None,\n    criado_por_usuario_id=None,\n):\n    """Compatibilidade do Portal do Prestador com o StorageService obrigatório."""\n    if origem != 'XML_MOTORISTA':\n        raise RuntimeError(f"Origem de upload legado não migrada para StorageService: {origem}")\n\n    from app_modules.storage.portal_prestador import armazenar_xml_portal_prestador\n\n    return armazenar_xml_portal_prestador(\n        cur,\n        caminho_absoluto,\n        empresa_id=empresa_id,\n        motorista_id=motorista_id,\n        origem_id=origem_id,\n        nome_original=nome_original,\n        criado_por_usuario_id=criado_por_usuario_id,\n    )\n'''


def main():
    fonte = APP.read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    alvo = None
    for node in arvore.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == NOME_FUNCAO:
            alvo = node
            break

    if alvo is None:
        raise SystemExit(f"[erro] Função {NOME_FUNCAO} não localizada em app.py")

    linhas = fonte.splitlines(keepends=True)
    inicio = alvo.lineno - 1
    fim = alvo.end_lineno
    atual = "".join(linhas[inicio:fim])

    if "armazenar_xml_portal_prestador" in atual:
        print("[ok] Portal do Prestador já utiliza StorageService.")
        return

    if not BACKUP.exists():
        BACKUP.write_text(fonte, encoding="utf-8")

    novo = "".join(linhas[:inicio]) + NOVO_HELPER + "\n\n" + "".join(linhas[fim:])
    ast.parse(novo)
    APP.write_text(novo, encoding="utf-8")
    print("[ok] Portal do Prestador migrado para StorageService obrigatório.")
    print(f"[info] Backup local: {BACKUP}")


if __name__ == "__main__":
    main()
