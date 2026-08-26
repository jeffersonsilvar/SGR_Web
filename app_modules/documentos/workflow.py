from datetime import datetime
from decimal import Decimal

from flask import flash, redirect, request, session, url_for


TRANSICOES = {
    "analise": {"Recebido": "Em análise"},
    "aprovar": {"Em análise": "Aprovado"},
    "recusar": {"Recebido": "Recusado", "Em análise": "Recusado"},
}

ACOES_AUDITORIA = {
    "analise": "DOCUMENTO_FISCAL_EM_ANALISE",
    "aprovar": "DOCUMENTO_FISCAL_APROVADO",
    "recusar": "DOCUMENTO_FISCAL_RECUSADO",
}


def _data_iso(valor):
    try:
        return datetime.strptime(str(valor or ""), "%Y-%m-%d").date()
    except Exception:
        return None


def _fechar(cur=None, con=None):
    try:
        if cur:
            cur.close()
    except Exception:
        pass
    try:
        if con:
            con.close()
    except Exception:
        pass


def _auditar(cur, *, documento, acao, status_anterior=None, status_novo=None, titulo_id=None, observacao=None):
    cur.execute(
        """
        INSERT INTO auditoria_financeira
            (empresa_id, usuario_id, modulo, acao, entidade_tipo, entidade_id,
             titulo_financeiro_id, pessoa_id, status_anterior, status_novo,
             valor_anterior, valor_novo, observacao, ip_origem, user_agent, created_at)
        VALUES
            (%s, %s, 'DOCUMENTOS_FISCAIS', %s, 'DOCUMENTO_FISCAL', %s,
             %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """,
        (
            documento["empresa_id"],
            session.get("usuario_id"),
            acao,
            documento["id"],
            titulo_id,
            documento.get("pessoa_id"),
            status_anterior,
            status_novo,
            documento.get("valor_total"),
            documento.get("valor_total"),
            observacao,
            request.remote_addr,
            request.headers.get("User-Agent"),
        ),
    )


def _buscar_documento(cur, documento_id, empresa_id, is_super_admin, *, for_update=False):
    sql = """
        SELECT df.*,
               p.nome_completo AS pessoa_nome,
               p.cpf_cnpj AS pessoa_documento
        FROM documentos_fiscais df
        LEFT JOIN pessoas p
               ON p.id = df.pessoa_id
              AND p.empresa_id = df.empresa_id
        WHERE df.id = %s
    """
    params = [documento_id]
    if not is_super_admin:
        sql += " AND df.empresa_id = %s"
        params.append(empresa_id)
    if for_update:
        sql += " FOR UPDATE"
    cur.execute(sql, params)
    return cur.fetchone()


