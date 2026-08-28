from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
BACKUP = ROOT / "app.py.historico-imutavel-nf-backup"
NOME_FUNCAO = "enviar_nf_motorista"
ALVO = "nf_reenvio_recusada_id = nf_existente.get('id')"
SUBSTITUTO = "nf_reenvio_recusada_id = None"


def main():
    fonte = APP.read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    funcao = next(
        (
            node
            for node in arvore.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == NOME_FUNCAO
        ),
        None,
    )
    if funcao is None:
        raise SystemExit(f"[erro] Função {NOME_FUNCAO} não localizada em app.py")

    linhas = fonte.splitlines(keepends=True)
    inicio = funcao.lineno - 1
    fim = funcao.end_lineno
    trecho = "".join(linhas[inicio:fim])

    if ALVO not in trecho:
        if SUBSTITUTO in trecho and "status_xml_existente == 'Recusada'" in trecho:
            print("[ok] Histórico imutável de NFS-e já aplicado.")
            return
        raise SystemExit("[erro] Bloco legado de reativação da NF recusada não foi localizado. Nenhuma alteração realizada.")

    if trecho.count(ALVO) != 1:
        raise SystemExit("[erro] Quantidade inesperada de pontos de reativação. Nenhuma alteração realizada.")

    trecho_novo = trecho.replace(ALVO, SUBSTITUTO, 1)
    novo = "".join(linhas[:inicio]) + trecho_novo + "".join(linhas[fim:])
    ast.parse(novo)

    if not BACKUP.exists():
        BACKUP.write_text(fonte, encoding="utf-8")

    APP.write_text(novo, encoding="utf-8")
    print("[ok] Reenvio de NF recusada agora cria novo registro e preserva o histórico anterior.")
    print("[info] Nenhuma NF recusada é reativada/sobrescrita pelo novo XML.")
    print(f"[info] Backup local: {BACKUP}")


if __name__ == "__main__":
    main()
