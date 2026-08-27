from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

MARCADOR = '''app.extensions["documentos_services"] = documentos_services
app.register_blueprint(criar_documentos_blueprint(documentos_services))


if __name__ == '__main__':
    app.run(debug=False, port=8080)
'''

SUBSTITUTO = '''app.extensions["documentos_services"] = documentos_services
app.register_blueprint(criar_documentos_blueprint(documentos_services))


# ==========================================================
# BLUEPRINT 16.4B — INTEGRAÇÕES / HEALTH CHECK DO STORAGE
# ==========================================================
from app_modules.integracoes import criar_integracoes_blueprint

integracoes_services = {
    "login_required": login_required,
    "perfis_permitidos": perfis_permitidos,
    "obter_conexao": obter_conexao,
}

app.extensions["integracoes_services"] = integracoes_services
app.register_blueprint(criar_integracoes_blueprint(integracoes_services))


if __name__ == '__main__':
    app.run(debug=False, port=8080)
'''


def main():
    texto = APP.read_text(encoding="utf-8")
    if 'app.register_blueprint(criar_integracoes_blueprint(integracoes_services))' in texto:
        print("[ok] Blueprint de Integrações já registrado.")
        return
    if MARCADOR not in texto:
        raise SystemExit("[erro] Marcador esperado não encontrado em app.py. Nenhuma alteração realizada.")
    backup = APP.with_name("app.py.blueprint16-storage-backup")
    backup.write_text(texto, encoding="utf-8")
    APP.write_text(texto.replace(MARCADOR, SUBSTITUTO, 1), encoding="utf-8")
    print("[ok] Blueprint de Integrações registrado em app.py.")
    print(f"[info] Backup local criado: {backup.name} (não versionar).")


if __name__ == "__main__":
    main()