def registrar_fluxo_documental(documentos_bp, services):
    login_required = services["login_required"]
    perfis_permitidos = services["perfis_permitidos"]
    usuario_eh_super_admin_global = services["usuario_eh_super_admin_global"]
    obter_conexao = services["obter_conexao"]

    def _mudar_status(documento_id, acao_fluxo):
        empresa_id = session.get("empresa_id")
        is_super_admin = usuario_eh_super_admin_global()
        con = obter_conexao()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("documentos.detalhes_documento_fiscal", id=documento_id))

        cur = con.cursor(dictionary=True)
        try:
            documento = _buscar_documento(cur, documento_id, empresa_id, is_super_admin, for_update=True)
            if not documento:
                flash("Documento fiscal não encontrado.", "warning")
                con.rollback()
                return redirect(url_for("documentos.central_documentos_fiscais"))

            status_atual = documento.get("status_documento")
            novo_status = TRANSICOES.get(acao_fluxo, {}).get(status_atual)
            if not novo_status:
                flash(f"Ação não permitida para documento no status {status_atual}.", "warning")
                con.rollback()
                return redirect(url_for("documentos.detalhes_documento_fiscal", id=documento_id))

            cur.execute(
                """
                UPDATE documentos_fiscais
                SET status_documento = %s,
                    usuario_atualizacao_id = %s,
                    updated_at = NOW()
                WHERE id = %s AND empresa_id = %s
                """,
                (novo_status, session.get("usuario_id"), documento_id, documento["empresa_id"]),
            )
            _auditar(
                cur,
                documento=documento,
                acao=ACOES_AUDITORIA[acao_fluxo],
                status_anterior=status_atual,
                status_novo=novo_status,
            )
            con.commit()
            flash(f"Documento atualizado para {novo_status}.", "success")
        except Exception as exc:
            con.rollback()
            print(f"Erro no fluxo documental {acao_fluxo}: {exc}")
            flash(f"Erro técnico ao atualizar documento: {exc}", "danger")
        finally:
            _fechar(cur, con)

        return redirect(url_for("documentos.detalhes_documento_fiscal", id=documento_id))

    @documentos_bp.post("/documentos-fiscais/<int:id>/marcar-analise")
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def marcar_documento_em_analise(id):
        return _mudar_status(id, "analise")

    @documentos_bp.post("/documentos-fiscais/<int:id>/aprovar")
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def aprovar_documento_fiscal(id):
        return _mudar_status(id, "aprovar")

    @documentos_bp.post("/documentos-fiscais/<int:id>/recusar")
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def recusar_documento_fiscal(id):
        return _mudar_status(id, "recusar")

    @documentos_bp.post("/documentos-fiscais/<int:id>/gerar-titulo")
    @login_required
    @perfis_permitidos("Administrador", "Financeiro")
    def gerar_titulo_documento_fiscal(id):
        empresa_id = session.get("empresa_id")
        is_super_admin = usuario_eh_super_admin_global()
        data_vencimento = _data_iso(request.form.get("data_vencimento"))
        if not data_vencimento:
            flash("Informe uma data de vencimento válida para gerar o título.", "warning")
            return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))

        con = obter_conexao()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))

        cur = con.cursor(dictionary=True)
        try:
            documento = _buscar_documento(cur, id, empresa_id, is_super_admin, for_update=True)
            if not documento:
                flash("Documento fiscal não encontrado.", "warning")
                con.rollback()
                return redirect(url_for("documentos.central_documentos_fiscais"))

            if documento.get("status_documento") != "Aprovado":
                flash("Somente documentos aprovados podem gerar título financeiro.", "warning")
                con.rollback()
                return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))

            if not documento.get("pessoa_id"):
                flash("Vincule uma Pessoa/Fornecedor ao documento antes de gerar o título.", "warning")
                con.rollback()
                return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))

            if documento.get("titulo_financeiro_id"):
                flash(f"Este documento já possui o título #{documento['titulo_financeiro_id']}.", "info")
                con.rollback()
                return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))

            emissao = documento.get("data_emissao")
            if emissao and data_vencimento < emissao:
                flash("O vencimento do título não pode ser anterior à emissão do documento.", "warning")
                con.rollback()
                return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))

            cur.execute(
                """
                SELECT id
                FROM titulos_financeiros
                WHERE empresa_id = %s
                  AND origem = 'DOCUMENTO_FISCAL'
                  AND origem_id = %s
                ORDER BY id ASC
                LIMIT 1
                FOR UPDATE
                """,
                (documento["empresa_id"], documento["id"]),
            )
            existente = cur.fetchone()
            if existente:
                titulo_id = existente["id"]
                cur.execute(
                    """
                    UPDATE documentos_fiscais
                    SET titulo_financeiro_id = %s,
                        usuario_atualizacao_id = %s,
                        updated_at = NOW()
                    WHERE id = %s AND empresa_id = %s
                    """,
                    (titulo_id, session.get("usuario_id"), documento["id"], documento["empresa_id"]),
                )
                _auditar(
                    cur,
                    documento=documento,
                    acao="DOCUMENTO_FISCAL_TITULO_VINCULADO",
                    status_anterior="Aprovado",
                    status_novo="Aprovado",
                    titulo_id=titulo_id,
                    observacao="Título existente localizado por origem e vinculado ao documento.",
                )
                con.commit()
                flash(f"Título existente #{titulo_id} vinculado ao documento.", "info")
                return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))

            valor = Decimal(str(documento.get("valor_total") or 0)).quantize(Decimal("0.01"))
            descricao = (documento.get("descricao") or "").strip() or f"Documento fiscal {documento.get('numero_documento')}"
            historico = f"{descricao} - Documento Fiscal #{documento['id']} - {documento.get('pessoa_nome') or documento.get('nome_emitente') or 'Fornecedor'}"

            cur.execute(
                """
                INSERT INTO titulos_financeiros
                    (empresa_id, tipo_titulo, origem, origem_id, pessoa_id, numero_documento,
                     descricao, historico, valor_original, valor_desconto, valor_acrescimo,
                     valor_liquido, data_emissao, data_competencia, data_vencimento,
                     forma_pagamento, conta_caixa_prevista_id, status_titulo, observacao,
                     usuario_criacao_id)
                VALUES
                    (%s, 'PAGAR', 'DOCUMENTO_FISCAL', %s, %s, %s,
                     %s, %s, %s, 0.00, 0.00,
                     %s, %s, %s, %s,
                     NULL, NULL, 'Aberto', %s, %s)
                """,
                (
                    documento["empresa_id"],
                    documento["id"],
                    documento["pessoa_id"],
                    documento["numero_documento"],
                    descricao,
                    historico,
                    valor,
                    valor,
                    documento["data_emissao"],
                    documento.get("data_competencia") or documento["data_emissao"],
                    data_vencimento,
                    f"Gerado a partir do Documento Fiscal #{documento['id']}.",
                    session.get("usuario_id"),
                ),
            )
            titulo_id = cur.lastrowid

            cur.execute(
                """
                UPDATE documentos_fiscais
                SET titulo_financeiro_id = %s,
                    usuario_atualizacao_id = %s,
                    updated_at = NOW()
                WHERE id = %s AND empresa_id = %s
                """,
                (titulo_id, session.get("usuario_id"), documento["id"], documento["empresa_id"]),
            )
            _auditar(
                cur,
                documento=documento,
                acao="DOCUMENTO_FISCAL_TITULO_GERADO",
                status_anterior="Aprovado",
                status_novo="Aprovado",
                titulo_id=titulo_id,
                observacao=f"Título a pagar #{titulo_id} gerado com vencimento em {data_vencimento.isoformat()}.",
            )
            con.commit()
            flash(f"Título financeiro #{titulo_id} gerado com sucesso.", "success")
        except Exception as exc:
            con.rollback()
            print(f"Erro ao gerar título por documento fiscal: {exc}")
            flash(f"Erro técnico ao gerar título: {exc}", "danger")
        finally:
            _fechar(cur, con)

        return redirect(url_for("documentos.detalhes_documento_fiscal", id=id))
