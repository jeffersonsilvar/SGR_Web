from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_endpoints_documentos_fiscais_registrados(app):
    regras = {regra.endpoint: regra.rule for regra in app.url_map.iter_rules()}
    assert regras["documentos.central_documentos_fiscais"] == "/documentos-fiscais"
    assert regras["documentos.novo_documento_fiscal"] == "/documentos-fiscais/novo"
    assert regras["documentos.detalhes_documento_fiscal"] == "/documentos-fiscais/<int:id>"
    assert regras["documentos.api_pessoas_documento_fiscal"] == "/documentos-fiscais/api/pessoas"


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


def test_central_tambem_le_estrutura_generica_16_2():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")

    assert "FROM documentos_fiscais df" in fonte
    assert 'documento["fonte"] = "NOVO"' in fonte
    assert "TIPOS_DOCUMENTO_ADMIN" in fonte
    assert 'documento["origem_documento"] = "Cadastro interno"' in fonte


def test_central_respeita_isolamento_multiempresa():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")

    assert 'where.append("nf.empresa_id = %s")' in fonte
    assert 'where_novo.append("df.empresa_id = %s")' in fonte
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
    assert 'return "Aprovado"' in fonte
    assert 'documento["status_documento"]' in fonte


def test_status_documental_generico_nao_mistura_financeiro():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")
    template = (ROOT / "templates" / "documentos_fiscais.html").read_text(encoding="utf-8")

    assert 'STATUS_DOCUMENTAIS = ("Recebido", "Em análise", "Aprovado", "Recusado", "Cancelado")' in fonte
    assert "Status documental" in template
    assert "Legado: {{ d.status_legado }}" in template
    assert "resumo.aprovados" in template


def test_novo_documento_nao_gera_titulo_automaticamente():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")

    assert "INSERT INTO documentos_fiscais" in fonte
    assert "'Recebido'" in fonte
    assert "INSERT INTO titulos_financeiros" not in fonte
    assert "gerar_titulo" not in fonte


def test_novo_documento_valida_pessoa_na_empresa_e_chave_duplicada():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")

    assert "WHERE id = %s AND empresa_id = %s" in fonte
    assert "WHERE empresa_id = %s AND chave_acesso = %s" in fonte
    assert "A Pessoa/Fornecedor selecionada não pertence à empresa" in fonte
    assert "Já existe um documento fiscal com esta chave" in fonte


def test_upload_16_2_aceita_somente_xml_e_pdf():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")

    assert 'EXTENSOES_UPLOAD = {"xml", "pdf"}' in fonte
    assert "_arquivo_valido(arquivo_xml, \"xml\")" in fonte
    assert "_arquivo_valido(arquivo_pdf, \"pdf\")" in fonte
    assert 'Path("uploads") / "documentos_fiscais"' in fonte


def test_busca_de_pessoa_para_documento_e_multiempresa():
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")

    assert "/documentos-fiscais/api/pessoas" in fonte
    assert "FROM pessoas" in fonte
    assert "WHERE empresa_id = %s" in fonte
    assert "LIMIT 20" in fonte


def test_templates_16_2_expoem_cadastro_e_detalhes_sem_titulo():
    central = (ROOT / "templates" / "documentos_fiscais.html").read_text(encoding="utf-8")
    form = (ROOT / "templates" / "documento_fiscal_form.html").read_text(encoding="utf-8")
    detalhes = (ROOT / "templates" / "documento_fiscal_detalhes.html").read_text(encoding="utf-8")
    fonte = (ROOT / "app_modules" / "documentos" / "routes.py").read_text(encoding="utf-8")

    assert "Importar XML" in central
    assert "Cadastro manual" in central
    assert '"NFSE_ADMIN": "NFS-e Administrativa"' in fonte
    assert '"NFE_USO_CONSUMO": "NF-e Uso/Consumo"' in fonte
    assert "tipos_documento.items()" in form
    assert "Arquivo XML" in form
    assert "Arquivo PDF" in form
    assert "Nenhum título financeiro gerado" in detalhes
    assert "Pagamento continua sendo responsabilidade exclusiva do Financeiro" in detalhes


def test_migracao_preserva_menu_legado():
    migration = (ROOT / "database" / "migrations" / "20260825_blueprint16_documentos_fiscais.sql").read_text(encoding="utf-8")

    assert "documentos.central_documentos_fiscais" in migration
    assert "financeiro_nfs_motoristas" in migration
    assert "DELETE FROM sistema_menus" not in migration
    assert "DROP" not in migration


def test_migracao_16_1_limita_documentos_fiscais_a_visualizacao():
    migration = (ROOT / "database" / "migrations" / "20260825_blueprint16_documentos_fiscais.sql").read_text(encoding="utf-8")

    assert "DELETE FROM perfil_permissoes" in migration
    assert "acao_codigo <> 'visualizar'" in migration
    assert "pp.acao_codigo = 'visualizar'" in migration
    assert "'documentos_fiscais',\n    'visualizar'" in migration


def test_migracao_16_2_cria_tabela_generica_sem_tocar_legado():
    migration = (ROOT / "database" / "migrations" / "20260825_blueprint16_2_documentos_administrativos.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS documentos_fiscais" in migration
    assert "uq_documentos_fiscais_empresa_chave" in migration
    assert "status_documento VARCHAR(30) NOT NULL DEFAULT 'Recebido'" in migration
    assert "titulo_financeiro_id INT(11) DEFAULT NULL" in migration
    assert "ALTER TABLE motorista_notas_fiscais" not in migration
    assert "DROP" not in migration


def test_migracao_16_2_habilita_criacao_sem_edicao():
    migration = (ROOT / "database" / "migrations" / "20260825_blueprint16_2_documentos_administrativos.sql").read_text(encoding="utf-8")

    assert "'criar'" in migration
    assert "pp.acao_codigo = 'visualizar'" in migration
    assert "'editar'" not in migration


def test_registrador_nao_remove_rotas_legadas():
    fonte = (ROOT / "scripts" / "aplicar_blueprint_documentos_fiscais.py").read_text(encoding="utf-8")

    assert 'app.extensions["documentos_services"]' in fonte
    assert "app.register_blueprint" in fonte
    assert "ast.parse" not in fonte
    assert "blueprint16-backup" in fonte
