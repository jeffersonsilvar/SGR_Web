from pathlib import Path


def test_template_detalhes_exibe_cancelamento_para_titulo_cancelavel(app):
    template = app.jinja_env.get_template("financeiro_titulo_detalhes.html")
    fonte, _, _ = app.jinja_loader.get_source(
        app.jinja_env,
        "financeiro_titulo_detalhes.html",
    )

    assert "financeiro.cancelar_titulo_financeiro" in fonte
    assert "Cancelar título" in fonte
    assert "motivo_cancelamento" in fonte
    assert 'minlength="5"' in fonte
    assert "cfg_cancelar_manual" not in fonte


def test_template_cancelamento_fica_dentro_do_bloco_de_status_cancelavel(app):
    fonte, _, _ = app.jinja_loader.get_source(
        app.jinja_env,
        "financeiro_titulo_detalhes.html",
    )

    condicao = (
        "{% if titulo.status_titulo not in "
        "['Pago', 'Recebido', 'Cancelado', 'Estornado'] %}"
    )
    pos_condicao = fonte.find(condicao)
    pos_cancelar = fonte.find("financeiro.cancelar_titulo_financeiro")
    pos_fim = fonte.find("{% endif %}", pos_cancelar)

    assert pos_condicao != -1
    assert pos_cancelar > pos_condicao
    assert pos_fim > pos_cancelar
