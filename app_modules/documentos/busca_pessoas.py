from __future__ import annotations

from flask import jsonify, request, session

from . import routes as routes_module


ROTA_BUSCA_PESSOAS = "/documentos-fiscais/api/pessoas"


def _deferred_registra_rota(funcao, rota):
    for celula in getattr(funcao, "__closure__", None) or ():
        try:
            valor = celula.cell_contents
        except ValueError:
            continue
        if valor == rota:
            return True
        if isinstance(valor, (tuple, list, set)) and rota in valor:
            return True
        if isinstance(valor, dict) and rota in valor.values():
            return True
    return False


def _remover_handler_legado(documentos_bp):
    anteriores = list(documentos_bp.deferred_functions)
    documentos_bp.deferred_functions = [
        funcao for funcao in anteriores if not _deferred_registra_rota(funcao, ROTA_BUSCA_PESSOAS)
    ]
    removidos = len(anteriores) - len(documentos_bp.deferred_functions)
    if removidos != 1:
        raise RuntimeError("Não foi possível substituir com segurança a busca de Pessoas do Documento Fiscal.")


def registrar_busca_pessoas_normalizada(documentos_bp, services):
    """Substitui a busca legada por uma versão que compara CPF/CNPJ sem máscara."""
    _remover_handler_legado(documentos_bp)

    login_required = services["login_required"]
    perfis_permitidos = services["perfis_permitidos"]
    usuario_eh_super_admin_global = services["usuario_eh_super_admin_global"]
    obter_conexao = services["obter_conexao"]

    @documentos_bp.route(ROTA_BUSCA_PESSOAS, methods=["GET"])
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def api_pessoas_documento_fiscal():
        empresa_logada_id = session.get("empresa_id")
        is_super_admin = usuario_eh_super_admin_global()
        empresa_id = routes_module._empresa_alvo(
            is_super_admin,
            empresa_logada_id,
            request.args.get("empresa_id"),
        )
        termo = (request.args.get("q") or "").strip()

        if not empresa_id or len(termo) < 2:
            return jsonify([])

        con = obter_conexao()
        if con is None:
            return jsonify([]), 503

        cur = con.cursor(dictionary=True)
        try:
            like_nome = f"%{termo}%"
            digitos = routes_module._somente_digitos(termo)
            documento_normalizado = f"%{digitos}%" if digitos else "%"

            cur.execute(
                """
                SELECT id, nome_completo, cpf_cnpj, tipo_cadastro, tipo_prestador
                FROM pessoas
                WHERE empresa_id = %s
                  AND (
                    nome_completo LIKE %s
                    OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(cpf_cnpj, '.', ''), '/', ''), '-', ''), ' ', ''), '\\', '') LIKE %s
                    OR CAST(id AS CHAR) = %s
                  )
                ORDER BY nome_completo
                LIMIT 20
                """,
                (empresa_id, like_nome, documento_normalizado, termo),
            )

            resultados = []
            for pessoa in cur.fetchall() or []:
                categoria = pessoa.get("tipo_cadastro") or "Pessoa"
                if pessoa.get("tipo_prestador"):
                    categoria = f"{categoria} / {pessoa.get('tipo_prestador')}"
                resultados.append(
                    {
                        "id": pessoa.get("id"),
                        "nome": pessoa.get("nome_completo"),
                        "documento": pessoa.get("cpf_cnpj") or "",
                        "categoria": categoria,
                        "label": f"#{pessoa.get('id')} — {pessoa.get('nome_completo')} — {pessoa.get('cpf_cnpj') or 'sem documento'}",
                    }
                )
            return jsonify(resultados)
        finally:
            routes_module._fechar(cur, con)
