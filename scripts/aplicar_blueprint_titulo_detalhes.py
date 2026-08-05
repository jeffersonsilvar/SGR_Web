from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP_PY = ROOT / "app.py"

ROTA_PATTERN = re.compile(
    r"\n@app\.route\('/financeiro/titulos/<int:id>', methods=\['GET'\]\)\n"
    r"@login_required\n"
    r"@perfis_permitidos\('Administrador', 'Operacional', 'Financeiro', 'Consulta'\)\n"
    r"def detalhes_titulo_financeiro\(id\):.*?"
    r"(?=\n@app\.route\()",
    re.DOTALL,
)

ANTIGO = "detalhes_titulo_financeiro"
NOVO = "financeiro.detalhes_titulo_financeiro"


def atualizar_referencias(path):
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

    backup = APP_PY.with_suffix(".py.titulo-detalhes-backup")
    shutil.copy2(APP_PY, backup)
    print(f"[ok] Backup criado: {backup.name}")

    texto = APP_PY.read_text(encoding="utf-8")
    novo_texto, quantidade = ROTA_PATTERN.subn("\n", texto, count=1)
    if quantidade != 1:
        raise SystemExit("A rota GET de detalhes do título não foi localizada de forma única.")

    marcador = '    "carregar_pessoas_financeiro": carregar_pessoas_financeiro,\n'
    if marcador not in novo_texto:
        raise SystemExit("Dicionário financeiro_services não localizado.")

    dependencias = {
        "carregar_parametros_financeiros_empresa": "carregar_parametros_financeiros_empresa",
        "parametro_bool": "parametro_bool",
    }
    insercoes = ""
    for chave, funcao in dependencias.items():
        if f'"{chave}"' not in novo_texto:
            insercoes += f'    "{chave}": {funcao},\n'
    if insercoes:
        novo_texto = novo_texto.replace(marcador, marcador + insercoes, 1)

    APP_PY.write_text(novo_texto, encoding="utf-8")
    print("[ok] Rota GET removida do app.py")
    print("[ok] Dependências registradas")

    atualizar_referencias(APP_PY)
    for pasta in (ROOT / "templates", ROOT / "app_modules"):
        for path in pasta.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".html"}:
                atualizar_referencias(path)

    print("\nMigração aplicada.")
    print("Execute: python -m pytest")


if __name__ == "__main__":
    main()
