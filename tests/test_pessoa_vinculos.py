import pytest

from app_modules.pessoas.vinculos import (
    TIPOS_VINCULO,
    condicao_sql_vinculo_pessoa,
    listar_vinculos_pessoa,
    normalizar_tipo_vinculo,
    pessoa_possui_vinculo,
    sincronizar_vinculos_por_cadastro,
    tipos_vinculo_derivados,
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


class CursorSincronizacaoFake:
    def __init__(self, existentes=None):
        self.existentes = existentes or []
        self.execucoes = []

    def execute(self, sql, params):
        self.execucoes.append((sql, params))

    def fetchall(self):
        return self.existentes


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


def test_derivacao_motorista_e_ajudante_permitem_multiplos_papeis():
    assert tipos_vinculo_derivados("Prestador de Serviço", "Motorista") == {
        "MOTORISTA",
        "PRESTADOR_SERVICO",
    }
    assert tipos_vinculo_derivados("Prestador de Serviço", "Motorista e Ajudante") == {
        "AJUDANTE",
        "MOTORISTA",
        "PRESTADOR_SERVICO",
    }


def test_derivacao_fornecedor_funcionario_e_outros_nao_cria_papel_indevido():
    assert tipos_vinculo_derivados("Fornecedor") == {"FORNECEDOR"}
    assert tipos_vinculo_derivados("Funcionário") == {"FUNCIONARIO"}
    assert tipos_vinculo_derivados("Funcionario") == {"FUNCIONARIO"}
    assert tipos_vinculo_derivados("Outros") == set()


def test_pessoa_inativa_nao_mantem_vinculo_derivado_ativo():
    assert tipos_vinculo_derivados(
        "Prestador de Serviço",
        "Motorista",
        status_cadastro="Inativo",
    ) == set()


def test_sincronizacao_cria_papeis_ausentes_sem_commit_proprio():
    cur = CursorSincronizacaoFake()

    resultado = sincronizar_vinculos_por_cadastro(
        cur,
        empresa_id=2,
        pessoa_id=15,
        tipo_cadastro="Prestador de Serviço",
        tipo_prestador="Motorista",
    )

    inserts = [(sql, params) for sql, params in cur.execucoes if "INSERT INTO pessoa_vinculos" in sql]
    assert resultado["desejados"] == ("MOTORISTA", "PRESTADOR_SERVICO")
    assert resultado["ativados"] == ("MOTORISTA", "PRESTADOR_SERVICO")
    assert len(inserts) == 2
    assert {params[2] for _, params in inserts} == {"MOTORISTA", "PRESTADOR_SERVICO"}


def test_sincronizacao_reativa_e_inativa_sem_apagar_historico():
    cur = CursorSincronizacaoFake(
        existentes=[
            {"id": 31, "tipo_vinculo": "MOTORISTA", "status_vinculo": "Inativo"},
            {"id": 32, "tipo_vinculo": "AJUDANTE", "status_vinculo": "Ativo"},
            {"id": 33, "tipo_vinculo": "PRESTADOR_SERVICO", "status_vinculo": "Ativo"},
        ]
    )

    resultado = sincronizar_vinculos_por_cadastro(
        cur,
        empresa_id=2,
        pessoa_id=15,
        tipo_cadastro="Prestador de Serviço",
        tipo_prestador="Motorista",
    )

    sql_total = "\n".join(sql for sql, _ in cur.execucoes)
    assert resultado["ativados"] == ("MOTORISTA",)
    assert resultado["inativados"] == ("AJUDANTE",)
    assert resultado["mantidos"] == ("PRESTADOR_SERVICO",)
    assert "DELETE FROM pessoa_vinculos" not in sql_total
    assert "SET status_vinculo = 'Ativo'" in sql_total
    assert "SET status_vinculo = 'Inativo'" in sql_total


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
