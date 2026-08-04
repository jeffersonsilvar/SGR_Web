# Mapeamento técnico inicial das rotas — SGR Web

> Inventário gerado por análise estática do `app.py`. Deve ser validado manualmente antes de qualquer movimentação de código.

## Resumo

- Rotas identificadas: **112**
- Domínios iniciais: **10**
- Funções analisadas no arquivo: **279**
- Linhas do `app.py`: **22657**

### Distribuição por domínio

| Domínio | Rotas |
|---|---:|
| Empresas e bases | 33 |
| Administração e acessos | 23 |
| Pessoas e cadastros | 16 |
| Motoristas | 15 |
| Financeiro | 9 |
| Rotas e divergências | 7 |
| Outros | 3 |
| Arquivos e integrações | 2 |
| Autenticação | 2 |
| Escalas e disponibilidade | 2 |

### Risco inicial estimado

| Risco | Rotas |
|---|---:|
| Baixo | 12 |
| Médio | 43 |
| Alto | 57 |

## Critérios usados

- **Domínio:** inferido por nomes de rota, função, templates e tabelas.
- **Autenticação:** indício detectado em decorators, sessão ou chamadas de permissão.
- **Risco baixo:** rota simples, normalmente leitura e poucas dependências.
- **Risco médio:** escrita ou múltiplas dependências.
- **Risco alto:** escrita, várias tabelas e fluxo interno mais complexo.
- A ausência de tabela ou autenticação na planilha **não prova** que a rota não as utilize; consultas e verificações indiretas podem escapar da análise estática.

## Inventário por domínio

### Administração e acessos

| Rota | Métodos | Função | Template(s) | Tabelas | Risco | Linhas |
|---|---|---|---|---|---|---:|
| `/` | GET | `dashboard` | dashboard.html | arquivos_sistema, auditoria_financeira, empresas, lancamentos_ajudantes, motorista_notas_fiscais, pessoas, rotas, titulos_financeiros, usuarios | Médio | 2293–2630 |
| `/pessoas/editar/<int:id>` | GET, POST | `editar_pessoa` | editar_pessoa.html | empresas, pessoas, usuarios | Alto | 4695–4975 |
| `/configuracao/usuarios/criar` | GET, POST | `criar_usuario` | criar_usuario.html | bases_operacionais, empresas, pessoas, usuarios | Alto | 7465–7594 |
| `/configuracao/usuarios/editar/<int:id>` | GET, POST | `editar_usuario` | editar_usuario.html | bases_operacionais, empresas, pessoas, usuarios | Alto | 7600–7804 |
| `/configuracao/usuarios` | GET | `visualizar_usuarios` | visualizar_usuarios.html | bases_operacionais, empresas, pessoas, usuarios | Médio | 7810–7907 |
| `/usuarios/alternar_status/<int:id>` | POST | `alternar_status_usuario` | — | usuarios | Alto | 7913–7984 |
| `/configuracoes/perfil-acesso` | GET | `perfil_acesso` | perfil_acesso.html | auditoria_permissoes, empresas, perfil_permissoes, perfis_acesso, sistema_menus, usuario_empresas_acesso, usuario_permissoes, usuarios | Médio | 8310–8472 |
| `/configuracoes/perfis/novo` | GET, POST | `novo_perfil_acesso_empresa` | perfil_acesso_form.html | empresas, perfis_acesso | Alto | 8497–8552 |
| `/configuracoes/perfis/<int:perfil_id>/permissoes` | GET, POST | `editar_permissoes_perfil_acesso` | perfil_permissoes_editar.html | perfil_permissoes, perfis_acesso, permitido | Alto | 8558–8620 |
| `/configuracoes/menus-modulos` | GET | `gerenciar_menus_modulos` | gerenciar_menus_modulos.html | — | Baixo | 8765–8785 |
| `/configuracoes/menus/novo` | GET, POST | `novo_menu_sistema` | menu_sistema_form.html | modulo_id, perfil_permissoes, permitido, sistema_menus | Alto | 8893–8945 |
| `/configuracoes/menus/<int:menu_id>/editar` | GET, POST | `editar_menu_sistema` | menu_sistema_form.html | sistema_menus | Alto | 8951–8994 |
| `/financeiro/historico-estornos` | GET | `historico_estornos` | historico_estornos.html | historico_operacoes, notas_fiscais, pessoas, rotas, usuarios | Médio | 9271–9315 |
| `/financeiro/pagamentos-ajudante/historico` | GET | `historico_pagamentos_ajudante` | historico_pagamentos_ajudante.html | historico_ajudante_pagamentos, pessoas, usuarios | Médio | 9816–9878 |
| `/empresas` | GET | `visualizar_empresas` | visualizar_empresas.html | empresas, pessoas, rotas, usuarios | Médio | 9887–9947 |
| `/financeiro/nfs-motoristas/<int:id>` | GET | `detalhes_nf_motorista` | detalhes_nf_motorista.html | empresas, motorista_nf_rotas, motorista_notas_fiscais, pessoas, rotas, titulos_financeiros, usuarios | Médio | 10531–10648 |
| `/operacao/relatorio-escala-base/exportar-excel` | GET | `exportar_relatorio_operacional_escala_base_excel` | — | auditoria_checkin_base, auditoria_supervisor, bases_operacionais, empresas, escala_motorista, fila_cancelados_base, pessoas, usuarios | Médio | 15705–16223 |
| `/operacao/auditoria-supervisor` | GET | `visualizar_auditoria_supervisor` | auditoria_supervisor.html | auditoria_supervisor, pessoas, usuarios | Médio | 16647–16714 |
| `/operacao/motoristas/<int:motorista_id>/historico` | GET | `historico_motorista_detalhe` | historico_motorista_detalhe.html | auditoria_checkin_base, bases_operacionais, ciencia_escala_motorista, empresas, escala_motorista, fila_cancelados_base, justificativas_ausencia_motorista, motorista_notas_fiscais, pessoas, rotas, usuarios | Médio | 17912–18106 |
| `/financeiro/auditoria` | GET | `financeiro_auditoria` | financeiro_auditoria.html | auditoria_financeira, empresas, pessoas, usuarios | Médio | 19674–19826 |
| `/financeiro/titulos/<int:id>` | GET | `detalhes_titulo_financeiro` | financeiro_titulo_detalhes.html | contas_caixa, empresas, movimentacoes_caixa, pessoas, titulos_financeiros, titulos_financeiros_vinculos, usuarios | Médio | 20864–20971 |
| `/financeiro/movimentacoes-caixa` | GET | `financeiro_movimentacoes_caixa` | financeiro_movimentacoes_caixa.html | contas_caixa, empresas, movimentacoes_caixa, pessoas, titulos_financeiros, usuarios | Médio | 21958–22097 |
| `/financeiro/conciliacao-caixa` | GET | `financeiro_conciliacao_caixa` | financeiro_conciliacao_caixa.html | contas_caixa, empresas, movimentacoes_caixa, pessoas, titulos_financeiros, usuarios | Médio | 22104–22291 |

