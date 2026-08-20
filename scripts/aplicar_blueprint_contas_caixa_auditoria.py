from __future__ import annotations

import ast
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP_PY = ROOT / "app.py"

FUNCOES_REMOVER = {
    "nova_conta_caixa",
    "editar_conta_caixa",
    "financeiro_auditoria",
}

SUBSTITUICOES_ENDPOINTS = {
    "'nova_conta_caixa'": "'financeiro.nova_conta_caixa'",
    '"nova_conta_caixa"': '"financeiro.nova_conta_caixa"',
    "'editar_conta_caixa'": "'financeiro.editar_conta_caixa'",
    '"editar_conta_caixa"': '"financeiro.editar_conta_caixa"',
    "'financeiro_auditoria'": "'financeiro.financeiro_auditoria'",
    '"financeiro_auditoria"': '"financeiro.financeiro_auditoria"',
}

TEMPLATES = (
    ROOT / "templates" / "base.html",
    ROOT / "templates" / "dashboard.html",
    ROOT / "templates" / "relatorios_central.html",
    ROOT / "templates" / "relatorios_financeiro.html",
    ROOT / "templates" / "financeiro_contas_caixa.html",
    ROOT / "templates" / "financeiro_conta_caixa_form.html",
)


def remover_funcoes_top_level(texto: str) -> tuple[str, list[str]]:
    arvore = ast.parse(texto)
    linhas = texto.splitlines(keepends=True)
    intervalos = []
    encontradas = []

    for node in arvore.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name not in FUNCOES_REMOVER:
            continue

        inicio = node.lineno
        if node.decorator_list:
            inicio = min(decorator.lineno for decorator in node.decorator_list)
        fim = node.end_lineno
        intervalos.append((inicio, fim))
        encontradas.append(node.name)

    faltantes = sorted(FUNCOES_REMOVER - set(encontradas))
    if faltantes:
        raise RuntimeError(
            "Não foi possível localizar as funções esperadas no app.py: "
            + ", ".join(faltantes)
        )

    for inicio, fim in sorted(intervalos, reverse=True):
        del linhas[inicio - 1 : fim]

    return "".join(linhas), sorted(encontradas)


def substituir_endpoints(texto: str) -> str:
    for antigo, novo in SUBSTITUICOES_ENDPOINTS.items():
        texto = texto.replace(antigo, novo)
    return texto


def atualizar_template(path: Path) -> bool:
    if not path.exists():
        return False
    texto = path.read_text(encoding="utf-8")
    novo = substituir_endpoints(texto)
    if novo == texto:
        return False
    path.write_text(novo, encoding="utf-8")
    return True


def main() -> None:
    if not APP_PY.exists():
        raise SystemExit("Execute este script na raiz do repositório SGR Web.")

    backup = APP_PY.with_name("app.py.blueprint15-backup")
    shutil.copy2(APP_PY, backup)
    print(f"[ok] Backup criado: {backup.name}")

    texto_original = APP_PY.read_text(encoding="utf-8")
    try:
        texto_novo, removidas = remover_funcoes_top_level(texto_original)
        texto_novo = substituir_endpoints(texto_novo)
        ast.parse(texto_novo)
    except Exception:
        if backup.exists():
            shutil.copy2(backup, APP_PY)
        raise

    APP_PY.write_text(texto_novo, encoding="utf-8")
    print("[ok] Rotas antigas removidas do app.py via AST: " + ", ".join(removidas))

    atualizados = []
    for template in TEMPLATES:
        if atualizar_template(template):
            atualizados.append(str(template.relative_to(ROOT)))

    if atualizados:
        print("[ok] Endpoints atualizados em templates:")
        for item in atualizados:
            print(f"     - {item}")
    else:
        print("[ok] Templates já utilizavam os endpoints do Blueprint.")

    print("[ok] Blueprint 15 aplicado.")
    print("\nValide com:")
    print("  python -m py_compile app.py")
    print("  python -m py_compile app_modules/financeiro/contas_caixa_auditoria.py")
    print("  python -m flask --app app routes | Select-String 'contas-caixa|auditoria'")
    print("  python -m pytest")
    print("\nNão versione app.py.blueprint15-backup.")


if __name__ == "__main__":
    main()
