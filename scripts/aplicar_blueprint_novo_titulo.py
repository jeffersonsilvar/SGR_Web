from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP_PY = ROOT / "app.py"

ROTA_PATTERN = re.compile(
    r"\n@app\.route\('/financeiro/titulos/novo', methods=\['GET', 'POST'\]\)\n"
    r"@login_required\n"
    r"@perfis_permitidos\('Administrador', 'Operacional', 'Financeiro'\)\n"
    r"def novo_titulo_financeiro\(\):.*?"
    r"(?=\n@app\.route\()",
    re.DOTALL,
)

ANTIGO = "novo_titulo_financeiro"
NOVO = "financeiro.novo_titulo_financeiro"


def atualizar_referencia(path):
    if not path.exists():
        return
    texto = path.read_text(encoding="utf-8")
    total = texto.count(f"'{ANTIGO}'") + texto.count(f'"{ANTIGO}"')
    if not total:
        return
    texto = texto.replace(f"'{ANTIGO}'", f"'{NOVO}'")
    texto = texto.replace(f'"{ANTIGO}"', f'"{NOVO}"')
    path.write_text(texto, encoding="utf-8")
    print(f"[ok] {path.relative_to(ROOT)}: {total} referência(s)")


def main():
    if not APP_PY.exists():
        raise SystemExit("Execute o script na raiz do repositório.")

    backup = APP_PY.with_suffix(".py.novo-titulo-backup")
    shutil.copy2(APP_PY, backup)
    print(f"[ok] Backup criado: {backup.name}")

    texto = APP_PY.read_text(encoding="utf-8")
    novo_texto, quantidade = ROTA_PATTERN.subn("\n", texto, count=1)
    if quantidade != 1:
        raise SystemExit(
            "A rota GET/POST /financeiro/titulos/novo não foi localizada "
            "de forma única. O app.py não foi alterado."
        )

    APP_PY.write_text(novo_texto, encoding="utf-8")
    print("[ok] Rota GET/POST removida do app.py")

    atualizar_referencia(APP_PY)

    arquivos = [
        ROOT / "templates" / "base.html",
        ROOT / "templates" / "financeiro_titulos.html",
        ROOT / "templates" / "financeiro_titulo_form.html",
    ]
    for arquivo in arquivos:
        atualizar_referencia(arquivo)

    print("\nMigração aplicada.")
    print("Execute:")
    print("  python -m py_compile app_modules/financeiro/routes.py")
    print("  python -m pytest")


if __name__ == "__main__":
    main()