### Arquivos e integrações

| Rota | Métodos | Função | Template(s) | Tabelas | Risco | Linhas |
|---|---|---|---|---|---|---:|
| `/arquivos/visualizar/<int:arquivo_id>` | GET | `visualizar_arquivo_sistema` | — | arquivos_sistema | Médio | 1784–1882 |
| `/arquivos/local/<path:caminho>` | GET | `visualizar_upload_local` | — | — | Baixo | 1887–1921 |

### Autenticação

| Rota | Métodos | Função | Template(s) | Tabelas | Risco | Linhas |
|---|---|---|---|---|---|---:|
| `/login` | GET, POST | `login` | login.html | empresas, perfis_acesso, pessoas, usuarios | Alto | 2047–2217 |
| `/logout` | GET | `logout` | — | — | Baixo | 2281–2284 |

### Empresas e bases

| Rota | Métodos | Função | Template(s) | Tabelas | Risco | Linhas |
|---|---|---|---|---|---|---:|
| `/portal-motorista/minhas-rotas` | GET | `minhas_rotas_motorista` | minhas_rotas_motorista.html | empresas, pessoas, rotas | Médio | 2916–3064 |
| `/portal-motorista/enviar-nf` | GET, POST | `enviar_nf_motorista` | enviar_nf_motorista.html | empresas, motorista_nf_rotas, motorista_notas_fiscais, pessoas, rotas | Alto | 3320–3721 |
| `/pessoas/cadastro` | GET, POST | `cadastro_pessoa` | cadastro_pessoa.html | empresas, pessoas | Alto | 4355–4560 |
| `/pessoas/visualizar` | GET | `visualizar_pessoas` | visualizar_pessoas.html | empresas, pessoas | Médio | 4566–4689 |
| `/api/pessoas/buscar` | GET | `api_buscar_pessoas` | — | empresas, pessoas | Médio | 5037–5135 |
| `/movimentacao/visualizar` | GET | `visualizar_rotas` | visualizar_rotas.html | empresas, pessoas, rotas | Médio | 5402–5632 |
| `/movimentacao/rotas/divergencias` | GET | `divergencias_rotas_motoristas` | rotas_divergencias.html | empresas, pessoas, rotas, rotas_divergencias_motorista | Médio | 5639–5762 |
| `/empresas/cadastro` | GET, POST | `cadastro_empresa` | cadastro_empresa.html | empresas | Alto | 9956–10067 |
| `/empresas/editar/<int:id>` | GET, POST | `editar_empresa` | editar_empresa.html | empresas | Alto | 10076–10242 |
| `/financeiro/nfs-motoristas` | GET | `financeiro_nfs_motoristas` | financeiro_nfs_motoristas.html | empresas, motorista_nf_rotas, motorista_notas_fiscais, pessoas, rotas, titulos_financeiros | Médio | 10316–10525 |
| `/portal-motorista/solicitar-pagamento-sem-nf` | GET, POST | `solicitar_pagamento_sem_nf_motorista` | solicitar_pagamento_sem_nf_motorista.html | empresas, motorista_nf_rotas, motorista_notas_fiscais, pessoas, rotas | Alto | 10764–10962 |
| `/operacao/bases-operacionais` | GET | `visualizar_bases_operacionais` | visualizar_bases_operacionais.html | bases_operacionais, empresas | Médio | 11943–12037 |
| `/operacao/bases-operacionais/cadastro` | GET, POST | `cadastro_base_operacional` | cadastro_base_operacional.html | bases_operacionais, empresas | Alto | 12043–12170 |
| `/operacao/bases-operacionais/editar/<int:id>` | GET, POST | `editar_base_operacional` | editar_base_operacional.html | bases_operacionais | Alto | 12176–12301 |
| `/operacao/escala-motoristas` | GET, POST | `escala_motoristas` | escala_motoristas.html | empresas, escala_motorista, status_escala | Alto | 12650–12937 |
| `/portal-motorista/minha-semana` | GET, POST | `minha_semana_motorista` | minha_semana_motorista.html | bases_operacionais, ciencia_escala_motorista, data_ciencia, escala_motorista, fila_cancelados_base, justificativas_ausencia_motorista, motivo | Alto | 13794–14409 |
| `/terminal-base/qrcode` | GET | `terminal_base_qrcode` | terminal_base_qrcode.html | bases_operacionais | Médio | 14567–14626 |
| `/terminal-base/qrcode/atualizar` | GET | `terminal_base_qrcode_atualizar` | — | bases_operacionais | Baixo | 14632–14694 |
| `/operacao/auditoria-checkin-base` | GET | `auditoria_checkin_base` | auditoria_checkin_base.html | auditoria_checkin_base, base_qr_tokens, bases_operacionais, escala_motorista, pessoas | Médio | 14765–14899 |
| `/operacao/mapa-checkins` | GET | `mapa_checkins` | mapa_checkins.html | auditoria_checkin_base, bases_operacionais, escala_motorista, pessoas | Médio | 14905–15100 |
| `/operacao/auditoria-checkin-base/exportar-csv` | GET | `exportar_auditoria_checkin_base_csv` | — | auditoria_checkin_base, bases_operacionais, pessoas | Médio | 15106–15193 |
| `/operacao/relatorio-escala-base` | GET | `relatorio_operacional_escala_base` | relatorio_operacional_escala_base.html | auditoria_checkin_base, bases_operacionais, escala_motorista, fila_cancelados_base, pessoas | Médio | 15202–15596 |
| `/operacao/relatorio-escala-base/exportar-csv` | GET | `exportar_relatorio_operacional_escala_base_csv` | — | bases_operacionais, escala_motorista, fila_cancelados_base, pessoas | Médio | 15602–15699 |
| `/operacao/relatorio-escala-base/exportar-pdf` | GET | `exportar_relatorio_operacional_escala_base_pdf` | — | auditoria_checkin_base, bases_operacionais, empresas, escala_motorista, fila_cancelados_base, pessoas | Médio | 16230–16641 |
| `/operacao/central-pendencias` | GET | `central_pendencias_operacao` | central_pendencias_operacao.html | auditoria_checkin_base, base_qr_tokens, bases_operacionais, ciencia_escala_motorista, disponibilidade_motorista, escala_motorista, fila_cancelados_base, justificativas_ausencia_motorista, pessoas | Médio | 17164–17556 |
| `/financeiro/configuracoes` | GET, POST | `financeiro_configuracoes` | financeiro_configuracoes.html | empresas, historico_operacoes | Alto | 18881–18988 |
| `/configuracoes/operacional-motorista` | GET, POST | `configuracoes_operacionais_motorista` | configuracoes_operacionais_motorista.html | configuracoes_disponibilidade, configuracoes_escala_motorista, empresas, historico_operacoes | Alto | 18994–19123 |
| `/relatorios` | GET | `relatorios_central` | relatorios_central.html | arquivos_sistema, auditoria_financeira, empresas, rotas, titulos_financeiros | Médio | 19311–19388 |
| `/relatorios/financeiro` | GET | `relatorios_financeiro` | relatorios_financeiro.html | contas_caixa, empresas, pessoas, titulos_financeiros | Médio | 19394–19531 |
| `/financeiro/dashboard` | GET | `financeiro_dashboard` | financeiro_dashboard.html | contas_caixa, empresas, movimentacoes_caixa, pessoas, titulos_financeiros | Médio | 19832–20151 |
| `/financeiro/titulos` | GET | `financeiro_titulos` | financeiro_titulos.html | contas_caixa, empresas, pessoas, titulos_financeiros | Médio | 20157–20377 |
| `/financeiro/titulos/novo` | GET, POST | `novo_titulo_financeiro` | financeiro_titulo_form.html | contas_caixa, empresas, pessoas, titulos_financeiros | Alto | 20383–20600 |
| `/financeiro/contas-caixa/nova` | GET, POST | `nova_conta_caixa` | financeiro_conta_caixa_form.html | contas_caixa, empresas | Alto | 22477–22555 |

