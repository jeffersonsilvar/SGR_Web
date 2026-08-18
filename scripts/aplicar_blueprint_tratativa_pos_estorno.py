from pathlib import Path
import ast
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

ENDPOINT_ANTIGO = "tratar_pos_estorno_titulo_financeiro"
ENDPOINT_NOVO = "financeiro.tratar_pos_estorno_titulo_financeiro"


def remover_funcao_top_level(texto, nome):
    arvore = ast.parse(texto)
    linhas = texto.splitlines(keepends=True)

    alvo = None
    for no in arvore.body:
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)) and no.name == nome:
            alvo = no
            break

    if alvo is None:
        raise SystemExit(f"Função {nome} não encontrada no app.py.")

    inicio = alvo.lineno
    if alvo.decorator_list:
        inicio = min(dec.lineno for dec in alvo.decorator_list)
    fim = alvo.end_lineno

    del linhas[inicio - 1:fim]
    return "".join(linhas)


def atualizar_endpoint(path):
    if not path.exists():
        return

    texto = path.read_text(encoding="utf-8")
    novo = texto.replace(
        f"'{ENDPOINT_ANTIGO}'",
        f"'{ENDPOINT_NOVO}'",
    ).replace(
        f'"{ENDPOINT_ANTIGO}"',
        f'"{ENDPOINT_NOVO}"',
    )

    if novo != texto:
        path.write_text(novo, encoding="utf-8")
        print(f"[ok] Referência atualizada: {path.relative_to(ROOT)}")


def main():
    if not APP.exists():
        raise SystemExit("Execute este script na raiz do repositório.")

    backup = ROOT / "app.py.tratativa-pos-estorno-backup"
    shutil.copy2(APP, backup)
    print(f"[ok] Backup criado: {backup.name}")

    original = APP.read_text(encoding="utf-8")

    # Remove exclusivamente o bloco AST da rota.
    novo = remover_funcao_top_level(
        original,
        "tratar_pos_estorno_titulo_financeiro",
    )

    APP.write_text(novo, encoding="utf-8")
    print(
        "[ok] Somente a rota tratar_pos_estorno_titulo_financeiro "
        "foi removida do app.py"
    )

    atualizar_endpoint(APP)

    for relativo in [
        "templates/base.html",
        "templates/financeiro_titulo_detalhes.html",
    ]:
        atualizar_endpoint(ROOT / relativo)

    print("\nMigração aplicada.")
    print("Execute:")
    print("  python -m py_compile app.py")
    print("  python -m py_compile app_modules/financeiro/routes.py")
    print("  python -m pytest")


if __name__ == "__main__":
    main()
