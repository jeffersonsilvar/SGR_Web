def test_endpoint_blueprint_contas_caixa_reconhecido(app, app_module):
    assert app_module.endpoint_existe_no_app(
        "financeiro.financeiro_contas_caixa",
        "/financeiro/contas-caixa",
    ) is True


def test_endpoint_antigo_reconhecido_por_sufixo_unico(app, app_module):
    assert app_module.endpoint_existe_no_app(
        "financeiro_contas_caixa"
    ) is True


def test_rota_reconhecida_como_fallback(app, app_module):
    assert app_module.endpoint_existe_no_app(
        "endpoint_inexistente",
        "/financeiro/contas-caixa",
    ) is True


def test_endpoint_e_rota_inexistentes(app, app_module):
    assert app_module.endpoint_existe_no_app(
        "endpoint_inexistente",
        "/rota-inexistente",
    ) is False
