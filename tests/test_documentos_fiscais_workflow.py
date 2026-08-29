from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_endpoints_workflow_documental_registrados(app):
    regras = {regra.endpoint: regra.rule for regra in app.url_map.iter_rules()}
    assert regras["documentos.marcar_documento_em_analise"] == "/documentos-fiscais/<int:id>/marcar-analise"
    assert regras["documentos.aprovar_documento_fiscal"] == "/documentos-fiscais/<int:id>/aprovar"
    assert regras["documentos.recusar_documento_fiscal"] == "/documentos-fiscais/<int:id>/recusar"
    assert regras["documentos.gerar_titulo_documento_fiscal"] == "/documentos-fiscais/<int:id>/gerar-titulo"


def test_workflow_exige_fluxo_documental_antes_do_titulo():
    fonte = (ROOT / "app_modules" / "documentos" / "workflow.py").read_text(encoding="utf-8")

    assert '"analise": {"Recebido": "Em análise"}' in fonte
    assert '"aprovar": {"Em análise": "Aprovado"}' in fonte
    assert '"recusar": {"Recebido": "Recusado", "Em análise": "Recusado"}' in fonte
    assert 'documento.get("status_documento") != "Aprovado"' in fonte


def test_geracao_de_titulo_usa_motor_financeiro_sem_pagamento_direto():
    fonte = (ROOT / "app_modules" / "documentos" / "workflow.py").read_text(encoding="utf-8")

    assert "INSERT INTO titulos_financeiros" in fonte
    assert "'PAGAR', 'DOCUMENTO_FISCAL'" in fonte
    assert "'Aberto'" in fonte
    assert "INSERT INTO movimentacoes_caixa" not in fonte
    assert "confirmar-pagamento" not in fonte
    assert "estornar-pagamento" not in fonte


def test_geracao_de_titulo_e_idempotente_e_transacional():
    fonte = (ROOT / "app_modules" / "documentos" / "workflow.py").read_text(encoding="utf-8")

    assert "FOR UPDATE" in fonte
    assert 'documento.get("titulo_financeiro_id")' in fonte
    assert "AND origem = 'DOCUMENTO_FISCAL'" in fonte
    assert "AND origem_id = %s" in fonte
    assert "DOCUMENTO_FISCAL_TITULO_VINCULADO" in fonte
    assert "con.rollback()" in fonte
    assert "con.commit()" in fonte


def test_titulo_exige_pessoa_e_vencimento_valido():
    fonte = (ROOT / "app_modules" / "documentos" / "workflow.py").read_text(encoding="utf-8")

    assert "data_vencimento = _data_iso" in fonte
    assert "Informe uma data de vencimento válida" in fonte
    assert 'not documento.get("pessoa_id")' in fonte
    assert "Vincule uma Pessoa/Fornecedor" in fonte
    assert "data_vencimento < emissao" in fonte


def test_workflow_registra_auditoria_documental():
    fonte = (ROOT / "app_modules" / "documentos" / "workflow.py").read_text(encoding="utf-8")

    assert "DOCUMENTO_FISCAL_EM_ANALISE" in fonte
    assert "DOCUMENTO_FISCAL_APROVADO" in fonte
    assert "DOCUMENTO_FISCAL_RECUSADO" in fonte
    assert "DOCUMENTO_FISCAL_TITULO_GERADO" in fonte
    assert "INSERT INTO auditoria_financeira" in fonte
    assert "'DOCUMENTOS_FISCAIS'" in fonte


def test_template_expoe_fluxo_e_integracao_financeira():
    template = (ROOT / "templates" / "documento_fiscal_detalhes.html").read_text(encoding="utf-8")

    assert "Marcar em análise" in template
    assert "Aprovar" in template
    assert "Recusar" in template
    assert "Gerar título a pagar" in template
    assert "data_vencimento" in template
    assert "financeiro.detalhes_titulo_financeiro" in template
    assert "Pagamento continua sendo responsabilidade exclusiva do Financeiro" in template


def test_migracao_16_3_habilita_edicao_sem_tocar_legado():
    migration = (ROOT / "database" / "migrations" / "20260826_blueprint16_3_fluxo_documental_titulos.sql").read_text(encoding="utf-8")

    assert "'editar'" in migration
    assert "pp.acao_codigo = 'visualizar'" in migration
    assert "motorista_notas_fiscais" not in migration
    assert "DROP" not in migration
    assert "DELETE" not in migration