### Escalas e disponibilidade

| Rota | Métodos | Função | Template(s) | Tabelas | Risco | Linhas |
|---|---|---|---|---|---|---:|
| `/operacao/fila-cancelados/<int:fila_id>/atribuir-rota` | POST | `atribuir_rota_extra_fila_cancelado` | — | — | Baixo | 13579–13584 |
| `/operacao/fila-cancelados/<int:fila_id>/dispensar` | POST | `dispensar_fila_cancelado` | — | — | Baixo | 13590–13595 |

### Financeiro

| Rota | Métodos | Função | Template(s) | Tabelas | Risco | Linhas |
|---|---|---|---|---|---|---:|
| `/relatorios/financeiro/exportar-csv` | GET | `relatorios_financeiro_exportar_csv` | — | — | Baixo | 19570–19594 |
| `/relatorios/financeiro/exportar-excel` | GET | `relatorios_financeiro_exportar_excel` | — | — | Baixo | 19600–19664 |
| `/financeiro/titulos/<int:id>/cancelar` | POST | `cancelar_titulo_financeiro` | — | titulos_financeiros | Alto | 20976–21043 |
| `/financeiro/titulos/<int:id>/baixar` | POST | `baixar_titulo_financeiro` | — | contas_caixa, movimentacoes_caixa, titulos_financeiros | Alto | 21051–21307 |
| `/financeiro/titulos/<int:id>/estornar` | POST | `estornar_baixa_titulo_financeiro` | — | historico_operacoes, movimentacoes_caixa, titulos_financeiros | Alto | 21508–21780 |
| `/financeiro/titulos/<int:id>/tratativa-pos-estorno` | POST | `tratar_pos_estorno_titulo_financeiro` | — | historico_operacoes, titulos_financeiros | Alto | 21790–21951 |
| `/financeiro/conciliacao-caixa/acao` | POST | `financeiro_conciliacao_caixa_acao` | — | movimentacoes_caixa | Alto | 22297–22420 |
| `/financeiro/contas-caixa` | GET | `financeiro_contas_caixa` | financeiro_contas_caixa.html | — | Baixo | 22425–22471 |
| `/financeiro/contas-caixa/<int:id>/editar` | GET, POST | `editar_conta_caixa` | financeiro_conta_caixa_form.html | contas_caixa | Alto | 22561–22653 |

