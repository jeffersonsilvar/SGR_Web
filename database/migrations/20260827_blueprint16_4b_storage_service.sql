-- Blueprint 16.4B — StorageService, integridade e health check
-- MySQL 5.6 compatível: evita IF NOT EXISTS em ADD COLUMN.

SET @db := DATABASE();

SET @sql := (
    SELECT IF(
        EXISTS(
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = @db
              AND TABLE_NAME = 'arquivos_sistema'
              AND COLUMN_NAME = 'sha256_hex'
        ),
        'SELECT 1',
        'ALTER TABLE arquivos_sistema ADD COLUMN sha256_hex CHAR(64) NULL AFTER tamanho_bytes'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
    SELECT IF(
        EXISTS(
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = @db
              AND TABLE_NAME = 'arquivos_sistema'
              AND COLUMN_NAME = 'versao'
        ),
        'SELECT 1',
        'ALTER TABLE arquivos_sistema ADD COLUMN versao INT NOT NULL DEFAULT 1 AFTER sha256_hex'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
    SELECT IF(
        EXISTS(
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = @db
              AND TABLE_NAME = 'arquivos_sistema'
              AND COLUMN_NAME = 'arquivo_anterior_id'
        ),
        'SELECT 1',
        'ALTER TABLE arquivos_sistema ADD COLUMN arquivo_anterior_id BIGINT NULL AFTER versao'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
    SELECT IF(
        EXISTS(
            SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = @db
              AND TABLE_NAME = 'arquivos_sistema'
              AND INDEX_NAME = 'idx_arquivos_sistema_sha256'
        ),
        'SELECT 1',
        'ALTER TABLE arquivos_sistema ADD INDEX idx_arquivos_sistema_sha256 (empresa_id, sha256_hex)'
    )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS storage_health_status (
    id INT NOT NULL AUTO_INCREMENT,
    provider VARCHAR(50) NOT NULL,
    status_integracao VARCHAR(30) NOT NULL,
    mensagem VARCHAR(500) DEFAULT NULL,
    latencia_ms INT DEFAULT NULL,
    verificado_em DATETIME NOT NULL,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_storage_health_provider (provider)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
