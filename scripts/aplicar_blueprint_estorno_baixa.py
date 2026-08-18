from pathlib import Path
import ast
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

ENDPOINT_ANTIGO = "estornar_baixa_titulo_financeiro"
ENDPOINT_NOVO = "financeiro.estornar_baixa_titulo_financeiro"
NOVA_DEPENDENCIA = "aplicar_estorno_em_documento_motorista_e_rotas"


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


def adicionar_dependencia_servicos(texto):
    linha = f'    "{NOVA_DEPENDENCIA}": {NOVA_DEPENDENCIA},\n'
    if linha in texto:
        return texto

    ancora = '    "aplicar_baixa_em_documento_motorista_e_rotas": aplicar_baixa_em_documento_motorista_e_rotas,\n'
    if ancora not in texto:
        raise SystemExit(
            "Âncora do financeiro_services não encontrada. "
            "O app.py não foi alterado."
        )

    return texto.replace(ancora, ancora + linha, 1)


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

    backup = ROOT / "app.py.estorno-baixa-backup"
    shutil.copy2(APP, backup)
    print(f"[ok] Backup criado: {backup.name}")

    original = APP.read_text(encoding="utf-8")

    # Toda a validação ocorre em memória antes da gravação.
    novo = remover_funcao_top_level(
        original,
        "estornar_baixa_titulo_financeiro",
    )
    novo = adicionar_dependencia_servicos(novo)

    APP.write_text(novo, encoding="utf-8")
    print("[ok] Somente a rota estornar_baixa_titulo_financeiro foi removida do app.py")
    print("[ok] Helper de sincronização de estorno adicionado ao financeiro_services")

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
