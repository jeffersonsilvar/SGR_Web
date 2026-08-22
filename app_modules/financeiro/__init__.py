from .contas_caixa_auditoria import registrar_rotas_contas_caixa_auditoria
from .edicao_titulo import registrar_rotas_edicao_titulo
from .idempotencia_estorno import instalar_protecao_idempotencia_estorno
from .routes import criar_financeiro_blueprint as _criar_financeiro_blueprint_base


def criar_financeiro_blueprint(services):
    # A proteção precisa ser instalada antes da criação das rotas, pois baixa e
    # estorno consomem esta dependência através do dicionário de services.
    instalar_protecao_idempotencia_estorno(services)
    financeiro_bp = _criar_financeiro_blueprint_base(services)
    registrar_rotas_edicao_titulo(financeiro_bp, services)
    registrar_rotas_contas_caixa_auditoria(financeiro_bp, services)
    return financeiro_bp


__all__ = ["criar_financeiro_blueprint"]