### Motoristas

| Rota | Métodos | Função | Template(s) | Tabelas | Risco | Linhas |
|---|---|---|---|---|---|---:|
| `/portal-motorista/minhas-rotas/<int:rota_id>/confirmar` | POST | `confirmar_rota_motorista` | — | rotas | Alto | 3070–3151 |
| `/portal-motorista/minhas-rotas/<int:rota_id>/divergencia` | POST | `apontar_divergencia_rota_motorista` | — | rotas, rotas_divergencias_motorista | Alto | 3157–3266 |
| `/portal-motorista/minhas-nfs` | GET | `minhas_nfs_motorista` | minhas_nfs_motorista.html | motorista_nf_rotas, motorista_notas_fiscais, rotas | Médio | 3844–3921 |
| `/portal-motorista/nfs/<int:nf_id>/danfse` | GET | `visualizar_danfse_nf` | visualizar_danfse_nf.html | — | Baixo | 3925–3956 |
| `/portal-motorista/nfs/<int:nf_id>/xml-original` | GET | `baixar_xml_nf_original` | — | — | Baixo | 3961–3991 |
| `/financeiro/nfs-motoristas/<int:id>/aprovar` | POST | `aprovar_documento_motorista` | — | motorista_nf_rotas, motorista_notas_fiscais, rotas | Alto | 4037–4161 |
| `/financeiro/nfs-motoristas/<int:id>/recusar` | POST | `recusar_documento_motorista` | — | motorista_nf_rotas, motorista_notas_fiscais, rotas | Alto | 4167–4349 |
| `/movimentacao/rotas/divergencias/<int:divergencia_id>/tratar` | POST | `tratar_divergencia_rota_motorista` | — | rotas, rotas_divergencias_motorista | Alto | 5768–5882 |
| `/movimentacao/rotas/<int:id>/bloquear-motorista` | POST | `bloquear_rota_motorista` | — | rotas | Alto | 6139–6221 |
| `/financeiro/nfs-motoristas/<int:id>/marcar-analise` | POST | `marcar_nf_motorista_em_analise` | — | motorista_nf_rotas, motorista_notas_fiscais, rotas | Alto | 10654–10753 |
| `/financeiro/nfs-motoristas/<int:id>/reverter-aprovacao` | POST | `reverter_aprovacao_documento_motorista` | — | motorista_nf_rotas, motorista_notas_fiscais, rotas | Alto | 10975–11126 |
| `/financeiro/nfs-motoristas/<int:id>/confirmar-pagamento` | POST | `confirmar_pagamento_documento_motorista` | — | motorista_nf_rotas, motorista_notas_fiscais, rotas | Alto | 11135–11288 |
| `/financeiro/nfs-motoristas/<int:id>/estornar-pagamento` | POST | `estornar_pagamento_documento_motorista` | — | motorista_nf_rotas, motorista_notas_fiscais, rotas | Alto | 11294–11453 |
| `/portal-motorista/disponibilidade` | GET, POST | `disponibilidade_motorista` | disponibilidade_motorista.html | disponibilidade_motorista, status_disponibilidade | Alto | 11622–11816 |
| `/financeiro/nfs-motoristas/<int:id>/solicitar-pagamento` | POST | `solicitar_pagamento_nf_motorista` | — | motorista_notas_fiscais | Alto | 18316–18397 |

