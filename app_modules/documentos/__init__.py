from .routes import criar_documentos_blueprint as _criar_documentos_blueprint_base
from .workflow import registrar_fluxo_documental
from .importacao_xml import registrar_importacao_xml


def criar_documentos_blueprint(services):
    documentos_bp = _criar_documentos_blueprint_base(services)
    registrar_fluxo_documental(documentos_bp, services)
    registrar_importacao_xml(documentos_bp, services)
    return documentos_bp


__all__ = ["criar_documentos_blueprint"]
