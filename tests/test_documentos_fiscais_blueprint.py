from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_endpoint_documentos_fiscais_registrado(app):
    regras = {regra.endpoint: regra.rule for regra in app.url_map.iter_rules()}
    assert regras["documentos.central_documentos_fiscais"] == "/documentos-fiscais"


def test_documentos_fiscais_exige_autenticacao(client):
    resposta = client.get("/documentos-fiscais", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_central_usa_fonte_legada_sem_migracao_destrutiva():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")

    assert "FROM motorista_notas_fiscais nf" in fonte
    assert "LEFT JOIN motorista_nf_rotas v" in fonte
    assert 'documento["tipo_documento"] = "NFS-e Prestador"' in fonte
    assert 'documento["origem_documento"]' in fonte


def test_central_respeita_isolamento_multiempresa():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")

    assert 'where.append("nf.empresa_id = %s")' in fonte
    assert "usuario_eh_super_admin_global" in fonte
    assert "empresa_id_filtro" in fonte


def test_central_nao_cria_pagamento_direto():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")

    assert "confirmar-pagamento" not in fonte
    assert "estornar-pagamento" not in fonte
    assert "INSERT INTO movimentacoes_caixa" not in fonte


def test_status_financeiros_legados_sao_projetados_como_documento_aprovado():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")

    assert '"Pagamento solicitado"' in fonte
    assert '"Pagamento confirmado"' in fonte
    assert '"Estornada"' in fonte
    assert "_status_documental_compativel" in fonte
    assert 'return "Aprovada"' in fonte
    assert 'documento["status_documento"]' in fonte


def test_filtro_da_central_usa_status_documental_e_preserva_status_legado():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")
    template = (ROOT / "templates" / "documentos_fiscais.html").read_text(encoding="utf-8")

    assert "STATUS_DOCUMENTAIS" in fonte
    assert "STATUS_LEGADOS_APROVADOS" in fonte
    assert "nf.status_nf IN" in fonte
    assert "Status documental" in template
    assert "Legado: {{ d.status_legado }}" in template


def test_template_deixa_clara_transicao_documental():
    template = (ROOT / "templates" / "documentos_fiscais.html").read_text(encoding="utf-8")

    assert "Documentos Fiscais" in template
    assert "NFS-e Prestadores" in template
    assert "NFS-e Administrativas" in template
    assert "NF-e Uso/Consumo" in template
    assert "Abrir legado" in template


def test_migracao_preserva_menu_legado():
    migration = (ROOT / "database" / "migrations" / "20260825_blueprint16_documentos_fiscais.sql").read_text(encoding="utf-8")

    assert "documentos.central_documentos_fiscais" in migration
    assert "financeiro_nfs_motoristas" in migration
    assert "DELETE FROM sistema_menus" not in migration
    assert "DROP" not in migration


def test_registrador_nao_remove_rotas_legadas():
    fonte = (ROOT / "scripts" / "aplicar_blueprint_documentos_fiscais.py").read_text(encoding="utf-8")

    assert 'app.extensions["documentos_services"]' in fonte
    assert "app.register_blueprint" in fonte
    assert "ast.parse" not in fonte
    assert "blueprint16-backup" in fonte
