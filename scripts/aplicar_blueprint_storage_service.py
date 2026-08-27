from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import obter_conexao


MIGRATION = ROOT / "database" / "migrations" / "20260827_blueprint16_4b_storage_service.sql"


def _split_sql(texto):
    comandos = []
    atual = []
    for linha in texto.splitlines():
        if linha.strip().startswith("--"):
            continue
        atual.append(linha)
        if linha.rstrip().endswith(";"):
            comando = "\n".join(atual).strip().rstrip(";").strip()
            if comando:
                comandos.append(comando)
            atual = []
    resto = "\n".join(atual).strip()
    if resto:
        comandos.append(resto)
    return comandos


def main():
    con = obter_conexao()
    if con is None:
        raise SystemExit("[erro] Não foi possível conectar ao banco.")
    cur = con.cursor()
    try:
        texto = MIGRATION.read_text(encoding="utf-8")
        for comando in _split_sql(texto):
            cur.execute(comando)
        con.commit()
        print("[ok] Migração Blueprint 16.4B aplicada.")
    except Exception:
        con.rollback()
        raise
    finally:
        cur.close()
        con.close()


if __name__ == "__main__":
    main()
