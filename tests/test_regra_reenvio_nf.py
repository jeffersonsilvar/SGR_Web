from pathlib import Path

from app_modules.documentos.regra_reenvio_nf import (
    STATUS_NF_BLOQUEIAM_REENVIO,
    STATUS_NF_LIBERAM_REENVIO,
    clausula_sql_status_bloqueante,
    status_nf_bloqueia_reenvio,
    status_nf_exige_novo_documento,
)


ROOT = Path(__file__).resolve().parents[1]


def test_status_vigentes_bloqueiam_reenvio():
    for status in (
        "Enviada",
        "Em análise",
        "Aprovada",
        "Pagamento solicitado",
        "Pagamento confirmado",
    ):
        assert status in STATUS_NF_BLOQUEIAM_REENVIO
        assert status_nf_bloqueia_reenvio(status) is True


def test_status_encerrados_liberam_reenvio():
    for status in ("Recusada", "Estornada", "Cancelada", "Invalidada", "Substituída"):
        assert status in STATUS_NF_LIBERAM_REENVIO
        assert status_nf_bloqueia_reenvio(status) is False


def test_status_historicos_exigem_novo_registro():
    for status in STATUS_NF_LIBERAM_REENVIO:
        assert status_nf_exige_novo_documento(status) is True


def test_status_vigentes_nao_sao_candidatos_a_reutilizacao():
    for status in STATUS_NF_BLOQUEIAM_REENVIO:
        assert status_nf_exige_novo_documento(status) is False


def test_clausula_sql_eh_explicita_e_nao_usa_diferente_de_recusada():
    clausula = clausula_sql_status_bloqueante("nf")
    assert "nf.status_nf IN" in clausula
    assert "Pagamento confirmado" in clausula
    assert "Recusada" not in clausula
    assert "Estornada" not in clausula
    assert "<>" not in clausula


def test_app_consolidado_usa_predicado_explicito_de_nf_vigente():
    fonte = (ROOT / "app.py").read_text(encoding="utf-8")
    predicado = "nf.status_nf IN ('Enviada', 'Em análise', 'Aprovada', 'Pagamento solicitado', 'Pagamento confirmado')"
    assert fonte.count(predicado) >= 2
    assert "nf.status_nf <> 'Recusada'" not in fonte


def test_app_consolidado_preserva_nf_recusada_como_historico():
    fonte = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "if status_xml_existente == 'Recusada':" in fonte
    assert "nf_reenvio_recusada_id = None" in fonte
    assert "nf_reenvio_recusada_id = nf_existente.get('id')" not in fonte
