from decimal import Decimal


def autenticar(client, empresa_id=10, perfil="Financeiro", super_admin=0):
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Usuário de teste"
        sessao["empresa_id"] = empresa_id
        sessao["perfil_de_acesso"] = perfil
        sessao["is_super_admin"] = super_admin


def dados_validos():
    return {
        "pessoa_id": "5",
        "numero_documento": "DOC-EDIT-200",
        "descricao": "Serviço alterado",
        "historico": "Histórico alterado",
        "data_emissao": "2026-08-10",
        "data_competencia": "2026-08-10",
        "data_vencimento": "2026-08-31",
        "forma_pagamento": "PIX",
        "conta_caixa_prevista_id": "2",
        "valor_original": "200,00",
        "valor_desconto": "10,00",
        "valor_acrescimo": "5,00",
        "observacao": "Alterado em teste",
    }


class CursorEdicao:
    def __init__(self, *, origem="MANUAL", status="Aberto", qtd_movimentacoes=0, falhar_update=False):
        self.origem = origem
        self.status = status
        self.qtd_movimentacoes = qtd_movimentacoes
        self.falhar_update = falhar_update
        self.retorno = None
        self.lista = []
        self.rowcount = 0
        self.execucoes = []

    def execute(self, query, params=None):
        params = tuple(params or ())
        self.execucoes.append((query, params))
        self.rowcount = 0

        if "FROM titulos_financeiros t" in query and "qtd_movimentacoes" in query:
            self.retorno = {
                "id": 7,
                "empresa_id": 10,
                "tipo_titulo": "PAGAR",
                "origem": self.origem,
                "status_titulo": self.status,
                "pessoa_id": 5,
                "pessoa_nome": "Fornecedor Teste",
                "pessoa_cpf_cnpj": "12345678901",
                "numero_documento": "DOC-100",
                "descricao": "Serviço original",
                "historico": "Histórico original",
                "valor_original": Decimal("100.00"),
                "valor_desconto": Decimal("0.00"),
                "valor_acrescimo": Decimal("0.00"),
                "valor_liquido": Decimal("100.00"),
                "data_emissao": "2026-08-01",
                "data_competencia": "2026-08-01",
                "data_vencimento": "2026-08-20",
                "forma_pagamento": "PIX",
                "conta_caixa_prevista_id": None,
                "observacao": "Original",
                "qtd_movimentacoes": self.qtd_movimentacoes,
            }
        elif "FROM pessoas" in query and "WHERE id = %s" in query:
            self.retorno = {"id": 5, "nome_completo": "Fornecedor Teste"}
        elif "FROM contas_caixa" in query and "WHERE id = %s" in query:
            self.retorno = {"id": 2}
        elif "FROM pessoas" in query and "ORDER BY nome_completo" in query:
            self.lista = [{"id": 5, "nome_completo": "Fornecedor Teste", "cpf_cnpj": "123"}]
            self.retorno = None
        elif "FROM contas_caixa" in query and "ORDER BY nome_conta" in query:
            self.lista = [{"id": 2, "nome_conta": "Conta Teste"}]
            self.retorno = None
        elif "UPDATE titulos_financeiros" in query:
            if self.falhar_update:
                raise RuntimeError("falha simulada")
            self.rowcount = 1
            self.retorno = None
        else:
            self.retorno = None

    def fetchone(self):
        return self.retorno

    def fetchall(self):
        return self.lista


class ConexaoEdicao:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.commits = 0
        self.rollbacks = 0

    def cursor(self, dictionary=False):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def preparar(app, monkeypatch, *, origem="MANUAL", status="Aberto", qtd_movimentacoes=0, falhar_update=False):
    services = app.extensions["financeiro_services"]
    cursor = CursorEdicao(
        origem=origem,
        status=status,
        qtd_movimentacoes=qtd_movimentacoes,
        falhar_update=falhar_update,
    )
    conexao = ConexaoEdicao(cursor)
    auditoria = {}

    monkeypatch.setitem(services, "obter_conexao", lambda: conexao)
    monkeypatch.setitem(services, "fechar_cursor_conexao", lambda cursor, con: None)
    monkeypatch.setitem(
        services,
        "registrar_auditoria_financeira",
        lambda cursor, **kwargs: auditoria.update(kwargs),
    )
    return services, conexao, cursor, auditoria


def test_endpoint_editar_titulo_registrado(app):
    regras = {regra.endpoint: (regra.rule, regra.methods) for regra in app.url_map.iter_rules()}
    rota, metodos = regras["financeiro.editar_titulo_financeiro"]
    assert rota == "/financeiro/titulos/<int:id>/editar"
    assert {"GET", "POST"}.issubset(metodos)


def test_editar_titulo_exige_autenticacao(client):
    resposta = client.get("/financeiro/titulos/7/editar", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_get_edicao_renderiza_titulo_manual(client, app, monkeypatch):
    preparar(app, monkeypatch)
    autenticar(client)
    resposta = client.get("/financeiro/titulos/7/editar")
    assert resposta.status_code == 200
    assert b"Editar T" in resposta.data
    assert b"DOC-100" in resposta.data
    assert b"sgr-busca-pessoa" in resposta.data
    assert b"Digite nome, CPF/CNPJ ou ID" in resposta.data
    assert b"Fornecedor Teste" in resposta.data


def test_edicao_bloqueia_titulo_automatico(client, app, monkeypatch):
    preparar(app, monkeypatch, origem="NF_MOTORISTA")
    autenticar(client)
    resposta = client.get("/financeiro/titulos/7/editar", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/financeiro/titulos/7" in resposta.headers["Location"]


def test_edicao_bloqueia_status_nao_aberto(client, app, monkeypatch):
    preparar(app, monkeypatch, status="Pago")
    autenticar(client)
    resposta = client.get("/financeiro/titulos/7/editar", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/financeiro/titulos/7" in resposta.headers["Location"]


def test_edicao_bloqueia_titulo_com_movimentacao_historica(client, app, monkeypatch):
    preparar(app, monkeypatch, qtd_movimentacoes=2)
    autenticar(client)
    resposta = client.get("/financeiro/titulos/7/editar", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/financeiro/titulos/7" in resposta.headers["Location"]


def test_edicao_recalcula_liquido_e_registra_auditoria(client, app, monkeypatch):
    _, conexao, cursor, auditoria = preparar(app, monkeypatch)
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/7/editar",
        data=dados_validos(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/7" in resposta.headers["Location"]
    assert conexao.commits == 1
    assert conexao.rollbacks == 0
    assert auditoria["acao"] == "TITULO_MANUAL_EDITADO"
    assert auditoria["valor_anterior"] == Decimal("100.00")
    assert auditoria["valor_novo"] == Decimal("195.00")
    assert auditoria["dados_antes"]["numero_documento"] == "DOC-100"
    assert auditoria["dados_depois"]["numero_documento"] == "DOC-EDIT-200"

    update = next(item for item in cursor.execucoes if "UPDATE titulos_financeiros" in item[0])
    assert "origem = 'MANUAL'" in update[0]
    assert "NOT EXISTS" in update[0]
    assert Decimal("195.00") in update[1]


def test_edicao_faz_rollback_em_erro(client, app, monkeypatch):
    _, conexao, _, _ = preparar(app, monkeypatch, falhar_update=True)
    autenticar(client)

    resposta = client.post(
        "/financeiro/titulos/7/editar",
        data=dados_validos(),
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/financeiro/titulos/7" in resposta.headers["Location"]
    assert conexao.commits == 0
    assert conexao.rollbacks == 1
