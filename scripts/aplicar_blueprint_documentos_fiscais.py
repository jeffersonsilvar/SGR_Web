from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP_PY = ROOT / "app.py"

REGISTER_BLOCK = r'''

# ==========================================================
# BLUEPRINT 16.1 — CENTRAL DE DOCUMENTOS FISCAIS
# ==========================================================
from app_modules.documentos import criar_documentos_blueprint

documentos_services = {
    "login_required": login_required,
    "perfis_permitidos": perfis_permitidos,
    "usuario_eh_super_admin_global": usuario_eh_super_admin_global,
    "obter_conexao": obter_conexao,
}

app.extensions["documentos_services"] = documentos_services
app.register_blueprint(criar_documentos_blueprint(documentos_services))
'''


def main():
    if not APP_PY.exists():
        raise SystemExit("Execute este script na raiz do repositório.")

    texto = APP_PY.read_text(encoding="utf-8")
    if 'app.extensions["documentos_services"]' in texto:
        print("[ok] Blueprint de Documentos Fiscais já está registrado no app.py.")
        return

    marcador = "\n\nif __name__ == '__main__':"
    if marcador not in texto:
        raise SystemExit("Marcador final do app.py não encontrado. Nenhuma alteração foi feita.")

    backup = APP_PY.with_suffix(".py.blueprint16-backup")
    shutil.copy2(APP_PY, backup)
    print(f"[ok] Backup criado: {backup.name}")

    novo_texto = texto.replace(marcador, REGISTER_BLOCK + marcador, 1)
    APP_PY.write_text(novo_texto, encoding="utf-8")

    print("[ok] Blueprint 16.1 registrado no app.py.")
    print("\nValide com:")
    print("  python -m py_compile app.py")
    print("  python -m py_compile app_modules/documentos/routes.py")
    print("  python -m flask --app app routes | Select-String 'documentos-fiscais'")
    print("  python -m pytest")
    print("\nNão versione app.py.blueprint16-backup.")


if __name__ == "__main__":
    main()
