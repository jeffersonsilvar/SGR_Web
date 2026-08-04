from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP_PY = ROOT / "app.py"

OLD_ROUTE_PATTERN = re.compile(
    r"\n@app\.route\('/financeiro/contas-caixa', methods=\['GET'\]\)"
    r".*?"
    r"\n(?=@app\.route\('/financeiro/contas-caixa/nova')",
    re.DOTALL,
)

REGISTER_BLOCK = """
# ==========================================================
# BLUEPRINT PILOTO — FINANCEIRO / CONTAS CAIXA
# ==========================================================
from app_modules.financeiro import criar_financeiro_blueprint

financeiro_services = {
    "login_required": login_required,
    "perfis_permitidos": perfis_permitidos,
    "usuario_eh_super_admin_global": usuario_eh_super_admin_global,
    "carregar_contas_caixa_financeiro": carregar_contas_caixa_financeiro,
    "obter_conexao": obter_conexao,
    "calcular_saldo_conta_caixa": calcular_saldo_conta_caixa,
    "converter_decimal": converter_decimal,
    "fechar_cursor_conexao": fechar_cursor_conexao,
}

app.extensions["financeiro_services"] = financeiro_services
app.register_blueprint(criar_financeiro_blueprint(financeiro_services))
"""


def atualizar_arquivo(path: Path, antigo: str, novo: str):
    texto = path.read_text(encoding="utf-8")
    if antigo not in texto:
        print(f"[aviso] Referência não encontrada em {path}: {antigo}")
        return
    path.write_text(texto.replace(antigo, novo), encoding="utf-8")
    print(f"[ok] Atualizado: {path}")


def main():
    if not APP_PY.exists():
        raise SystemExit("Execute este script na raiz do repositório.")

    backup = APP_PY.with_suffix(".py.blueprint-backup")
    shutil.copy2(APP_PY, backup)
    print(f"[ok] Backup criado: {backup.name}")

    texto = APP_PY.read_text(encoding="utf-8")
    novo_texto, quantidade = OLD_ROUTE_PATTERN.subn("\n", texto, count=1)

    if quantidade != 1:
        raise SystemExit(
            "Não foi possível localizar de forma única a rota atual. "
            "O app.py não foi alterado."
        )

    marcador = "\n\nif __name__ == '__main__':"
    if marcador not in novo_texto:
        raise SystemExit("Marcador final do app.py não encontrado.")

    if "criar_financeiro_blueprint" not in novo_texto:
        novo_texto = novo_texto.replace(
            marcador,
            "\n" + REGISTER_BLOCK + marcador,
            1,
        )

    novo_texto = novo_texto.replace(
        "'financeiro_contas_caixa'",
        "'financeiro.financeiro_contas_caixa'",
    )

    APP_PY.write_text(novo_texto, encoding="utf-8")
    print("[ok] app.py atualizado")

    templates = [
        ROOT / "templates" / "base.html",
        ROOT / "templates" / "financeiro_conta_caixa_form.html",
        ROOT / "templates" / "financeiro_titulos.html",
    ]

    for template in templates:
        if template.exists():
            atualizar_arquivo(
                template,
                "'financeiro_contas_caixa'",
                "'financeiro.financeiro_contas_caixa'",
            )

    print("\nMigração aplicada.")
    print("Execute: python -m pytest")
    print("Em caso de erro, restaure app.py.blueprint-backup.")


if __name__ == "__main__":
    main()
