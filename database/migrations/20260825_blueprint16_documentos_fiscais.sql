-- Blueprint 16.1 — Central de Documentos Fiscais
-- Compatível com MySQL 5.6.
-- Não remove nem altera o menu legado de Documentos Motoristas.

SET @modulo_financeiro_id := (
    SELECT id FROM sistema_modulos WHERE codigo = 'FINANCEIRO' LIMIT 1
);

SET @menu_pai_financeiro_id := (
    SELECT id FROM sistema_menus WHERE codigo = 'gestao_financeira' LIMIT 1
);

INSERT INTO sistema_menus (
    modulo_id, menu_pai_id, grupo_menu, codigo, titulo,
    endpoint, rota_url, icone, ordem, ativo, visivel_menu
)
SELECT
    @modulo_financeiro_id,
    @menu_pai_financeiro_id,
    'FINANCEIRO',
    'documentos_fiscais',
    'Documentos Fiscais',
    'documentos.central_documentos_fiscais',
    NULL,
    'fa-solid fa-file-invoice',
    70,
    1,
    1
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1 FROM sistema_menus WHERE codigo = 'documentos_fiscais'
);

UPDATE sistema_menus
SET titulo = 'Documentos Fiscais',
    endpoint = 'documentos.central_documentos_fiscais',
    ativo = 1,
    visivel_menu = 1,
    atualizado_em = CURRENT_TIMESTAMP
WHERE codigo = 'documentos_fiscais';

-- Reaproveita as permissões de visualização do menu legado de NFs de motoristas.
INSERT INTO perfil_permissoes (
    perfil_de_acesso, menu_codigo, acao_codigo, empresa_id, permitido
)
SELECT
    pp.perfil_de_acesso,
    'documentos_fiscais',
    pp.acao_codigo,
    pp.empresa_id,
    pp.permitido
FROM perfil_permissoes pp
WHERE pp.menu_codigo = 'financeiro_nfs_motoristas'
  AND NOT EXISTS (
      SELECT 1
      FROM perfil_permissoes atual
      WHERE atual.perfil_de_acesso = pp.perfil_de_acesso
        AND atual.menu_codigo = 'documentos_fiscais'
        AND atual.acao_codigo = pp.acao_codigo
        AND atual.empresa_id = pp.empresa_id
  );
