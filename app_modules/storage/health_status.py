from __future__ import annotations

from datetime import datetime
from typing import Optional


def registrar_status_storage(
    *,
    provider: str,
    status: str,
    mensagem: Optional[str] = None,
    latencia_ms: Optional[int] = None,
    verificado_em: Optional[datetime] = None,
) -> bool:
    """Persiste health do Storage em transacao separada e best-effort.

    O registro nao participa da transacao documental do chamador. Assim, uma
    falha real do provider continua visivel no painel mesmo quando o fluxo de
    negocio executa rollback. Qualquer falha ao registrar o proprio health e
    silenciosa para nunca substituir o erro original da operacao.
    """
    con = None
    cur = None
    try:
        from database import obter_conexao

        con = obter_conexao()
        if con is None:
            return False

        cur = con.cursor(dictionary=True)
        cur.execute(
            """
            INSERT INTO storage_health_status
                (provider, status_integracao, mensagem, latencia_ms, verificado_em)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                status_integracao = VALUES(status_integracao),
                mensagem = VALUES(mensagem),
                latencia_ms = VALUES(latencia_ms),
                verificado_em = VALUES(verificado_em),
                atualizado_em = CURRENT_TIMESTAMP
            """,
            (
                str(provider or "").strip().upper(),
                str(status or "").strip().upper(),
                mensagem,
                latencia_ms,
                verificado_em or datetime.now(),
            ),
        )
        con.commit()
        return True
    except Exception:
        try:
            if con is not None:
                con.rollback()
        except Exception:
            pass
        return False
    finally:
        try:
            if cur is not None:
                cur.close()
        except Exception:
            pass
        try:
            if con is not None:
                con.close()
        except Exception:
            pass
