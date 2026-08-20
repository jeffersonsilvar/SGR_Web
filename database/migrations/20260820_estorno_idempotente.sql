-- Proteção definitiva contra estorno duplicado da mesma movimentação de caixa.
-- Compatível com MySQL 5.6.
--
-- Pré-condição: não pode existir mais de um registro com o mesmo
-- estorno_de_movimentacao_id não nulo. Antes de aplicar, rode:
--
-- SELECT estorno_de_movimentacao_id, COUNT(*) AS quantidade,
--        GROUP_CONCAT(id ORDER BY id) AS ids_estornos
-- FROM movimentacoes_caixa
-- WHERE estorno_de_movimentacao_id IS NOT NULL
-- GROUP BY estorno_de_movimentacao_id
-- HAVING COUNT(*) > 1;
--
-- A consulta acima deve retornar 0 linhas.

SET @schema_atual := DATABASE();

-- Remove o índice não-único legado apenas se ele ainda existir.
SELECT COUNT(*) INTO @idx_legado_existe
FROM information_schema.statistics
WHERE table_schema = @schema_atual
  AND table_name = 'movimentacoes_caixa'
  AND index_name = 'idx_mov_caixa_estorno_de';

SET @sql_drop_legado := IF(
    @idx_legado_existe > 0,
    'ALTER TABLE movimentacoes_caixa DROP INDEX idx_mov_caixa_estorno_de',
    'SELECT 1'
);
PREPARE stmt_drop_legado FROM @sql_drop_legado;
EXECUTE stmt_drop_legado;
DEALLOCATE PREPARE stmt_drop_legado;

-- Cria o índice UNIQUE somente se ainda não existir.
SELECT COUNT(*) INTO @idx_unico_existe
FROM information_schema.statistics
WHERE table_schema = @schema_atual
  AND table_name = 'movimentacoes_caixa'
  AND index_name = 'uq_movimentacoes_caixa_estorno_origem'
  AND non_unique = 0;

SET @sql_add_unico := IF(
    @idx_unico_existe = 0,
    'ALTER TABLE movimentacoes_caixa ADD UNIQUE KEY uq_movimentacoes_caixa_estorno_origem (estorno_de_movimentacao_id)',
    'SELECT 1'
);
PREPARE stmt_add_unico FROM @sql_add_unico;
EXECUTE stmt_add_unico;
DEALLOCATE PREPARE stmt_add_unico;

-- Verificação final esperada: Non_unique = 0.
SHOW INDEX
FROM movimentacoes_caixa
WHERE Key_name = 'uq_movimentacoes_caixa_estorno_origem';
