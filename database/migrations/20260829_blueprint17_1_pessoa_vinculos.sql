-- Blueprint 17.1 — Pessoas, Prestadores e Vínculos
-- Compatível com MySQL 5.6.
-- Migração aditiva e não destrutiva: preserva pessoas, usuarios e colunas legadas
-- como motorista_id/ajudante_id. O objetivo é introduzir papéis múltiplos por Pessoa.

CREATE TABLE IF NOT EXISTS pessoa_vinculos (
    id BIGINT(20) NOT NULL AUTO_INCREMENT,
    empresa_id INT(11) NOT NULL,
    pessoa_id INT(11) NOT NULL,
    tipo_vinculo VARCHAR(60) NOT NULL,
    status_vinculo VARCHAR(30) NOT NULL DEFAULT 'Ativo',
    origem_vinculo VARCHAR(40) NOT NULL DEFAULT 'MIGRACAO_LEGADO',
    observacao VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_pessoa_vinculos_empresa_pessoa_tipo (empresa_id, pessoa_id, tipo_vinculo),
    KEY idx_pessoa_vinculos_empresa_tipo (empresa_id, tipo_vinculo, status_vinculo),
    KEY idx_pessoa_vinculos_pessoa (empresa_id, pessoa_id, status_vinculo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Fornecedor é papel da Pessoa, não conta de acesso.
INSERT INTO pessoa_vinculos (
    empresa_id, pessoa_id, tipo_vinculo, status_vinculo, origem_vinculo, observacao
)
SELECT
    p.empresa_id,
    p.id,
    'FORNECEDOR',
    'Ativo',
    'MIGRACAO_LEGADO',
    'Originado de pessoas.tipo_cadastro = Fornecedor'
FROM pessoas p
WHERE p.empresa_id IS NOT NULL
  AND TRIM(COALESCE(p.tipo_cadastro, '')) = 'Fornecedor'
  AND NOT EXISTS (
      SELECT 1
      FROM pessoa_vinculos pv
      WHERE pv.empresa_id = p.empresa_id
        AND pv.pessoa_id = p.id
        AND pv.tipo_vinculo = 'FORNECEDOR'
  );

-- Prestador de Serviço pode acumular outros papéis, por exemplo Motorista ou Ajudante.
INSERT INTO pessoa_vinculos (
    empresa_id, pessoa_id, tipo_vinculo, status_vinculo, origem_vinculo, observacao
)
SELECT
    p.empresa_id,
    p.id,
    'PRESTADOR_SERVICO',
    'Ativo',
    'MIGRACAO_LEGADO',
    'Originado de pessoas.tipo_cadastro = Prestador de Serviço'
FROM pessoas p
WHERE p.empresa_id IS NOT NULL
  AND TRIM(COALESCE(p.tipo_cadastro, '')) IN ('Prestador de Serviço', 'Prestador de Servico')
  AND NOT EXISTS (
      SELECT 1
      FROM pessoa_vinculos pv
      WHERE pv.empresa_id = p.empresa_id
        AND pv.pessoa_id = p.id
        AND pv.tipo_vinculo = 'PRESTADOR_SERVICO'
  );

INSERT INTO pessoa_vinculos (
    empresa_id, pessoa_id, tipo_vinculo, status_vinculo, origem_vinculo, observacao
)
SELECT
    p.empresa_id,
    p.id,
    'FUNCIONARIO',
    'Ativo',
    'MIGRACAO_LEGADO',
    'Originado de pessoas.tipo_cadastro = Funcionario'
FROM pessoas p
WHERE p.empresa_id IS NOT NULL
  AND TRIM(COALESCE(p.tipo_cadastro, '')) IN ('Funcionario', 'Funcionário')
  AND NOT EXISTS (
      SELECT 1
      FROM pessoa_vinculos pv
      WHERE pv.empresa_id = p.empresa_id
        AND pv.pessoa_id = p.id
        AND pv.tipo_vinculo = 'FUNCIONARIO'
  );

-- tipo_prestador descreve função operacional e gera vínculo independente.
INSERT INTO pessoa_vinculos (
    empresa_id, pessoa_id, tipo_vinculo, status_vinculo, origem_vinculo, observacao
)
SELECT
    p.empresa_id,
    p.id,
    'MOTORISTA',
    'Ativo',
    'MIGRACAO_LEGADO',
    'Originado de pessoas.tipo_prestador = Motorista'
FROM pessoas p
WHERE p.empresa_id IS NOT NULL
  AND TRIM(COALESCE(p.tipo_prestador, '')) = 'Motorista'
  AND NOT EXISTS (
      SELECT 1
      FROM pessoa_vinculos pv
      WHERE pv.empresa_id = p.empresa_id
        AND pv.pessoa_id = p.id
        AND pv.tipo_vinculo = 'MOTORISTA'
  );

INSERT INTO pessoa_vinculos (
    empresa_id, pessoa_id, tipo_vinculo, status_vinculo, origem_vinculo, observacao
)
SELECT
    p.empresa_id,
    p.id,
    'AJUDANTE',
    'Ativo',
    'MIGRACAO_LEGADO',
    'Originado de pessoas.tipo_prestador = Ajudante'
FROM pessoas p
WHERE p.empresa_id IS NOT NULL
  AND TRIM(COALESCE(p.tipo_prestador, '')) = 'Ajudante'
  AND NOT EXISTS (
      SELECT 1
      FROM pessoa_vinculos pv
      WHERE pv.empresa_id = p.empresa_id
        AND pv.pessoa_id = p.id
        AND pv.tipo_vinculo = 'AJUDANTE'
  );

-- Deliberadamente não converte tipo_cadastro = 'Outros': não há semântica suficiente
-- para inferir um papel operacional seguro.
-- permite_acesso_portal também não é vínculo; acesso/login permanece domínio de usuarios.
