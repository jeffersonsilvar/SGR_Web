from __future__ import annotations


STATUS_NF_BLOQUEIAM_REENVIO = (
    "Enviada",
    "Em análise",
    "Aprovada",
    "Pagamento solicitado",
    "Pagamento confirmado",
)

STATUS_NF_LIBERAM_REENVIO = (
    "Recusada",
    "Estornada",
    "Cancelada",
    "Invalidada",
    "Substituída",
)


def status_nf_bloqueia_reenvio(status_nf: str | None) -> bool:
    """Retorna True somente quando existe documento vigente que bloqueia nova NFS-e."""
    status = str(status_nf or "").strip()
    return status in STATUS_NF_BLOQUEIAM_REENVIO


def status_nf_exige_novo_documento(status_nf: str | None) -> bool:
    """Indica quando um reenvio deve criar outro registro e preservar o histórico.

    Documentos encerrados, recusados ou substituídos nunca são reativados nem
    sobrescritos pelo novo XML. Eles continuam disponíveis para auditoria.
    """
    status = str(status_nf or "").strip()
    return status in STATUS_NF_LIBERAM_REENVIO


def clausula_sql_status_bloqueante(alias: str = "nf") -> str:
    """Cláusula SQL compatível com MySQL 5.6 para a regra de documento vigente."""
    valores = ", ".join(f"'{status}'" for status in STATUS_NF_BLOQUEIAM_REENVIO)
    return f"{alias}.status_nf IN ({valores})"
