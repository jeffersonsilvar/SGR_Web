TIPOS_VINCULO = frozenset(
    {
        "AJUDANTE",
        "FORNECEDOR",
        "FUNCIONARIO",
        "MOTORISTA",
        "PRESTADOR_SERVICO",
    }
)

VINCULOS_GERENCIADOS_CADASTRO = frozenset(
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


def tipos_vinculo_derivados(tipo_cadastro, tipo_prestador=None, *, status_cadastro="Ativo"):
    """Deriva os vínculos gerenciados a partir dos campos legados de Pessoa.

    Durante a transição da Blueprint 17, ``tipo_cadastro`` e ``tipo_prestador``
    continuam sendo gravados pelo cadastro existente. Esta função traduz esses
    campos para os papéis independentes de ``pessoa_vinculos`` sem transformar
    acesso ao portal em papel operacional.
    """
    if (status_cadastro or "").strip() != "Ativo":
        return frozenset()

    cadastro = (tipo_cadastro or "").strip()
    prestador = (tipo_prestador or "").strip()
    vinculos = set()

    if cadastro == "Fornecedor":
        vinculos.add("FORNECEDOR")

    if cadastro in {"Funcionário", "Funcionario"}:
        vinculos.add("FUNCIONARIO")

    cadastro_prestador = cadastro in {
        "Prestador de Serviço",
        "Prestador de Servico",
        "Prestador",
        "Motorista",
        "Ajudante",
    }
    if cadastro_prestador:
        vinculos.add("PRESTADOR_SERVICO")

    if cadastro == "Motorista" and not prestador:
        prestador = "Motorista"
    elif cadastro == "Ajudante" and not prestador:
        prestador = "Ajudante"

    if cadastro_prestador and prestador in {"Motorista", "Motorista e Ajudante"}:
        vinculos.add("MOTORISTA")
    if cadastro_prestador and prestador in {"Ajudante", "Motorista e Ajudante"}:
        vinculos.add("AJUDANTE")

    return frozenset(vinculos)


def sincronizar_vinculos_por_cadastro(
    cur,
    *,
    empresa_id,
    pessoa_id,
    tipo_cadastro,
    tipo_prestador=None,
    status_cadastro="Ativo",
):
    """Sincroniza apenas os vínculos que pertencem ao cadastro legado de Pessoa.

    A função não faz ``commit``: criação/edição da Pessoa e sincronização dos
    vínculos devem permanecer na mesma transação do chamador. Vínculos removidos
    semanticamente são inativados, nunca apagados, e um vínculo já existente é
    reativado em vez de gerar uma nova linha.
    """
    if not empresa_id or not pessoa_id:
        raise ValueError("Empresa e Pessoa são obrigatórias para sincronizar vínculos.")

    desejados = tipos_vinculo_derivados(
        tipo_cadastro,
        tipo_prestador,
        status_cadastro=status_cadastro,
    )
    tipos_gerenciados = sorted(VINCULOS_GERENCIADOS_CADASTRO)
    placeholders = ", ".join(["%s"] * len(tipos_gerenciados))

    cur.execute(
        f"""
        SELECT id, tipo_vinculo, status_vinculo
        FROM pessoa_vinculos
        WHERE empresa_id = %s
          AND pessoa_id = %s
          AND tipo_vinculo IN ({placeholders})
        """,
        (int(empresa_id), int(pessoa_id), *tipos_gerenciados),
    )
    existentes = {
        registro["tipo_vinculo"]: registro
        for registro in (cur.fetchall() or [])
    }

    ativados = []
    inativados = []
    mantidos = []

    for tipo in tipos_gerenciados:
        registro = existentes.get(tipo)
        deve_estar_ativo = tipo in desejados

        if deve_estar_ativo and registro is None:
            cur.execute(
                """
                INSERT INTO pessoa_vinculos (
                    empresa_id, pessoa_id, tipo_vinculo, status_vinculo,
                    origem_vinculo, observacao
                )
                VALUES (%s, %s, %s, 'Ativo', 'CADASTRO_PESSOA', %s)
                """,
                (
                    int(empresa_id),
                    int(pessoa_id),
                    tipo,
                    "Sincronizado pelo cadastro/edição de Pessoa.",
                ),
            )
            ativados.append(tipo)
            continue

        if deve_estar_ativo and registro.get("status_vinculo") != "Ativo":
            cur.execute(
                """
                UPDATE pessoa_vinculos
                SET status_vinculo = 'Ativo'
                WHERE id = %s
                  AND empresa_id = %s
                  AND pessoa_id = %s
                """,
                (int(registro["id"]), int(empresa_id), int(pessoa_id)),
            )
            ativados.append(tipo)
            continue

        if not deve_estar_ativo and registro and registro.get("status_vinculo") == "Ativo":
            cur.execute(
                """
                UPDATE pessoa_vinculos
                SET status_vinculo = 'Inativo'
                WHERE id = %s
                  AND empresa_id = %s
                  AND pessoa_id = %s
                """,
                (int(registro["id"]), int(empresa_id), int(pessoa_id)),
            )
            inativados.append(tipo)
            continue

        if deve_estar_ativo and registro:
            mantidos.append(tipo)

    return {
        "desejados": tuple(sorted(desejados)),
        "ativados": tuple(ativados),
        "inativados": tuple(inativados),
        "mantidos": tuple(mantidos),
    }


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
