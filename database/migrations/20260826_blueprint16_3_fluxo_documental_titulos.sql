-- Blueprint 16.3 — Fluxo documental e geração controlada de títulos
-- Compatível com MySQL 5.6.
-- Não cria pagamento direto e não altera documentos legados de motoristas.

-- A Etapa 16.3 habilita ações de fluxo (análise/aprovação/recusa/geração de título)
-- para os mesmos perfis que já podem visualizar Documentos Fiscais.
INSERT INTO perfil_permissoes (
    perfil_de_acesso, menu_codigo, acao_codigo, empresa_id, permitido
)
SELECT
    pp.perfil_de_acesso,
    'documentos_fiscais',
    'editar',
    pp.empresa_id,
    pp.permitido
FROM perfil_permissoes pp
WHERE pp.menu_codigo = 'documentos_fiscais'
  AND pp.acao_codigo = 'visualizar'
  AND pp.permitido = 1
  AND NOT EXISTS (
      SELECT 1
      FROM perfil_permissoes atual
      WHERE atual.perfil_de_acesso = pp.perfil_de_acesso
        AND atual.menu_codigo = 'documentos_fiscais'
        AND atual.acao_codigo = 'editar'
        AND atual.empresa_id = pp.empresa_id
  );
