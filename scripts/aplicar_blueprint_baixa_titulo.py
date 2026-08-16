from pathlib import Path
import ast
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

DEPENDENCIAS = [
    "buscar_movimentacoes_baixa_nao_estornadas",
    "moeda_br",
    "salvar_comprovante_baixa_titulo",
    "aplicar_baixa_em_documento_motorista_e_rotas",
]

ENDPOINT_ANTIGO = "baixar_titulo_financeiro"
ENDPOINT_NOVO = "financeiro.baixar_titulo_financeiro"


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

    # Remove somente o bloco AST da função e seus decorators.
    del linhas[inicio - 1:fim]

    return "".join(linhas)


def adicionar_dependencias_servicos(texto):
    ancora = '    "parametro_bool": parametro_bool,\n'
    if ancora not in texto:
        raise SystemExit(
            "Âncora do dicionário financeiro_services não encontrada. "
            "O app.py não foi alterado."
        )

    novas = []
    for nome in DEPENDENCIAS:
        linha = f'    "{nome}": {nome},\n'
        if linha not in texto:
            novas.append(linha)

    if novas:
        texto = texto.replace(ancora, ancora + "".join(novas), 1)

    return texto


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
        print(f"[ok] Referências atualizadas: {path.relative_to(ROOT)}")


def main():
    if not APP.exists():
        raise SystemExit("Execute este script na raiz do repositório.")

    backup = ROOT / "app.py.baixa-titulo-backup"
    shutil.copy2(APP, backup)
    print(f"[ok] Backup criado: {backup.name}")

    original = APP.read_text(encoding="utf-8")

    # Faz todas as validações em memória antes de gravar.
    novo = remover_funcao_top_level(original, "baixar_titulo_financeiro")
    novo = adicionar_dependencias_servicos(novo)

    APP.write_text(novo, encoding="utf-8")
    print("[ok] Somente a rota baixar_titulo_financeiro foi removida do app.py")
    print("[ok] Dependências da baixa adicionadas ao financeiro_services")

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
