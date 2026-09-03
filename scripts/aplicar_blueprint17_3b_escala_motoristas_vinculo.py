from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

OLD = """cur.execute(\"\"\"
                    SELECT mot.id                                              AS motorista_id,
                           mot.nome_completo                                   AS motorista_nome,
                           mot.cpf_cnpj                                        AS motorista_cpf_cnpj,
                           COALESCE(dm.status_disponibilidade, 'Sem resposta') AS status_disponibilidade,
                           dm.observacao                                       AS observacao_disponibilidade,
                           em.id                                               AS escala_id,
                           COALESCE(em.status_escala, 'Pendente')              AS status_escala,
                           COALESCE(em.status_presenca, 'Não se aplica')       AS status_presenca,
                           em.base_operacional_id,
                           em.base_operacao,
                           bo.nome_base                                        AS base_operacional_nome,
                           em.horario_apresentacao,
                           em.observacao_supervisor,
                           em.presenca_confirmada_em,
                           em.falta_automatica,
                           em.falta_marcada_em,
                           em.falta_motivo,
                           em.falta_revertida,
                           em.motivo_reversao,
                           em.data_reversao,
                           cem.data_ciencia,
                           cem.origem_ciencia
                    FROM pessoas mot
                             LEFT JOIN disponibilidade_motorista dm
                                       ON dm.empresa_id = mot.empresa_id
                                           AND dm.motorista_id = mot.id
                                           AND dm.data_disponibilidade = %s
                             LEFT JOIN escala_motorista em
                                       ON em.empresa_id = mot.empresa_id
                                           AND em.motorista_id = mot.id
                                           AND em.data_escala = %s
                             LEFT JOIN bases_operacionais bo
                                       ON bo.id = em.base_operacional_id
                                           AND bo.empresa_id = em.empresa_id
                             LEFT JOIN ciencia_escala_motorista cem
                                       ON cem.empresa_id = mot.empresa_id
                                           AND cem.motorista_id = mot.id
                                           AND cem.escala_id = em.id
                    WHERE mot.empresa_id = %s
                      AND mot.tipo_cadastro = 'Motorista'
                      AND mot.status_cadastro = 'Ativo'
                    ORDER BY mot.nome_completo ASC
                    \"\"\", (data_escala, data_escala, empresa_id))"""

NEW = """from app_modules.pessoas.vinculos import condicao_sql_vinculo_pessoa

        condicao_motorista_escala = condicao_sql_vinculo_pessoa(
            alias_pessoa='mot',
            tipo_vinculo='MOTORISTA',
            alias_vinculo='pv_motorista_escala_supervisor',
        )
        cur.execute(f\"\"\"
                    SELECT mot.id                                              AS motorista_id,
                           mot.nome_completo                                   AS motorista_nome,
                           mot.cpf_cnpj                                        AS motorista_cpf_cnpj,
                           COALESCE(dm.status_disponibilidade, 'Sem resposta') AS status_disponibilidade,
                           dm.observacao                                       AS observacao_disponibilidade,
                           em.id                                               AS escala_id,
                           COALESCE(em.status_escala, 'Pendente')              AS status_escala,
                           COALESCE(em.status_presenca, 'Não se aplica')       AS status_presenca,
                           em.base_operacional_id,
                           em.base_operacao,
                           bo.nome_base                                        AS base_operacional_nome,
                           em.horario_apresentacao,
                           em.observacao_supervisor,
                           em.presenca_confirmada_em,
                           em.falta_automatica,
                           em.falta_marcada_em,
                           em.falta_motivo,
                           em.falta_revertida,
                           em.motivo_reversao,
                           em.data_reversao,
                           cem.data_ciencia,
                           cem.origem_ciencia
                    FROM pessoas mot
                             LEFT JOIN disponibilidade_motorista dm
                                       ON dm.empresa_id = mot.empresa_id
                                           AND dm.motorista_id = mot.id
                                           AND dm.data_disponibilidade = %s
                             LEFT JOIN escala_motorista em
                                       ON em.empresa_id = mot.empresa_id
                                           AND em.motorista_id = mot.id
                                           AND em.data_escala = %s
                             LEFT JOIN bases_operacionais bo
                                       ON bo.id = em.base_operacional_id
                                           AND bo.empresa_id = em.empresa_id
                             LEFT JOIN ciencia_escala_motorista cem
                                       ON cem.empresa_id = mot.empresa_id
                                           AND cem.motorista_id = mot.id
                                           AND cem.escala_id = em.id
                    WHERE mot.empresa_id = %s
                      AND (
                            (mot.status_cadastro = 'Ativo' AND {condicao_motorista_escala})
                            OR em.id IS NOT NULL
                          )
                    ORDER BY mot.nome_completo ASC
                    \"\"\", (data_escala, data_escala, empresa_id))"""


def localizar_funcao(source: str):
    arvore = ast.parse(source, filename=str(APP))
    for no in arvore.body:
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)) and no.name == "carregar_escala_supervisor":
            return no
    raise RuntimeError("Função carregar_escala_supervisor não encontrada; nenhuma alteração foi feita.")


def main():
    source = APP.read_text(encoding="utf-8")
    no = localizar_funcao(source)
    linhas = source.splitlines(keepends=True)
    inicio = no.lineno - 1
    fim = no.end_lineno
    trecho = "".join(linhas[inicio:fim])

    if NEW in trecho:
        print("Blueprint 17.3B já aplicada em app.py.")
        return

    ocorrencias = trecho.count(OLD)
    if ocorrencias != 1:
        raise RuntimeError(
            f"Bloco esperado da escala encontrado {ocorrencias} vez(es) dentro de carregar_escala_supervisor; "
            "nenhuma alteração foi feita."
        )

    trecho_atualizado = trecho.replace(OLD, NEW, 1)
    linhas[inicio:fim] = [trecho_atualizado]
    atualizado = "".join(linhas)
    ast.parse(atualizado, filename=str(APP))
    APP.write_text(atualizado, encoding="utf-8", newline="\n")
    print("Blueprint 17.3B aplicada: escala usa vínculo MOTORISTA ativo e preserva registros já escalados.")


if __name__ == "__main__":
    main()
