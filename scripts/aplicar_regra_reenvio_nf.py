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


class SubstituirPredicado(ast.NodeTransformer):
    def __init__(self):
        self.funcoes = []
        self.alteracoes = 0

    def visit_FunctionDef(self, node):
        if node.name not in ALVOS:
            return node
        self.funcoes.append(node.name)
        self.generic_visit(node)
        self.funcoes.pop()
        return node

    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)

    def visit_Constant(self, node):
        if self.funcoes and isinstance(node.value, str) and PREDICADO_ANTIGO in node.value:
            node.value = node.value.replace(PREDICADO_ANTIGO, PREDICADO_NOVO)
            self.alteracoes += 1
        return node


def main():
    fonte = APP.read_text(encoding="utf-8")
    arvore = ast.parse(fonte)

    presentes = {
        node.name
        for node in arvore.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ALVOS
    }
    faltantes = ALVOS - presentes
    if faltantes:
        raise SystemExit(f"[erro] Funções não localizadas no app.py: {', '.join(sorted(faltantes))}")

    if PREDICADO_NOVO in fonte and PREDICADO_ANTIGO not in fonte:
        print("[ok] Regra de reenvio de NFS-e já aplicada.")
        return

    transformador = SubstituirPredicado()
    arvore = transformador.visit(arvore)
    ast.fix_missing_locations(arvore)

    if transformador.alteracoes < 2:
        raise SystemExit(
            f"[erro] Esperadas ao menos 2 substituições seguras; encontradas {transformador.alteracoes}. Nenhuma alteração gravada."
        )

    if not BACKUP.exists():
        BACKUP.write_text(fonte, encoding="utf-8")

    novo = ast.unparse(arvore) + "\n"
    ast.parse(novo)
    APP.write_text(novo, encoding="utf-8")
    print(f"[ok] Regra de reenvio aplicada em {transformador.alteracoes} pontos do fluxo.")
    print("[info] Somente NFs vigentes bloqueiam nova NFS-e; Recusada/Estornada deixam de bloquear a rota.")
    print(f"[info] Backup local: {BACKUP}")


if __name__ == "__main__":
    main()
