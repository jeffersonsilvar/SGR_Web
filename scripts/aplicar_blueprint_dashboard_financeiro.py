from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP_PY = ROOT / "app.py"

ROTA_PATTERN = re.compile(
    r"\n@app\.route\('/financeiro/dashboard'\)\n"
    r"@login_required\n"
    r"@perfis_permitidos\('Administrador', 'Operacional', 'Financeiro', 'Consulta'\)\n"
    r"def financeiro_dashboard\(\):.*?"
    r"(?=\n@app\.route\()",
    re.DOTALL,
)

ANTIGO = "financeiro_dashboard"
NOVO = "financeiro.financeiro_dashboard"


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

    backup = APP_PY.with_suffix(".py.dashboard-backup")
    shutil.copy2(APP_PY, backup)
    print(f"[ok] Backup criado: {backup.name}")

    texto = APP_PY.read_text(encoding="utf-8")
    novo_texto, quantidade = ROTA_PATTERN.subn("\n", texto, count=1)

    if quantidade != 1:
        raise SystemExit(
            "A rota GET do Dashboard Financeiro não foi localizada "
            "de forma única. O app.py não foi alterado."
        )

    dependencias = {
        "validar_data_iso": "validar_data_iso",
        "financeiro_base_origens": "financeiro_base_origens",
    }

    marcador = (
        '    "registrar_auditoria_financeira": '
        'registrar_auditoria_financeira,\n'
    )
    if marcador not in novo_texto:
        raise SystemExit(
            "Dicionário financeiro_services não localizado."
        )

    insercoes = ""
    for chave, funcao in dependencias.items():
        if f'"{chave}"' not in novo_texto:
            insercoes += f'    "{chave}": {funcao},\n'

    if insercoes:
        novo_texto = novo_texto.replace(
            marcador,
            marcador + insercoes,
            1,
        )

    APP_PY.write_text(novo_texto, encoding="utf-8")
    print("[ok] Rota GET removida do app.py")
    print("[ok] Dependências do dashboard registradas")

    atualizar_referencia(APP_PY)

    arquivos = [
        ROOT / "templates" / "base.html",
        ROOT / "templates" / "financeiro_dashboard.html",
        ROOT / "templates" / "financeiro_titulos.html",
        ROOT / "templates" / "financeiro_contas_caixa.html",
        ROOT / "templates" / "financeiro_movimentacoes_caixa.html",
        ROOT / "templates" / "financeiro_conciliacao_caixa.html",
    ]
    for arquivo in arquivos:
        atualizar_referencia(arquivo)

    print("\nMigração aplicada.")
    print("Execute: python -m pytest")


if __name__ == "__main__":
    main()
