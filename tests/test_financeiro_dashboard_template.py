def test_template_dashboard_financeiro_compila(app):
    """
    Protege contra erros de sintaxe Jinja no dashboard financeiro.
    """
    template = app.jinja_env.get_template("financeiro_dashboard.html")
    assert template is not None


def test_link_movimentacoes_caixa_no_dashboard_usa_blueprint(app):
    source, _, _ = app.jinja_loader.get_source(
        app.jinja_env,
        "financeiro_dashboard.html",
    )

    assert (
        "url_for('financeiro.financeiro_movimentacoes_caixa')"
        in source
    )
    assert (
        "url_for('financeiro.financeiro_movimentacoes_caixa'))"
        not in source
    )
