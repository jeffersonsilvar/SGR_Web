def test_endpoint_blueprint_e_reconhecido_pelo_gerenciador(app, app_module):
    assert app_module.endpoint_existe_no_app(
        "financeiro.financeiro_contas_caixa",
        "/financeiro/contas-caixa",
    ) is True


def test_rota_publica_pode_validar_menu_com_endpoint_legado(app, app_module):
    assert app_module.endpoint_existe_no_app(
        "financeiro_contas_caixa",
        "/financeiro/contas-caixa",
    ) is True


def test_endpoint_inexistente_continua_sendo_recusado(app_module):
    assert app_module.endpoint_existe_no_app(
        "modulo.endpoint_inexistente",
        "/rota-que-nao-existe",
    ) is False
