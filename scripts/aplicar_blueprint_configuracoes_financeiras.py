from pathlib import Path
import ast
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

NEW_DEFAULTS = "PARAMETROS_FINANCEIROS_PADRAO = {\n    'baixa.exigir_comprovante': {\n        'grupo': 'baixa', 'tipo': 'boolean', 'valor': '0',\n        'descricao': 'Exigir comprovante na baixa financeira.'\n    },\n    'baixa.permitir_data_retroativa': {\n        'grupo': 'baixa', 'tipo': 'boolean', 'valor': '1',\n        'descricao': 'Permitir baixa com data anterior à data atual.'\n    },\n    'baixa.limite_dias_retroativo': {\n        'grupo': 'baixa', 'tipo': 'integer', 'valor': '30',\n        'descricao': 'Limite máximo, em dias, para baixa retroativa. Zero significa sem limite quando habilitada.'\n    },\n    'caixa.permitir_saldo_negativo': {\n        'grupo': 'caixa', 'tipo': 'boolean', 'valor': '0',\n        'descricao': 'Permitir pagamento mesmo quando a conta caixa não possui saldo suficiente.'\n    },\n    'caixa.conta_padrao_id': {\n        'grupo': 'caixa', 'tipo': 'integer', 'valor': '',\n        'descricao': 'Conta caixa padrão sugerida nas operações financeiras.'\n    },\n    'caixa.forma_pagamento_padrao': {\n        'grupo': 'caixa', 'tipo': 'string', 'valor': 'PIX',\n        'descricao': 'Forma de pagamento padrão para títulos e documentos.'\n    },\n    'documentos.permitir_sem_nf_pf': {\n        'grupo': 'documentos', 'tipo': 'boolean', 'valor': '1',\n        'descricao': 'Permitir solicitação de pagamento sem NF para prestador pessoa física.'\n    },\n    'documentos.permitir_reaproveitar_pos_estorno': {\n        'grupo': 'documentos', 'tipo': 'boolean', 'valor': '1',\n        'descricao': 'Permitir reaproveitar documento fiscalmente válido após estorno.'\n    },\n    'titulos.modo_geracao_documento': {\n        'grupo': 'titulos', 'tipo': 'string', 'valor': 'AUTOMATICO',\n        'descricao': 'Modo de geração do título ao solicitar pagamento de documento aprovado.'\n    },\n    'titulos.dias_padrao_vencimento_motorista': {\n        'grupo': 'titulos', 'tipo': 'integer', 'valor': '5',\n        'descricao': 'Prazo padrão, em dias, para vencimento de títulos de prestadores/motoristas.'\n    },\n}\n"
HELPER_SRC = 'def _dias_vencimento_pagamento_nf_motorista(empresa_id, cur=None):\n    """Prazo configurado por empresa para títulos gerados por documento de motorista."""\n    try:\n        return max(0, int(obter_parametro_empresa(\n            empresa_id,\n            \'titulos.dias_padrao_vencimento_motorista\',\n            5,\n            cur=cur,\n        )))\n    except Exception:\n        return 5\n'
SOLICITAR_SRC = '@app.route(\'/financeiro/nfs-motoristas/<int:id>/solicitar-pagamento\', methods=[\'POST\'])\n@login_required\n@financeiro_nf_motorista_required\ndef solicitar_pagamento_nf_motorista(id):\n    empresa_logada_id = session.get(\'empresa_id\')\n    usuario_id = session.get(\'usuario_id\')\n    is_super_admin = int(session.get(\'is_super_admin\') or 0) == 1\n\n    if not empresa_logada_id:\n        flash("Empresa não identificada na sessão. Faça login novamente.", "danger")\n        return redirect(url_for(\'logout\'))\n\n    con = obter_conexao()\n    if con is None:\n        flash("Erro de conexão com o banco de dados.", "danger")\n        return redirect(url_for(\'financeiro_nfs_motoristas\'))\n\n    cur = con.cursor(dictionary=True)\n    try:\n        query = """\n            SELECT id, empresa_id, numero_nf, status_nf\n            FROM motorista_notas_fiscais\n            WHERE id = %s\n        """\n        params = [id]\n        if not is_super_admin:\n            query += " AND empresa_id = %s"\n            params.append(empresa_logada_id)\n        query += " LIMIT 1"\n        cur.execute(query, params)\n        nf = cur.fetchone()\n\n        if not nf:\n            flash("Documento do motorista não encontrado ou não pertence à empresa logada.", "danger")\n            return redirect(url_for(\'financeiro_nfs_motoristas\'))\n\n        parametros = carregar_parametros_financeiros_empresa(nf[\'empresa_id\'], cur=cur)\n        modo = str(\n            parametros.get(\'titulos.modo_geracao_documento\', {}).get(\'valor\')\n            or \'AUTOMATICO\'\n        ).upper()\n        forma_padrao = (\n            parametros.get(\'caixa.forma_pagamento_padrao\', {}).get(\'valor\')\n            or \'PIX\'\n        )\n        conta_padrao = str(\n            parametros.get(\'caixa.conta_padrao_id\', {}).get(\'valor\') or \'\'\n        ).strip()\n        conta_prevista_id = int(conta_padrao) if conta_padrao.isdigit() else None\n\n        if conta_prevista_id:\n            cur.execute("""\n                SELECT id\n                FROM contas_caixa\n                WHERE id = %s\n                  AND empresa_id = %s\n                  AND status_conta = \'Ativa\'\n                LIMIT 1\n            """, (conta_prevista_id, nf[\'empresa_id\']))\n            if not cur.fetchone():\n                conta_prevista_id = None\n\n        if modo == \'ASSISTIDO\':\n            data_vencimento = (\n                request.form.get(\'data_vencimento\') or \'\'\n            ).strip()\n            forma_pagamento = (\n                request.form.get(\'forma_pagamento\') or forma_padrao\n            ).strip()\n\n            if not data_vencimento or not validar_data_iso(data_vencimento):\n                flash(\'Informe uma data de vencimento válida.\', \'warning\')\n                return redirect(url_for(\'detalhes_nf_motorista\', id=id))\n\n            if forma_pagamento not in financeiro_base_formas_pagamento():\n                flash(\'Selecione uma forma de pagamento válida.\', \'warning\')\n                return redirect(url_for(\'detalhes_nf_motorista\', id=id))\n        else:\n            data_vencimento = None\n            forma_pagamento = (\n                forma_padrao\n                if forma_padrao in financeiro_base_formas_pagamento()\n                else \'PIX\'\n            )\n\n        titulo_id, msg = gerar_titulo_financeiro_por_nf_motorista(\n            cur,\n            nf_id=id,\n            empresa_id=nf[\'empresa_id\'],\n            usuario_id=usuario_id,\n            data_vencimento=data_vencimento,\n            forma_pagamento=forma_pagamento,\n            conta_caixa_prevista_id=conta_prevista_id,\n        )\n\n        registrar_auditoria_financeira(\n            cur,\n            empresa_id=nf[\'empresa_id\'],\n            usuario_id=usuario_id,\n            acao=\'TITULO_GERADO_DOCUMENTO_MOTORISTA\',\n            modulo=\'DOCUMENTOS_MOTORISTAS\',\n            entidade_tipo=\'MOTORISTA_NOTA_FISCAL\',\n            entidade_id=id,\n            titulo_financeiro_id=titulo_id,\n            status_anterior=nf.get(\'status_nf\'),\n            status_novo=\'Pagamento solicitado\',\n            motivo=\'Solicitação de pagamento de documento\',\n            observacao=msg,\n            dados_depois={\n                \'numero_nf\': nf.get(\'numero_nf\'),\n                \'modo_geracao\': modo,\n                \'forma_pagamento\': forma_pagamento,\n                \'data_vencimento\': (\n                    data_vencimento or \'PADRAO_CONFIGURADO\'\n                ),\n                \'conta_caixa_prevista_id\': conta_prevista_id,\n            },\n        )\n        con.commit()\n\n        registrar_historico_nf_motorista(\n            empresa_id=nf[\'empresa_id\'],\n            motorista_nf_id=id,\n            usuario_id=usuario_id,\n            status_anterior=\'Aprovada\',\n            status_novo=_status_nf_motorista_com_pagamento_solicitado(),\n            motivo=\'Solicitação de pagamento\',\n            observacao=(\n                f"{msg} O título entrou em Contas a Pagar como Solicitado."\n            ),\n        )\n\n        flash(f"Pagamento solicitado com sucesso. {msg}", "success")\n        return redirect(\n            url_for(\'financeiro.detalhes_titulo_financeiro\', id=titulo_id)\n        )\n\n    except Exception as e:\n        con.rollback()\n        print(f"Erro ao solicitar pagamento da NF motorista {id}: {e}")\n        flash(f"Erro ao solicitar pagamento: {e}", "danger")\n        return redirect(url_for(\'detalhes_nf_motorista\', id=id))\n    finally:\n        fechar_cursor_conexao(cur, con)\n'


