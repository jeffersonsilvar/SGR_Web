from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
BACKUP = ROOT / "app.py.regra-reenvio-nf-backup"
ALVOS = {"rota_tem_documento_ativo", "enviar_nf_motorista"}
PREDICADO_ANTIGO = "nf.status_nf <> 'Recusada'"
PREDICADO_NOVO = (
    "nf.status_nf IN ('Enviada', 'Em análise', 'Aprovada', "
    "'Pagamento solicitado', 'Pagamento confirmado')"
)


def main():
    fonte = APP.read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    linhas = fonte.splitlines(keepends=True)

    alvos = [
        node
        for node in arvore.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ALVOS
    ]
    presentes = {node.name for node in alvos}
    faltantes = ALVOS - presentes
    if faltantes:
        raise SystemExit(f"[erro] Funções não localizadas no app.py: {', '.join(sorted(faltantes))}")

    alteracoes = 0
    substituicoes = []
    for node in alvos:
        inicio = node.lineno - 1
        fim = node.end_lineno
        trecho = "".join(linhas[inicio:fim])
        quantidade = trecho.count(PREDICADO_ANTIGO)
        if quantidade:
            novo_trecho = trecho.replace(PREDICADO_ANTIGO, PREDICADO_NOVO)
            substituicoes.append((inicio, fim, novo_trecho))
            alteracoes += quantidade

    if not alteracoes:
        if PREDICADO_NOVO in fonte:
            print("[ok] Regra de reenvio de NFS-e já aplicada.")
            return
        raise SystemExit("[erro] Predicado legado não localizado nas funções esperadas. Nenhuma alteração gravada.")

    # Esperamos ao menos o helper central e a validação do POST do Portal.
    if alteracoes < 2:
        raise SystemExit(
            f"[erro] Esperadas ao menos 2 substituições seguras; encontradas {alteracoes}. Nenhuma alteração gravada."
        )

    if not BACKUP.exists():
        BACKUP.write_text(fonte, encoding="utf-8")

    # Substitui apenas os trechos delimitados pelo AST, de baixo para cima,
    # preservando todo o restante do app.py exatamente como está.
    for inicio, fim, novo_trecho in sorted(substituicoes, reverse=True):
        linhas[inicio:fim] = [novo_trecho]

    novo = "".join(linhas)
    ast.parse(novo)
    APP.write_text(novo, encoding="utf-8")
    print(f"[ok] Regra de reenvio aplicada em {alteracoes} pontos do fluxo.")
    print("[info] Somente NFs vigentes bloqueiam nova NFS-e; Recusada/Estornada deixam de bloquear a rota.")
    print(f"[info] Backup local: {BACKUP}")


if __name__ == "__main__":
    main()
