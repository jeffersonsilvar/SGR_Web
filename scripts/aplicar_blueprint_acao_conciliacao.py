from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP_PY = ROOT / "app.py"

ROTA_POST_PATTERN = re.compile(
    r"\n@app\.route\('/financeiro/conciliacao-caixa/acao', methods=\['POST'\]\)"
    r".*?"
    r"(?=\n@app\.route\('/financeiro/contas-caixa/nova', methods=\['GET', 'POST'\]\))",
    re.DOTALL,
)

ANTIGO = "financeiro_conciliacao_caixa_acao"
NOVO = "financeiro.financeiro_conciliacao_caixa_acao"


def atualizar_arquivo(path):
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

    backup = APP_PY.with_suffix(".py.conciliacao-acao-backup")
    shutil.copy2(APP_PY, backup)
    print(f"[ok] Backup criado: {backup.name}")

    texto = APP_PY.read_text(encoding="utf-8")
    novo_texto, quantidade = ROTA_POST_PATTERN.subn("\n", texto, count=1)

    if quantidade != 1:
        raise SystemExit(
            "A rota POST de Conciliação de Caixa não foi localizada "
            "de forma única. O app.py não foi alterado."
        )

    dependencia = (
        '    "registrar_auditoria_financeira": '
        'registrar_auditoria_financeira,\n'
    )
    if '"registrar_auditoria_financeira"' not in novo_texto:
        marcador = (
            '    "carregar_empresas_ativas": carregar_empresas_ativas,\n'
        )
        if marcador not in novo_texto:
            raise SystemExit(
                "Dicionário financeiro_services não localizado."
            )
        novo_texto = novo_texto.replace(
            marcador,
            marcador + dependencia,
            1,
        )

    APP_PY.write_text(novo_texto, encoding="utf-8")
    print("[ok] Rota POST removida do app.py")
    print("[ok] Dependência de auditoria registrada")

    atualizar_arquivo(APP_PY)

    arquivos = [
        ROOT / "templates" / "base.html",
        ROOT / "templates" / "financeiro_conciliacao_caixa.html",
    ]
    for arquivo in arquivos:
        atualizar_arquivo(arquivo)

    print("\nMigração aplicada.")
    print("Execute: python -m pytest")


if __name__ == "__main__":
    main()
