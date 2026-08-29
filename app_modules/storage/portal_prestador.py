from __future__ import annotations

import os
from datetime import datetime

from app_modules.storage import StorageService


def _resolver_pessoa_prestador(cur, *, empresa_id, pessoa_id=None, motorista_id=None):
    """Resolve a identidade mestre do prestador.

    ``motorista_id`` é aceito apenas como alias legado porque, historicamente, o
    Portal do Motorista usa o próprio id da tabela ``pessoas`` nesse campo. Novos
    fluxos devem informar ``pessoa_id``.
    """
    candidato = pessoa_id if pessoa_id is not None else motorista_id
    if not candidato:
        raise ValueError("Pessoa/Prestador não informado para o armazenamento do documento.")

    cur.execute(
        """
        SELECT id, nome_completo
        FROM pessoas
        WHERE id = %s
          AND empresa_id = %s
        LIMIT 1
        """,
        (int(candidato), int(empresa_id)),
    )
    pessoa = cur.fetchone() or {}
    if not pessoa.get("id"):
        raise ValueError("Pessoa/Prestador não pertence à empresa informada.")
    return int(pessoa["id"]), pessoa.get("nome_completo")


def armazenar_xml_portal_prestador(
    cur,
    caminho_absoluto,
    *,
    empresa_id,
    origem_id,
    nome_original,
    pessoa_id=None,
    motorista_id=None,
    criado_por_usuario_id=None,
):
    """Armazena o XML/NFS-e do Portal do Prestador no StorageService.

    Pessoa é a identidade principal. ``motorista_id`` permanece somente como
    alias de compatibilidade com o fluxo legado até a futura migração do Portal
    do Motorista para Portal do Prestador.

    O arquivo escrito pelo fluxo legado passa a ser apenas temporário. Não existe
    fallback local silencioso: se o provider falhar, a exceção sobe para o fluxo
    chamador, que deve fazer rollback da operação documental.
    """
    if not caminho_absoluto or not os.path.exists(caminho_absoluto):
        raise FileNotFoundError("Arquivo temporário do Portal do Prestador não localizado.")

    pessoa_id_resolvida, _ = _resolver_pessoa_prestador(
        cur,
        empresa_id=empresa_id,
        pessoa_id=pessoa_id,
        motorista_id=motorista_id,
    )

    cur.execute(
        """
        SELECT COALESCE(NULLIF(nome_fantasia, ''), NULLIF(razao_social, ''), CONCAT('Empresa_', id)) AS nome
        FROM empresas
        WHERE id = %s
        LIMIT 1
        """,
        (empresa_id,),
    )
    empresa = cur.fetchone() or {}
    empresa_nome = empresa.get("nome") or f"Empresa_{empresa_id}"

    storage = StorageService()
    try:
        info = storage.armazenar_arquivo(
            cur,
            caminho_local=caminho_absoluto,
            empresa_id=int(empresa_id),
            empresa_nome=empresa_nome,
            categoria="Documentos_Fiscais",
            subcategoria="NFSe_Prestador",
            pasta_registro=f"nf_prestador_{int(origem_id)}",
            origem="XML_MOTORISTA",
            origem_id=int(origem_id),
            tipo_arquivo="XML_NF_MOTORISTA",
            nome_original=nome_original or os.path.basename(caminho_absoluto),
            pessoa_id=pessoa_id_resolvida,
            criado_por_usuario_id=criado_por_usuario_id,
            data_referencia=datetime.now(),
        )
        return info["url_interna"]
    finally:
        # O caminho local existe apenas para compatibilidade com o fluxo legado.
        try:
            os.remove(caminho_absoluto)
        except OSError:
            pass
