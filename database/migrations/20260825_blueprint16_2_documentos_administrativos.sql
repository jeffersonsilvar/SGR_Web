-- Blueprint 16.2 — Documentos Fiscais Administrativos
-- Compatível com MySQL 5.6.
-- Não altera motorista_notas_fiscais nem motorista_nf_rotas.

CREATE TABLE IF NOT EXISTS documentos_fiscais (
    id BIGINT(20) NOT NULL AUTO_INCREMENT,
    empresa_id INT(11) NOT NULL,
    pessoa_id INT(11) DEFAULT NULL,
    tipo_documento VARCHAR(40) NOT NULL,
    origem_documento VARCHAR(40) NOT NULL DEFAULT 'INTERNO',
    numero_documento VARCHAR(60) NOT NULL,
    serie VARCHAR(30) DEFAULT NULL,
    chave_acesso VARCHAR(120) DEFAULT NULL,
    data_emissao DATE NOT NULL,
    data_competencia DATE DEFAULT NULL,
    valor_total DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    nome_emitente VARCHAR(180) DEFAULT NULL,
    cpf_cnpj_emitente VARCHAR(20) DEFAULT NULL,
    cpf_cnpj_destinatario VARCHAR(20) DEFAULT NULL,
    descricao VARCHAR(255) DEFAULT NULL,
    arquivo_xml VARCHAR(500) DEFAULT NULL,
    arquivo_pdf VARCHAR(500) DEFAULT NULL,
    status_documento VARCHAR(30) NOT NULL DEFAULT 'Recebido',
    titulo_financeiro_id INT(11) DEFAULT NULL,
    origem_legada_tipo VARCHAR(50) DEFAULT NULL,
    origem_legada_id BIGINT(20) DEFAULT NULL,
    observacao TEXT,
    usuario_criacao_id INT(11) DEFAULT NULL,
    usuario_atualizacao_id INT(11) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_documentos_fiscais_empresa_chave (empresa_id, chave_acesso),
    KEY idx_documentos_fiscais_empresa_status (empresa_id, status_documento),
    KEY idx_documentos_fiscais_empresa_tipo (empresa_id, tipo_documento),
    KEY idx_documentos_fiscais_pessoa (empresa_id, pessoa_id),
    KEY idx_documentos_fiscais_emissao (empresa_id, data_emissao),
    KEY idx_documentos_fiscais_titulo (empresa_id, titulo_financeiro_id),
    KEY idx_documentos_fiscais_origem_legada (empresa_id, origem_legada_tipo, origem_legada_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- A Etapa 16.2 habilita o cadastro interno. Perfis que já visualizam a central
-- passam a poder criar documentos; edição/aprovação ficam para etapas posteriores.
INSERT INTO perfil_permissoes (
    perfil_de_acesso, menu_codigo, acao_codigo, empresa_id, permitido
)
SELECT
    pp.perfil_de_acesso,
    'documentos_fiscais',
    'criar',
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
        AND atual.acao_codigo = 'criar'
        AND atual.empresa_id = pp.empresa_id
  );
