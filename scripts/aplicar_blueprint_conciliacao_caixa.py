from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP_PY = ROOT / "app.py"

ROTA_GET_PATTERN = re.compile(
    r"\n@app\.route\('/financeiro/conciliacao-caixa', methods=\['GET'\]\)"
    r".*?"
    r"(?=\n@app\.route\('/financeiro/conciliacao-caixa/acao', methods=\['POST'\]\))",
    re.DOTALL,
)

ANTIGO = "financeiro_conciliacao_caixa"
NOVO = "financeiro.financeiro_conciliacao_caixa"


def atualizar_referencia(path):
    if not path.exists():
        return

    texto = path.read_text(encoding="utf-8")
    ocorrencias = texto.count(f"'{ANTIGO}'") + texto.count(f'"{ANTIGO}"')
    if not ocorrencias:
        return

    texto = texto.replace(f"'{ANTIGO}'", f"'{NOVO}'")
    texto = texto.replace(f'"{ANTIGO}"', f'"{NOVO}"')
    path.write_text(texto, encoding="utf-8")
    print(f"[ok] {path.relative_to(ROOT)}: {ocorrencias} referência(s)")


def main():
    if not APP_PY.exists():
        raise SystemExit("Execute o script na raiz do repositório.")

    backup = APP_PY.with_suffix(".py.conciliacao-backup")
    shutil.copy2(APP_PY, backup)
    print(f"[ok] Backup criado: {backup.name}")

    texto = APP_PY.read_text(encoding="utf-8")
    novo_texto, quantidade = ROTA_GET_PATTERN.subn("\n", texto, count=1)

    if quantidade != 1:
        raise SystemExit(
            "A rota GET de Conciliação de Caixa não foi localizada "
            "de forma única. O app.py não foi alterado."
        )

    APP_PY.write_text(novo_texto, encoding="utf-8")
    print("[ok] Rota GET removida do app.py")

    # Atualiza menu padrão e redirects da ação POST.
    atualizar_referencia(APP_PY)

    arquivos = [
        ROOT / "templates" / "base.html",
        ROOT / "templates" / "financeiro_conciliacao_caixa.html",
        ROOT / "templates" / "financeiro_dashboard.html",
    ]
    for arquivo in arquivos:
        atualizar_referencia(arquivo)

    print("\nMigração aplicada.")
    print("A rota POST /financeiro/conciliacao-caixa/acao permanece no app.py.")
    print("Execute: python -m pytest")


if __name__ == "__main__":
    main()
