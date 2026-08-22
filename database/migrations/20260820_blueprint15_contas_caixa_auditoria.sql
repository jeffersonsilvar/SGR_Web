-- Blueprint 15 — Contas Caixa + Auditoria Financeira
-- Atualiza apenas referências de endpoint do menu dinâmico.
-- Não altera permissões nem códigos dos menus.

UPDATE sistema_menus
SET endpoint = 'financeiro.financeiro_auditoria',
    atualizado_em = CURRENT_TIMESTAMP
WHERE endpoint = 'financeiro_auditoria';

-- Contas Caixa já utiliza a listagem do Blueprint como item de menu.
-- As rotas nova/editar são ações internas da tela e não precisam de item próprio.
