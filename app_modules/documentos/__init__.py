from .routes import criar_documentos_blueprint as _criar_documentos_blueprint_base
from .workflow import registrar_fluxo_documental
from . import importacao_xml as _importacao_xml
from .visualizacao_fiscal import registrar_visualizacao_fiscal
from .cte_importacao import instalar_suporte_cte
from .cadastro_manual_storage import registrar_cadastro_manual_storage


instalar_suporte_cte(_importacao_xml)
registrar_importacao_xml = _importacao_xml.registrar_importacao_xml


def criar_documentos_blueprint(services):
    documentos_bp = _criar_documentos_blueprint_base(services)
    registrar_cadastro_manual_storage(documentos_bp, services)
    registrar_fluxo_documental(documentos_bp, services)
    registrar_importacao_xml(documentos_bp, services)
    registrar_visualizacao_fiscal(documentos_bp, services)
    return documentos_bp


__all__ = ["criar_documentos_blueprint"]
