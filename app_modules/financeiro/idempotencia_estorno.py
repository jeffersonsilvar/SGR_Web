def instalar_protecao_idempotencia_estorno(services):
    """Substitui a busca de baixas ativas por uma leitura transacional idempotente.

    A mesma função é usada pela baixa e pelo estorno. No estorno, o FOR UPDATE
    serializa tentativas concorrentes sobre a movimentação original. O NOT EXISTS
    impede nova compensação quando uma tentativa anterior chegou a gravar o estorno
    mesmo que a resposta ao cliente tenha falhado por perda de conexão.
    """

    def buscar_movimentacoes_baixa_nao_estornadas(cur, *, titulo_id, empresa_id):
        cur.execute(
            """
            SELECT
                m.id,
                m.empresa_id,
                m.conta_caixa_id,
                m.titulo_financeiro_id,
                m.tipo_movimentacao,
                m.data_movimentacao,
                m.valor_movimentacao,
                m.forma_pagamento,
                m.historico,
                m.observacao,
                m.comprovante_url,
                m.status_movimentacao,
                m.usuario_criacao_id
            FROM movimentacoes_caixa m
            WHERE m.titulo_financeiro_id = %s
              AND m.empresa_id = %s
              AND COALESCE(m.status_movimentacao, 'Ativa') = 'Ativa'
              AND m.estorno_de_movimentacao_id IS NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM movimentacoes_caixa est
                  WHERE est.empresa_id = m.empresa_id
                    AND est.titulo_financeiro_id = m.titulo_financeiro_id
                    AND est.estorno_de_movimentacao_id = m.id
              )
            ORDER BY m.id ASC
            FOR UPDATE
            """,
            (titulo_id, empresa_id),
        )
        return cur.fetchall()

    services["buscar_movimentacoes_baixa_nao_estornadas"] = buscar_movimentacoes_baixa_nao_estornadas
    return buscar_movimentacoes_baixa_nao_estornadas
