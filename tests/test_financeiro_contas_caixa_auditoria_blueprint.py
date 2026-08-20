from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rotas_blueprint_contas_caixa_e_auditoria_registradas(app):
    regras = {regra.endpoint: regra.rule for regra in app.url_map.iter_rules()}

    assert regras["financeiro.nova_conta_caixa"] == "/financeiro/contas-caixa/nova"
    assert regras["financeiro.editar_conta_caixa"] == "/financeiro/contas-caixa/<int:id>/editar"
    assert regras["financeiro.financeiro_auditoria"] == "/financeiro/auditoria"


def test_endpoints_legados_foram_removidos_do_app(app):
    assert "nova_conta_caixa" not in app.view_functions
    assert "editar_conta_caixa" not in app.view_functions
    assert "financeiro_auditoria" not in app.view_functions


def test_novas_rotas_exigem_autenticacao(client):
    for url in (
        "/financeiro/contas-caixa/nova",
        "/financeiro/contas-caixa/1/editar",
        "/financeiro/auditoria",
    ):
        resposta = client.get(url, follow_redirects=False)
        assert resposta.status_code == 302
        assert "/login" in resposta.headers["Location"]


def test_operacional_nao_pode_administrar_conta_caixa():
    fonte = (ROOT / "app_modules" / "financeiro" / "contas_caixa_auditoria.py").read_text(encoding="utf-8")

    assert '@perfis_permitidos("Administrador", "Financeiro")' in fonte
    assert '@perfis_permitidos("Administrador", "Operacional", "Financeiro")' not in fonte


def test_edicao_bloqueia_saldo_inicial_de_conta_movimentada():
    fonte = (ROOT / "app_modules" / "financeiro" / "contas_caixa_auditoria.py").read_text(encoding="utf-8")
    template = (ROOT / "templates" / "financeiro_conta_caixa_form.html").read_text(encoding="utf-8")

    assert "_conta_tem_movimentacao" in fonte
    assert "if not tem_movimentacao" in fonte
    assert "conta.tem_movimentacao" in template
    assert "readonly" in template
    assert "Ajustes devem ser feitos por movimentação/conciliação" in template


def test_criacao_e_edicao_de_conta_geram_auditoria():
    fonte = (ROOT / "app_modules" / "financeiro" / "contas_caixa_auditoria.py").read_text(encoding="utf-8")

    assert 'acao="CONTA_CAIXA_CRIADA"' in fonte
    assert 'acao="CONTA_CAIXA_EDITADA"' in fonte
    assert 'entidade_tipo' in fonte
    assert '"CONTA_CAIXA"' in fonte
    assert "dados_antes" in fonte
    assert "dados_depois" in fonte


def test_templates_usam_endpoints_do_blueprint():
    lista = (ROOT / "templates" / "financeiro_contas_caixa.html").read_text(encoding="utf-8")

    assert "financeiro.nova_conta_caixa" in lista
    assert "financeiro.editar_conta_caixa" in lista
    assert "url_for('nova_conta_caixa')" not in lista
    assert "url_for('editar_conta_caixa'" not in lista


def test_migrador_remove_rotas_legadas_por_ast():
    fonte = (ROOT / "scripts" / "aplicar_blueprint_contas_caixa_auditoria.py").read_text(encoding="utf-8")

    assert '"nova_conta_caixa"' in fonte
    assert '"editar_conta_caixa"' in fonte
    assert '"financeiro_auditoria"' in fonte
    assert "ast.parse" in fonte
    assert "decorator_list" in fonte
    assert "app.py.blueprint15-backup" in fonte
