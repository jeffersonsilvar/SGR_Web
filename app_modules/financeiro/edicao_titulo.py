from decimal import Decimal

from flask import flash, redirect, render_template, request, session, url_for


def registrar_rotas_edicao_titulo(financeiro_bp, services):
    """Registra a edição segura de títulos financeiros lançados manualmente."""

    login_required = services["login_required"]
    perfis_permitidos = services["perfis_permitidos"]

    def _carregar_titulo_editavel(cur, titulo_id, empresa_logada_id, is_super_admin):
        query = """
            SELECT t.*,
                   p.nome_completo AS pessoa_nome,
                   p.cpf_cnpj AS pessoa_cpf_cnpj,
                   cx.nome_conta AS conta_caixa_nome,
                   e.nome_fantasia AS empresa_nome,
                   e.razao_social AS empresa_razao_social,
                   (
                       SELECT COUNT(*)
                       FROM movimentacoes_caixa m
                       WHERE m.titulo_financeiro_id = t.id
                         AND m.empresa_id = t.empresa_id
                   ) AS qtd_movimentacoes
            FROM titulos_financeiros t
            LEFT JOIN pessoas p
                   ON p.id = t.pessoa_id
                  AND p.empresa_id = t.empresa_id
            LEFT JOIN contas_caixa cx
                   ON cx.id = t.conta_caixa_prevista_id
                  AND cx.empresa_id = t.empresa_id
            LEFT JOIN empresas e ON e.id = t.empresa_id
            WHERE t.id = %s
        """
        params = [titulo_id]
        if not is_super_admin:
            query += " AND t.empresa_id = %s"
            params.append(empresa_logada_id)
        query += " LIMIT 1"
        cur.execute(query, params)
        return cur.fetchone()

    def _motivo_bloqueio_edicao(titulo):
        if not titulo:
            return "Título financeiro não encontrado ou não pertence à empresa logada."
        if str(titulo.get("origem") or "").strip().upper() != "MANUAL":
            return "Somente títulos de origem MANUAL podem ser editados. Títulos automáticos devem ser corrigidos na origem."
        if str(titulo.get("status_titulo") or "").strip() != "Aberto":
            return "Somente títulos manuais com status Aberto podem ser editados."
        if int(titulo.get("qtd_movimentacoes") or 0) > 0:
            return "Este título possui histórico de movimentação de caixa e não pode mais ser editado."
        return None

    @financeiro_bp.route("/financeiro/titulos/<int:id>/editar", methods=["GET", "POST"])
    @login_required
    @perfis_permitidos("Administrador", "Operacional", "Financeiro")
    def editar_titulo_financeiro(id):
        usuario_logado = session.get("usuario_nome", "Usuário")
        empresa_logada_id = session.get("empresa_id")
        usuario_id = session.get("usuario_id")
        is_super_admin = services["usuario_eh_super_admin_global"]()

        if not empresa_logada_id:
            flash("Empresa não identificada na sessão. Faça login novamente.", "danger")
            return redirect(url_for("logout"))

        con = services["obter_conexao"]()
        if con is None:
            flash("Erro de conexão com o banco de dados.", "danger")
            return redirect(url_for("financeiro.financeiro_titulos"))

        cur = con.cursor(dictionary=True)
        try:
            titulo = _carregar_titulo_editavel(cur, id, empresa_logada_id, is_super_admin)
            motivo_bloqueio = _motivo_bloqueio_edicao(titulo)
            if motivo_bloqueio:
                flash(motivo_bloqueio, "warning" if titulo else "danger")
                return redirect(
                    url_for("financeiro.detalhes_titulo_financeiro", id=id)
                    if titulo
                    else url_for("financeiro.financeiro_titulos")
                )

            empresa_titulo_id = int(titulo["empresa_id"])

            if request.method == "POST":
                pessoa_id = (request.form.get("pessoa_id") or "").strip()
                numero_documento = (request.form.get("numero_documento") or "").strip()
                descricao = (request.form.get("descricao") or "").strip()
                historico = (request.form.get("historico") or "").strip()
                data_emissao = (request.form.get("data_emissao") or "").strip()
                data_competencia = (request.form.get("data_competencia") or "").strip()
                data_vencimento = (request.form.get("data_vencimento") or "").strip()
                forma_pagamento = (request.form.get("forma_pagamento") or "").strip()
                conta_caixa_prevista_id = (request.form.get("conta_caixa_prevista_id") or "").strip()
                valor_original = services["converter_decimal"](request.form.get("valor_original"))
                valor_desconto = services["converter_decimal"](request.form.get("valor_desconto"))
                valor_acrescimo = services["converter_decimal"](request.form.get("valor_acrescimo"))
                observacao = (request.form.get("observacao") or "").strip()

                if not pessoa_id.isdigit():
                    flash("Selecione uma pessoa válida.", "danger")
                    return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))
                pessoa_id = int(pessoa_id)

                if not numero_documento:
                    flash("Informe o número do documento.", "danger")
                    return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))
                if not descricao:
                    flash("Informe uma descrição para o título.", "danger")
                    return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))

                if not data_emissao or not services["validar_data_iso"](data_emissao):
                    flash("Informe uma data de emissão válida.", "danger")
                    return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))
                if not data_competencia:
                    data_competencia = data_emissao
                if not services["validar_data_iso"](data_competencia):
                    flash("Informe uma data de competência válida.", "danger")
                    return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))
                if not data_vencimento or not services["validar_data_iso"](data_vencimento):
                    flash("Informe uma data de vencimento válida.", "danger")
                    return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))

                if valor_original <= 0:
                    flash("Informe um valor original maior que zero.", "danger")
                    return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))
                if valor_desconto < 0 or valor_acrescimo < 0:
                    flash("Desconto e acréscimo não podem ser negativos.", "danger")
                    return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))

                valor_liquido = (valor_original - valor_desconto + valor_acrescimo).quantize(Decimal("0.01"))
                if valor_liquido <= 0:
                    flash("O valor líquido do título precisa ser maior que zero.", "danger")
                    return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))

                if forma_pagamento and forma_pagamento not in services["financeiro_base_formas_pagamento"]():
                    flash("Forma de pagamento inválida.", "danger")
                    return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))

                conta_caixa_prevista_id_int = None
                if conta_caixa_prevista_id:
                    if not conta_caixa_prevista_id.isdigit():
                        flash("Conta caixa inválida.", "danger")
                        return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))
                    conta_caixa_prevista_id_int = int(conta_caixa_prevista_id)

                cur.execute(
                    """SELECT id, nome_completo
                       FROM pessoas
                       WHERE id = %s AND empresa_id = %s AND status_cadastro = 'Ativo'
                       LIMIT 1""",
                    (pessoa_id, empresa_titulo_id),
                )
                pessoa = cur.fetchone()
                if not pessoa:
                    flash("Pessoa inválida ou não pertence à empresa do título.", "danger")
                    return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))

                if conta_caixa_prevista_id_int:
                    cur.execute(
                        """SELECT id
                           FROM contas_caixa
                           WHERE id = %s AND empresa_id = %s AND status_conta = 'Ativa'
                           LIMIT 1""",
                        (conta_caixa_prevista_id_int, empresa_titulo_id),
                    )
                    if not cur.fetchone():
                        flash("Conta caixa inválida, inativa ou pertencente a outra empresa.", "danger")
                        return redirect(url_for("financeiro.editar_titulo_financeiro", id=id))

                if not historico:
                    historico = f"{descricao} - Documento {numero_documento} - {pessoa['nome_completo']}"

                dados_antes = {
                    "pessoa_id": titulo.get("pessoa_id"),
                    "numero_documento": titulo.get("numero_documento"),
                    "descricao": titulo.get("descricao"),
                    "historico": titulo.get("historico"),
                    "valor_original": str(titulo.get("valor_original") or "0.00"),
                    "valor_desconto": str(titulo.get("valor_desconto") or "0.00"),
                    "valor_acrescimo": str(titulo.get("valor_acrescimo") or "0.00"),
                    "valor_liquido": str(titulo.get("valor_liquido") or "0.00"),
                    "data_emissao": str(titulo.get("data_emissao") or ""),
                    "data_competencia": str(titulo.get("data_competencia") or ""),
                    "data_vencimento": str(titulo.get("data_vencimento") or ""),
                    "forma_pagamento": titulo.get("forma_pagamento"),
                    "conta_caixa_prevista_id": titulo.get("conta_caixa_prevista_id"),
                    "observacao": titulo.get("observacao"),
                }
                dados_depois = {
                    "pessoa_id": pessoa_id,
                    "numero_documento": numero_documento,
                    "descricao": descricao,
                    "historico": historico,
                    "valor_original": str(valor_original),
                    "valor_desconto": str(valor_desconto),
                    "valor_acrescimo": str(valor_acrescimo),
                    "valor_liquido": str(valor_liquido),
                    "data_emissao": data_emissao,
                    "data_competencia": data_competencia,
                    "data_vencimento": data_vencimento,
                    "forma_pagamento": forma_pagamento or None,
                    "conta_caixa_prevista_id": conta_caixa_prevista_id_int,
                    "observacao": observacao or None,
                }

                cur.execute(
                    """
                    UPDATE titulos_financeiros
                    SET pessoa_id = %s,
                        numero_documento = %s,
                        descricao = %s,
                        historico = %s,
                        valor_original = %s,
                        valor_desconto = %s,
                        valor_acrescimo = %s,
                        valor_liquido = %s,
                        data_emissao = %s,
                        data_competencia = %s,
                        data_vencimento = %s,
                        forma_pagamento = %s,
                        conta_caixa_prevista_id = %s,
                        observacao = %s,
                        updated_at = NOW()
                    WHERE id = %s
                      AND empresa_id = %s
                      AND origem = 'MANUAL'
                      AND status_titulo = 'Aberto'
                      AND NOT EXISTS (
                          SELECT 1
                          FROM movimentacoes_caixa m
                          WHERE m.titulo_financeiro_id = titulos_financeiros.id
                            AND m.empresa_id = titulos_financeiros.empresa_id
                      )
                    """,
                    (
                        pessoa_id,
                        numero_documento,
                        descricao,
                        historico,
                        valor_original,
                        valor_desconto,
                        valor_acrescimo,
                        valor_liquido,
                        data_emissao,
                        data_competencia,
                        data_vencimento,
                        forma_pagamento or None,
                        conta_caixa_prevista_id_int,
                        observacao or None,
                        id,
                        empresa_titulo_id,
                    ),
                )
                if cur.rowcount != 1:
                    con.rollback()
                    flash("O título deixou de ser elegível para edição. Nenhuma alteração foi salva.", "warning")
                    return redirect(url_for("financeiro.detalhes_titulo_financeiro", id=id))

                cur.execute(
                    """INSERT INTO historico_operacoes
                       (empresa_id, tipo_operacao, usuario_id, status_anterior, status_novo, motivo, observacao)
                       VALUES (%s, 'TITULO_FINANCEIRO', %s, 'Aberto', 'Aberto',
                               'Edição de título manual', %s)""",
                    (empresa_titulo_id, usuario_id, f"Título manual #{id} editado. Documento: {numero_documento}."),
                )

                services["registrar_auditoria_financeira"](
                    cur,
                    empresa_id=empresa_titulo_id,
                    usuario_id=usuario_id,
                    acao="TITULO_MANUAL_EDITADO",
                    modulo="TITULOS_FINANCEIROS",
                    entidade_tipo="TITULO_FINANCEIRO",
                    entidade_id=id,
                    titulo_financeiro_id=id,
                    pessoa_id=pessoa_id,
                    status_anterior="Aberto",
                    status_novo="Aberto",
                    valor_anterior=titulo.get("valor_liquido"),
                    valor_novo=valor_liquido,
                    motivo="Edição de título financeiro manual",
                    observacao=f"Título manual #{id} editado. Documento: {numero_documento}.",
                    dados_antes=dados_antes,
                    dados_depois=dados_depois,
                )
                con.commit()
                flash(f"Título financeiro #{id} atualizado com sucesso.", "success")
                return redirect(url_for("financeiro.detalhes_titulo_financeiro", id=id))

            cur.execute(
                """SELECT id, nome_completo, cpf_cnpj
                   FROM pessoas
                   WHERE empresa_id = %s AND status_cadastro = 'Ativo'
                   ORDER BY nome_completo ASC""",
                (empresa_titulo_id,),
            )
            pessoas = cur.fetchall()

            cur.execute(
                """SELECT id, nome_conta
                   FROM contas_caixa
                   WHERE empresa_id = %s AND status_conta = 'Ativa'
                   ORDER BY nome_conta ASC""",
                (empresa_titulo_id,),
            )
            contas_caixa = cur.fetchall()

            return render_template(
                "financeiro_titulo_editar.html",
                usuario_logado=usuario_logado,
                titulo=titulo,
                pessoas=pessoas,
                contas_caixa=contas_caixa,
                formas_pagamento=services["financeiro_base_formas_pagamento"](),
                is_super_admin=is_super_admin,
            )

        except Exception as exc:
            try:
                con.rollback()
            except Exception:
                pass
            print(f"Erro ao editar título financeiro {id}: {exc}")
            flash("Erro técnico ao editar título financeiro.", "danger")
            return redirect(url_for("financeiro.detalhes_titulo_financeiro", id=id))
        finally:
            services["fechar_cursor_conexao"](cur, con)