### Outros

| Rota | Métodos | Função | Template(s) | Tabelas | Risco | Linhas |
|---|---|---|---|---|---|---:|
| `/inicio` | GET | `inicio_sem_modulos` | — | — | Baixo | 1982–2043 |
| `/configuracoes/modulos/novo` | GET, POST | `novo_modulo_sistema` | modulo_sistema_form.html | nome, sistema_modulos | Alto | 8791–8825 |
| `/configuracoes/modulos/<int:modulo_id>/editar` | GET, POST | `editar_modulo_sistema` | modulo_sistema_form.html | sistema_modulos | Alto | 8831–8864 |

### Pessoas e cadastros

| Rota | Métodos | Função | Template(s) | Tabelas | Risco | Linhas |
|---|---|---|---|---|---|---:|
| `/portal-motorista` | GET | `portal_motorista` | portal_motorista.html | pessoas, rotas | Médio | 2636–2851 |
| `/portal-motorista/nfs/<int:id>/xml` | GET | `visualizar_xml_nf_motorista` | — | motorista_notas_fiscais, pessoas | Médio | 3749–3838 |
| `/pessoas/excluir/<int:id>` | POST | `excluir_pessoa` | — | pessoas | Alto | 4981–5032 |
| `/movimentacao/lancar` | GET, POST | `lancar_rota` | lancar_rota.html | pessoas, rotas | Alto | 5144–5316 |
| `/movimentacao/editar/<int:id>` | GET, POST | `editar_rota` | editar_rota.html | pessoas, rotas | Alto | 6227–6447 |
| `/rotas/lancamento-ajudante` | GET, POST | `lancamento_ajudante` | lancamento_ajudante.html | lancamento_ajudante_rotas, lancamentos_ajudantes, pessoas, rotas | Alto | 6537–6751 |
| `/faturamento` | GET | `faturamento` | faturamento.html | nota_fiscal_rotas, notas_fiscais, pessoas, rotas | Médio | 6760–6848 |
| `/processar-faturamento` | POST | `processar_faturamento` | — | historico_operacoes, nota_fiscal_rotas, notas_fiscais, pessoas, rotas | Alto | 6854–7127 |
| `/financeiro/recebimento` | GET | `recebimento` | recebimento.html | nota_fiscal_rotas, notas_fiscais, pessoas, rotas | Médio | 7177–7244 |
| `/financeiro/pagamentos-ajudante` | GET | `pagamentos_ajudante` | pagamentos_ajudante.html | lancamento_ajudante_rotas, lancamentos_ajudantes, pessoas | Médio | 9326–9433 |
| `/financeiro/pagamentos-ajudante/baixar/<int:lancamento_id>` | POST | `baixar_pagamento_ajudante` | — | historico_ajudante_pagamentos, lancamento_ajudante_rotas, lancamentos_ajudantes, pessoas | Alto | 9439–9551 |
| `/financeiro/pagamentos-ajudante/estornar-baixa/<int:lancamento_id>` | POST | `estornar_baixa_pagamento_ajudante` | — | historico_ajudante_pagamentos, lancamento_ajudante_rotas, lancamentos_ajudantes, pessoas | Alto | 9557–9669 |
| `/financeiro/pagamentos-ajudante/estornar-lancamento/<int:lancamento_id>` | POST | `estornar_lancamento_ajudante` | — | historico_ajudante_pagamentos, lancamento_ajudante_rotas, lancamentos_ajudantes, pessoas | Alto | 9675–9810 |
| `/operacao/score-motoristas` | GET | `score_motoristas` | score_motoristas.html | auditoria_checkin_base, ciencia_escala_motorista, disponibilidade_motorista, escala_motorista, fila_cancelados_base, pessoas | Médio | 16723–17155 |
| `/operacao/justificativas-ausencia/<int:justificativa_id>/analisar` | POST | `analisar_justificativa_ausencia` | — | escala_motorista, justificativas_ausencia_motorista, pessoas | Alto | 17562–17691 |
| `/operacao/historico-motoristas` | GET | `historico_motoristas` | historico_motoristas.html | auditoria_checkin_base, escala_motorista, fila_cancelados_base, justificativas_ausencia_motorista, pessoas | Médio | 17702–17906 |

