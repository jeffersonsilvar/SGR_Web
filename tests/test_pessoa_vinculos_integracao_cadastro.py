from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def _source():
    return APP.read_text(encoding="utf-8")


def test_cadastro_pessoa_sincroniza_vinculos_antes_do_commit():
    source = _source()

    trecho = source[source.index("def cadastro_pessoa():"):source.index("def visualizar_pessoas():")]
    assert "pessoa_id = cur.lastrowid" in trecho
    assert "sincronizar_vinculos_por_cadastro(" in trecho
    assert "empresa_id=empresa_id_destino" in trecho
    assert "pessoa_id=pessoa_id" in trecho
    assert trecho.index("sincronizar_vinculos_por_cadastro(") < trecho.index("con.commit()")


def test_edicao_pessoa_sincroniza_vinculos_antes_do_commit():
    source = _source()

    trecho = source[source.index("def editar_pessoa(id):"):source.index("def excluir_pessoa(id):")]
    assert "sincronizar_vinculos_por_cadastro(" in trecho
    assert "pessoa_id=id" in trecho
    assert "status_cadastro=status_cadastro" in trecho
    assert trecho.index("sincronizar_vinculos_por_cadastro(") < trecho.index("con.commit()")


def test_troca_de_empresa_move_vinculos_e_usuario_na_mesma_transacao():
    source = _source()

    trecho = source[source.index("def editar_pessoa(id):"):source.index("def excluir_pessoa(id):")]
    assert "UPDATE pessoa_vinculos SET empresa_id = %s WHERE pessoa_id = %s AND empresa_id = %s" in trecho
    assert "UPDATE usuarios SET empresa_id = %s WHERE pessoa_id = %s" in trecho
    assert trecho.index("UPDATE pessoa_vinculos SET empresa_id") < trecho.index("sincronizar_vinculos_por_cadastro(")
    assert trecho.index("sincronizar_vinculos_por_cadastro(") < trecho.index("con.commit()")
