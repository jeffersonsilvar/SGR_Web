from datetime import date, datetime, timedelta
from decimal import Decimal


def test_formatar_data_br(app_module):
    assert app_module.formatar_data_br(date(2026, 8, 4)) == "04/08/2026"
    assert app_module.formatar_data_br(datetime(2026, 8, 4, 15, 30)) == "04/08/2026"
    assert app_module.formatar_data_br(None) == "-"


def test_formatar_data_hora_br(app_module):
    resultado = app_module.formatar_data_hora_br("2026-08-04 17:30:00")
    assert resultado == "04/08/2026 17:30"


def test_moeda_br(app_module):
    assert app_module.moeda_br(1234.5) == "R$ 1.234,50"
    assert app_module.moeda_br(None) == "R$ 0,00"


def test_converter_decimal(app_module):
    assert app_module.converter_decimal("R$ 1.234,56") == Decimal("1234.56")
    assert app_module.converter_decimal("") == Decimal("0.00")
    assert app_module.converter_decimal("valor inválido") == Decimal("0.00")


def test_normalizar_horario(app_module):
    assert app_module.normalizar_horario_input(timedelta(hours=8, minutes=30)) == "08:30"
    assert app_module.normalizar_horario_input("18:45:00") == "18:45"
    assert app_module.normalizar_horario_input(None) == ""


def test_somente_digitos(app_module):
    assert app_module.somente_digitos("123.456.789-00") == "12345678900"


def test_rota_pode_ser_editada(app_module):
    assert app_module.rota_pode_ser_editada(
        {"status_motorista": "Aguardando liberação"}
    ) is True

    assert app_module.rota_pode_ser_editada(
        {"status_motorista": "Bloqueada"},
        possui_documento_ativo=False,
    ) is True

    assert app_module.rota_pode_ser_editada(
        {"status_motorista": "Pagamento confirmado"}
    ) is False

    assert app_module.rota_pode_ser_editada(
        {"status_motorista": "Aguardando liberação"},
        possui_documento_ativo=True,
    ) is False