### Rotas e divergências

| Rota | Métodos | Função | Template(s) | Tabelas | Risco | Linhas |
|---|---|---|---|---|---|---:|
| `/movimentacao/rotas/<int:id>/liberar-nf` | POST | `liberar_rota_para_nf` | — | rotas | Alto | 5888–5970 |
| `/movimentacao/rotas/liberar-em-massa-nf` | POST | `liberar_rotas_em_massa_para_nf` | — | rotas | Alto | 5976–6133 |
| `/movimentacao/excluir/<int:id>` | POST | `excluir_rota` | — | lancamento_ajudante_rotas, nota_fiscal_rotas, rotas | Alto | 6453–6528 |
| `/faturamento/contingencia/<int:id>` | POST | `contingencia_quitar_rota` | — | rotas | Médio | 7133–7168 |
| `/financeiro/recebimento/confirmar/<int:id>` | POST | `confirmar_recebimento` | — | historico_operacoes, nota_fiscal_rotas, notas_fiscais, rotas | Alto | 7254–7349 |
| `/faturamento/estornar/<int:nota_id>` | POST | `estornar_faturamento` | — | historico_operacoes, nota_fiscal_rotas, notas_fiscais, rotas | Alto | 9028–9155 |
| `/financeiro/recebimento/estornar/<int:nota_id>` | POST | `estornar_recebimento` | — | historico_operacoes, nota_fiscal_rotas, notas_fiscais, rotas | Alto | 9166–9262 |
