import pytest

from app_modules.pessoas.vinculos import (
    TIPOS_VINCULO,
    condicao_sql_vinculo_pessoa,
    listar_vinculos_pessoa,
    normalizar_tipo_vinculo,
    pessoa_possui_vinculo,
)


class CursorFake:
    def __init__(self, *, fetchall=None, fetchone=None):
        self._fetchall = fetchall or []
        self._fetchone = fetchone
        self.sql = None
        self.params = None

    def execute(self, sql, params):
        self.sql = sql
        self.params = params

    def fetchall(self):
        return self._fetchall

    def fetchone(self):
        return self._fetchone


def test_tipos_vinculo_iniciais_sao_explicitos():
    assert TIPOS_VINCULO == {
        "AJUDANTE",
        "FORNECEDOR",
        "FUNCIONARIO",
        "MOTORISTA",
        "PRESTADOR_SERVICO",
    }


def test_normalizacao_nao_aceita_papel_desconhecido():
    assert normalizar_tipo_vinculo("motorista") == "MOTORISTA"
    assert normalizar_tipo_vinculo("prestador servico") == "PRESTADOR_SERVICO"

    with pytest.raises(ValueError):
        normalizar_tipo_vinculo("portal")


def test_condicao_sql_vinculo_filtra_mesma_empresa_pessoa_e_status_ativo():
    sql = condicao_sql_vinculo_pessoa(alias_pessoa="p", tipo_vinculo="motorista", alias_vinculo="pvm")

    assert "FROM pessoa_vinculos pvm" in sql
    assert "pvm.empresa_id = p.empresa_id" in sql
    assert "pvm.pessoa_id = p.id" in sql
    assert "pvm.tipo_vinculo = 'MOTORISTA'" in sql
    assert "pvm.status_vinculo = 'Ativo'" in sql


def test_condicao_sql_vinculo_rejeita_alias_arbitrario():
    with pytest.raises(ValueError):
        condicao_sql_vinculo_pessoa(alias_pessoa="p; DROP TABLE pessoas", tipo_vinculo="MOTORISTA")


def test_listagem_filtra_empresa_pessoa_e_status_ativo():
    cur = CursorFake(fetchall=[{"tipo_vinculo": "MOTORISTA"}, {"tipo_vinculo": "PRESTADOR_SERVICO"}])

    resultado = listar_vinculos_pessoa(cur, empresa_id=2, pessoa_id=3)

    assert resultado == ["MOTORISTA", "PRESTADOR_SERVICO"]
    assert "empresa_id = %s" in cur.sql
    assert "pessoa_id = %s" in cur.sql
    assert "status_vinculo = 'Ativo'" in cur.sql
    assert cur.params == [2, 3]


def test_listagem_pode_incluir_historico_sem_remover_isolamento_multiempresa():
    cur = CursorFake(fetchall=[{"tipo_vinculo": "MOTORISTA"}])

    listar_vinculos_pessoa(cur, empresa_id=2, pessoa_id=3, somente_ativos=False)

    assert "empresa_id = %s" in cur.sql
    assert "pessoa_id = %s" in cur.sql
    assert "status_vinculo = 'Ativo'" not in cur.sql


def test_verificacao_de_vinculo_exige_mesma_empresa_e_status_ativo():
    cur = CursorFake(fetchone={"1": 1})

    assert pessoa_possui_vinculo(cur, empresa_id=2, pessoa_id=3, tipo_vinculo="motorista") is True
    assert cur.params == (2, 3, "MOTORISTA")
    assert "status_vinculo = 'Ativo'" in cur.sql
    assert "LIMIT 1" in cur.sql


def test_sem_empresa_ou_pessoa_nao_consulta_banco():
    cur = CursorFake()

    assert listar_vinculos_pessoa(cur, empresa_id=None, pessoa_id=3) == []
    assert pessoa_possui_vinculo(cur, empresa_id=2, pessoa_id=None, tipo_vinculo="MOTORISTA") is False
    assert cur.sql is None
