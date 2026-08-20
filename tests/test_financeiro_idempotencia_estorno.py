from app_modules.financeiro.idempotencia_estorno import instalar_protecao_idempotencia_estorno


class CursorProtecao:
    def __init__(self, retornos=None):
        self.retornos = list(retornos or [])
        self.query = ""
        self.params = None

    def execute(self, query, params=None):
        self.query = query
        self.params = tuple(params or ())

    def fetchall(self):
        return self.retornos


def test_protecao_estorno_instala_helper_no_services():
    services = {"buscar_movimentacoes_baixa_nao_estornadas": lambda *args, **kwargs: ["legado"]}

    helper = instalar_protecao_idempotencia_estorno(services)

    assert services["buscar_movimentacoes_baixa_nao_estornadas"] is helper


def test_busca_baixa_ativa_trava_linhas_e_ignora_movimento_ja_estornado():
    services = {}
    helper = instalar_protecao_idempotencia_estorno(services)
    cursor = CursorProtecao([
        {
            "id": 28,
            "empresa_id": 2,
            "conta_caixa_id": 1,
            "titulo_financeiro_id": 16,
            "tipo_movimentacao": "SAIDA",
            "valor_movimentacao": 1130,
            "forma_pagamento": "PIX",
        }
    ])

    retorno = helper(cursor, titulo_id=16, empresa_id=2)

    assert retorno[0]["id"] == 28
    assert cursor.params == (16, 2)
    assert "FOR UPDATE" in cursor.query
    assert "m.estorno_de_movimentacao_id IS NULL" in cursor.query
    assert "NOT EXISTS" in cursor.query
    assert "est.estorno_de_movimentacao_id = m.id" in cursor.query
    assert "status_movimentacao" in cursor.query


def test_retentativa_sem_baixa_elegivel_nao_gera_nova_candidata():
    services = {}
    helper = instalar_protecao_idempotencia_estorno(services)
    cursor = CursorProtecao([])

    retorno = helper(cursor, titulo_id=16, empresa_id=2)

    assert retorno == []
    assert cursor.params == (16, 2)
