from __future__ import annotations

import os
from datetime import datetime

from app_modules.storage import StorageService


def armazenar_xml_portal_prestador(
    cur,
    caminho_absoluto,
    *,
    empresa_id,
    motorista_id,
    origem_id,
    nome_original,
    criado_por_usuario_id=None,
):
    """Armazena o XML/NFS-e do Portal do Prestador no StorageService.

    O arquivo escrito pelo fluxo legado passa a ser apenas temporário. Não existe
    fallback local silencioso: se o provider falhar, a exceção sobe para o fluxo
    chamador, que deve fazer rollback da operação documental.
    """
    if not caminho_absoluto or not os.path.exists(caminho_absoluto):
        raise FileNotFoundError("Arquivo temporário do Portal do Prestador não localizado.")

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
            pessoa_id=int(motorista_id) if motorista_id else None,
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
