TIPOS_VINCULO = frozenset(
    {
        "AJUDANTE",
        "FORNECEDOR",
        "FUNCIONARIO",
        "MOTORISTA",
        "PRESTADOR_SERVICO",
    }
)


def normalizar_tipo_vinculo(tipo_vinculo):
    valor = (tipo_vinculo or "").strip().upper().replace(" ", "_")
    if valor not in TIPOS_VINCULO:
        raise ValueError("Tipo de vínculo inválido.")
    return valor


def condicao_sql_vinculo_pessoa(*, alias_pessoa="p", tipo_vinculo, alias_vinculo="pv"):
    """Retorna uma condição SQL EXISTS para filtrar Pessoas por vínculo ativo.

    A função retorna apenas SQL estrutural. ``tipo_vinculo`` é validado contra o
    catálogo fechado de papéis do domínio antes de ser incorporado à expressão.
    Os aliases também são validados para evitar composição arbitrária de SQL.
    """
    tipo = normalizar_tipo_vinculo(tipo_vinculo)

    for alias in (alias_pessoa, alias_vinculo):
        if not alias or not str(alias).replace("_", "").isalnum():
            raise ValueError("Alias SQL inválido.")

    return f"""
        EXISTS (
            SELECT 1
            FROM pessoa_vinculos {alias_vinculo}
            WHERE {alias_vinculo}.empresa_id = {alias_pessoa}.empresa_id
              AND {alias_vinculo}.pessoa_id = {alias_pessoa}.id
              AND {alias_vinculo}.tipo_vinculo = '{tipo}'
              AND {alias_vinculo}.status_vinculo = 'Ativo'
        )
    """.strip()


def listar_vinculos_pessoa(cur, *, empresa_id, pessoa_id, somente_ativos=True):
    if not empresa_id or not pessoa_id:
        return []

    sql = """
        SELECT tipo_vinculo
        FROM pessoa_vinculos
        WHERE empresa_id = %s
          AND pessoa_id = %s
    """
    params = [int(empresa_id), int(pessoa_id)]

    if somente_ativos:
        sql += " AND status_vinculo = 'Ativo'"

    sql += " ORDER BY tipo_vinculo"
    cur.execute(sql, params)
    registros = cur.fetchall() or []
    return [registro["tipo_vinculo"] for registro in registros]


def pessoa_possui_vinculo(cur, *, empresa_id, pessoa_id, tipo_vinculo):
    if not empresa_id or not pessoa_id:
        return False

    tipo = normalizar_tipo_vinculo(tipo_vinculo)
    cur.execute(
        """
        SELECT 1
        FROM pessoa_vinculos
        WHERE empresa_id = %s
          AND pessoa_id = %s
          AND tipo_vinculo = %s
          AND status_vinculo = 'Ativo'
        LIMIT 1
        """,
        (int(empresa_id), int(pessoa_id), tipo),
    )
    return cur.fetchone() is not None
