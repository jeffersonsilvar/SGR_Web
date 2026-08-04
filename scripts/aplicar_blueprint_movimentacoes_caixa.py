from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP_PY = ROOT / "app.py"
ROUTES_PY = ROOT / "app_modules" / "financeiro" / "routes.py"

OLD_ROUTE_PATTERN = re.compile(
    r"\n@app\.route\('/financeiro/movimentacoes-caixa', methods=\['GET'\]\)"
    r".*?"
    r"\n(?=@app\.route\('/financeiro/conciliacao-caixa')",
    re.DOTALL,
)


def substituir_endpoint_em_arquivo(path, antigo, novo):
    if not path.exists():
        return

    texto = path.read_text(encoding="utf-8")
    if antigo not in texto:
        return

    path.write_text(texto.replace(antigo, novo), encoding="utf-8")
    print(f"[ok] Endpoint atualizado em {path}")


def main():
    if not APP_PY.exists():
        raise SystemExit("Execute o script na raiz do repositório.")

    if not ROUTES_PY.exists():
        raise SystemExit(
            "Copie app_modules/financeiro/routes.py antes de executar."
        )

    backup = APP_PY.with_suffix(".py.movimentacoes-backup")
    shutil.copy2(APP_PY, backup)
    print(f"[ok] Backup criado: {backup.name}")

    texto = APP_PY.read_text(encoding="utf-8")
    novo_texto, quantidade = OLD_ROUTE_PATTERN.subn("\n", texto, count=1)

    if quantidade != 1:
        raise SystemExit(
            "A rota antiga de Movimentações Caixa não foi localizada "
            "de forma única. O app.py não foi alterado."
        )

    # Adiciona a nova dependência ao dicionário já existente.
    trecho = (
        '    "carregar_empresas_ativas": carregar_empresas_ativas,\n'
    )
    if '"carregar_empresas_ativas"' not in novo_texto:
        marcador = (
            '    "fechar_cursor_conexao": fechar_cursor_conexao,\n'
        )
        if marcador not in novo_texto:
            raise SystemExit(
                "Não foi localizado o dicionário financeiro_services."
            )
        novo_texto = novo_texto.replace(
            marcador,
            marcador + trecho,
            1,
        )

    novo_texto = novo_texto.replace(
        "'financeiro_movimentacoes_caixa'",
        "'financeiro.financeiro_movimentacoes_caixa'",
    )

    APP_PY.write_text(novo_texto, encoding="utf-8")
    print("[ok] app.py atualizado")

    arquivos = [
        ROOT / "templates" / "base.html",
        ROOT / "templates" / "financeiro_contas_caixa.html",
        ROOT / "templates" / "financeiro_movimentacoes_caixa.html",
        ROOT / "templates" / "financeiro_titulos.html",
    ]

    for arquivo in arquivos:
        substituir_endpoint_em_arquivo(
            arquivo,
            "'financeiro_movimentacoes_caixa'",
            "'financeiro.financeiro_movimentacoes_caixa'",
        )

    print("\nMigração aplicada.")
    print("Execute: python -m pytest")


if __name__ == "__main__":
    main()
