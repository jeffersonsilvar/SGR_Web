from .edicao_titulo import registrar_rotas_edicao_titulo
from .routes import criar_financeiro_blueprint as _criar_financeiro_blueprint_base


def criar_financeiro_blueprint(services):
    financeiro_bp = _criar_financeiro_blueprint_base(services)
    registrar_rotas_edicao_titulo(financeiro_bp, services)
    return financeiro_bp


__all__ = ["criar_financeiro_blueprint"]