def top_level_span(text, name):
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
            return start, node.end_lineno
    raise RuntimeError(f"Função {name} não encontrada.")


def replace_function(text, name, new_source):
    lines = text.splitlines(keepends=True)
    start, end = top_level_span(text, name)
    lines[start:end] = [new_source.rstrip() + "\n\n"]
    return "".join(lines)


def remove_function(text, name):
    lines = text.splitlines(keepends=True)
    start, end = top_level_span(text, name)
    del lines[start:end]
    return "".join(lines)


def replace_assignment(text, name, new_source):
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            lines[node.lineno - 1:node.end_lineno] = [
                new_source.rstrip() + "\n\n"
            ]
            return "".join(lines)
    raise RuntimeError(f"Atribuição {name} não encontrada.")


def main():
    backup = ROOT / "app.py.blueprint13-backup"
    shutil.copy2(APP, backup)
    text = APP.read_text(encoding="utf-8")

    text = replace_assignment(
        text,
        "PARAMETROS_FINANCEIROS_PADRAO",
        NEW_DEFAULTS,
    )
    text = remove_function(text, "financeiro_configuracoes")
    text = replace_function(
        text,
        "_dias_vencimento_pagamento_nf_motorista",
        HELPER_SRC,
    )
    text = replace_function(
        text,
        "solicitar_pagamento_nf_motorista",
        SOLICITAR_SRC,
    )

    old_sig = (
        "def gerar_titulo_financeiro_por_nf_motorista(cur, nf_id, "
        "empresa_id, usuario_id, data_vencimento=None, forma_pagamento='PIX'):"
    )
    new_sig = (
        "def gerar_titulo_financeiro_por_nf_motorista(cur, nf_id, "
        "empresa_id, usuario_id, data_vencimento=None, "
        "forma_pagamento='PIX', conta_caixa_prevista_id=None):"
    )
    if old_sig not in text:
        raise RuntimeError("Assinatura de geração de título não encontrada.")
    text = text.replace(old_sig, new_sig, 1)

    old_due = (
        "data_vencimento = (hoje + timedelta(days="
        "_dias_vencimento_pagamento_nf_motorista())).strftime('%Y-%m-%d')"
    )
    new_due = (
        "data_vencimento = (hoje + timedelta(days="
        "_dias_vencimento_pagamento_nf_motorista("
        "empresa_id, cur=cur))).strftime('%Y-%m-%d')"
    )
    if old_due not in text:
        raise RuntimeError("Prazo fixo da NF não encontrado.")
    text = text.replace(old_due, new_due, 1)

    old_values = "%s, NULL, 'Solicitado', %s,"
    if old_values not in text:
        raise RuntimeError("Conta prevista fixa NULL não encontrada.")
    text = text.replace(
        old_values,
        "%s, %s, 'Solicitado', %s,",
        1,
    )

    old_params = (
        "        forma_pagamento or 'PIX',\n"
        "        observacao_geracao,"
    )
    new_params = (
        "        forma_pagamento or 'PIX',\n"
        "        conta_caixa_prevista_id,\n"
        "        observacao_geracao,"
    )
    if old_params not in text:
        raise RuntimeError("Parâmetros do INSERT de título não encontrados.")
    text = text.replace(old_params, new_params, 1)

    # Política real: sem NF somente quando habilitado e somente para CPF.
    start, end = top_level_span(
        text,
        "solicitar_pagamento_sem_nf_motorista",
    )
    lines = text.splitlines(keepends=True)
    frag = "".join(lines[start:end])
    needle = """    if not motorista:
        flash("Seu usuário não está vinculado a um motorista ativo nesta empresa.", "danger")
        return redirect(url_for('portal_motorista'))

    motorista_id = motorista['id']
"""
    replacement = """    if not motorista:
        flash("Seu usuário não está vinculado a um motorista ativo nesta empresa.", "danger")
        return redirect(url_for('portal_motorista'))

    parametros_financeiros = carregar_parametros_financeiros_empresa(
        empresa_id
    )
    if not parametro_bool(
        parametros_financeiros.get(
            'documentos.permitir_sem_nf_pf',
            {},
        ).get('valor')
    ):
        flash(
            'Solicitação de pagamento sem NF está desabilitada para esta empresa.',
            'warning'
        )
        return redirect(url_for('portal_motorista'))

    if len(somente_digitos(motorista.get('cpf_cnpj'))) != 11:
        flash(
            'Pagamento sem NF é permitido somente para prestador pessoa física (CPF).',
            'warning'
        )
        return redirect(url_for('portal_motorista'))

    motorista_id = motorista['id']
"""
    if needle not in frag:
        raise RuntimeError("Ponto de política SEM_NF não encontrado.")
    frag = frag.replace(needle, replacement, 1)
    lines[start:end] = [frag]
    text = "".join(lines)

    old_menu = (
        "('FINANCEIRO', 'gestao_financeira', "
        "'financeiro_configuracoes', 'Configurações Financeiras', "
        "'financeiro_configuracoes',"
    )
    new_menu = (
        "('FINANCEIRO', 'gestao_financeira', "
        "'financeiro_configuracoes', 'Configurações Financeiras', "
        "'financeiro.financeiro_configuracoes',"
    )
    if old_menu not in text:
        raise RuntimeError("Endpoint de menu financeiro não encontrado.")
    text = text.replace(old_menu, new_menu, 1)

    marker = (
        '    "aplicar_estorno_em_documento_motorista_e_rotas": '
        'aplicar_estorno_em_documento_motorista_e_rotas,\n'
    )
    addition = marker + (
        '    "PARAMETROS_FINANCEIROS_PADRAO": '
        'PARAMETROS_FINANCEIROS_PADRAO,\n'
        '    "salvar_parametro_empresa": salvar_parametro_empresa,\n'
    )
    if marker not in text:
        raise RuntimeError("Marcador financeiro_services não encontrado.")
    text = text.replace(marker, addition, 1)

    APP.write_text(text, encoding="utf-8")
    print(f"[ok] Backup criado: {backup.name}")
    print("[ok] Configurações financeiras saneadas.")
    print("[ok] Geração automática/assistida conectada.")
    print("[ok] Rota antiga de configurações removida do app.py.")


if __name__ == "__main__":
    main()
