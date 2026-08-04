-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host removido por segurança
-- Tempo de geração: 04/08/2026 às 16:55
-- Versão do servidor: 5.6.26-log
-- Versão do PHP: 8.0.15

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: configure MYSQL_DATABASE no arquivo .env
--

-- --------------------------------------------------------

--
-- Estrutura para tabela `arquivos_sistema`
--

CREATE TABLE `arquivos_sistema` (
  `id` bigint(20) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `pessoa_id` int(11) DEFAULT NULL,
  `motorista_id` int(11) DEFAULT NULL,
  `origem` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `origem_id` bigint(20) DEFAULT NULL,
  `tipo_arquivo` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nome_original` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nome_armazenado` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `mime_type` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tamanho_bytes` bigint(20) DEFAULT '0',
  `storage_provider` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'GOOGLE_DRIVE',
  `caminho_local` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `drive_file_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `drive_folder_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `drive_view_url` text COLLATE utf8mb4_unicode_ci,
  `drive_download_url` text COLLATE utf8mb4_unicode_ci,
  `status_arquivo` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ATIVO',
  `erro_upload` text COLLATE utf8mb4_unicode_ci,
  `criado_por_usuario_id` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `auditoria_checkin_base`
--

CREATE TABLE `auditoria_checkin_base` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `motorista_id` int(11) DEFAULT NULL,
  `escala_id` int(11) DEFAULT NULL,
  `base_operacional_id` int(11) DEFAULT NULL,
  `data_tentativa` datetime NOT NULL,
  `latitude` decimal(12,8) DEFAULT NULL,
  `longitude` decimal(13,8) DEFAULT NULL,
  `distancia_base_metros` decimal(10,2) DEFAULT NULL,
  `codigo_qr_informado` varchar(120) DEFAULT NULL,
  `qr_token_id` int(11) DEFAULT NULL,
  `resultado` varchar(80) NOT NULL,
  `motivo_bloqueio` varchar(255) DEFAULT NULL,
  `selfie_path` varchar(255) DEFAULT NULL,
  `ip_origem` varchar(80) DEFAULT NULL,
  `user_agent` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `auditoria_financeira`
--

CREATE TABLE `auditoria_financeira` (
  `id` bigint(20) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `modulo` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'FINANCEIRO',
  `acao` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `entidade_tipo` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `entidade_id` bigint(20) DEFAULT NULL,
  `titulo_financeiro_id` int(11) DEFAULT NULL,
  `movimentacao_caixa_id` int(11) DEFAULT NULL,
  `pessoa_id` int(11) DEFAULT NULL,
  `status_anterior` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status_novo` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `valor_anterior` decimal(15,2) DEFAULT NULL,
  `valor_novo` decimal(15,2) DEFAULT NULL,
  `motivo` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `observacao` text COLLATE utf8mb4_unicode_ci,
  `dados_antes` text COLLATE utf8mb4_unicode_ci,
  `dados_depois` text COLLATE utf8mb4_unicode_ci,
  `ip_origem` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_agent` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `auditoria_permissoes`
--

CREATE TABLE `auditoria_permissoes` (
  `id` int(11) NOT NULL,
  `usuario_executor_id` int(11) DEFAULT NULL,
  `usuario_afetado_id` int(11) DEFAULT NULL,
  `perfil_afetado_id` int(11) DEFAULT NULL,
  `tipo_acao` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'CORRECAO',
  `entidade` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `entidade_id` int(11) DEFAULT NULL,
  `antes_json` text COLLATE utf8mb4_unicode_ci,
  `depois_json` text COLLATE utf8mb4_unicode_ci,
  `ip_origem` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_agent` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `perfil_afetado` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `acao` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `detalhe` text COLLATE utf8mb4_unicode_ci,
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `auditoria_supervisor`
--

CREATE TABLE `auditoria_supervisor` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `data_acao` datetime NOT NULL,
  `tipo_acao` varchar(50) NOT NULL,
  `descricao` text NOT NULL,
  `ip_origem` varchar(45) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estrutura para tabela `bases_operacionais`
--

CREATE TABLE `bases_operacionais` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `nome_base` varchar(120) NOT NULL,
  `descricao` varchar(255) DEFAULT NULL,
  `endereco` varchar(255) DEFAULT NULL,
  `latitude` decimal(12,8) DEFAULT NULL,
  `longitude` decimal(13,8) DEFAULT NULL,
  `raio_permitido_metros` int(11) NOT NULL DEFAULT '150',
  `codigo_qr_base` varchar(120) DEFAULT NULL,
  `qr_validade_minutos` int(11) NOT NULL DEFAULT '5',
  `status_base` varchar(20) NOT NULL DEFAULT 'Ativa',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `base_qr_tokens`
--

CREATE TABLE `base_qr_tokens` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `base_operacional_id` int(11) NOT NULL,
  `codigo_token` varchar(120) NOT NULL,
  `data_geracao` datetime NOT NULL,
  `data_expiracao` datetime NOT NULL,
  `status_token` varchar(20) NOT NULL DEFAULT 'Ativo',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `ciencia_escala_motorista`
--

CREATE TABLE `ciencia_escala_motorista` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `motorista_id` int(11) NOT NULL,
  `escala_id` int(11) NOT NULL,
  `data_ciencia` datetime NOT NULL,
  `origem_ciencia` varchar(30) NOT NULL DEFAULT 'Motorista',
  `usuario_id` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `configuracoes_disponibilidade`
--

CREATE TABLE `configuracoes_disponibilidade` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `horario_limite_edicao` time NOT NULL DEFAULT '11:00:00',
  `limite_dias_disponiveis_semana` int(11) NOT NULL DEFAULT '6',
  `permite_liberacao_setimo_dia` char(1) NOT NULL DEFAULT 'S',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `configuracoes_escala_motorista`
--

CREATE TABLE `configuracoes_escala_motorista` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `horario_limite_presenca` time NOT NULL DEFAULT '11:01:00',
  `aplicar_falta_automatica` char(1) NOT NULL DEFAULT 'S',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `contas_caixa`
--

CREATE TABLE `contas_caixa` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `nome_conta` varchar(150) NOT NULL,
  `tipo_conta` varchar(50) NOT NULL,
  `banco` varchar(120) DEFAULT NULL,
  `agencia` varchar(30) DEFAULT NULL,
  `numero_conta` varchar(50) DEFAULT NULL,
  `saldo_inicial` decimal(15,2) NOT NULL DEFAULT '0.00',
  `status_conta` varchar(20) NOT NULL DEFAULT 'Ativa',
  `observacao` text,
  `usuario_criacao_id` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estrutura para tabela `disponibilidade_motorista`
--

CREATE TABLE `disponibilidade_motorista` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `motorista_id` int(11) NOT NULL,
  `data_disponibilidade` date NOT NULL,
  `dia_semana` varchar(30) DEFAULT NULL,
  `status_disponibilidade` varchar(30) NOT NULL DEFAULT 'Sem resposta',
  `observacao` varchar(255) DEFAULT NULL,
  `origem_lancamento` varchar(30) NOT NULL DEFAULT 'Motorista',
  `usuario_lancamento_id` int(11) DEFAULT NULL,
  `bloqueado_por_horario` char(1) NOT NULL DEFAULT 'N',
  `liberado_excepcional` char(1) NOT NULL DEFAULT 'N',
  `usuario_liberacao_id` int(11) DEFAULT NULL,
  `motivo_liberacao` varchar(255) DEFAULT NULL,
  `data_liberacao` datetime DEFAULT NULL,
  `data_criacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_atualizacao` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `empresas`
--

CREATE TABLE `empresas` (
  `id` int(11) NOT NULL,
  `data_cadastro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `razao_social` varchar(150) NOT NULL,
  `nome_fantasia` varchar(150) DEFAULT NULL,
  `cnpj` varchar(20) DEFAULT NULL,
  `slug` varchar(80) DEFAULT NULL,
  `status_empresa` varchar(30) NOT NULL DEFAULT 'Ativa',
  `plano` varchar(50) DEFAULT 'Profissional',
  `limite_usuarios` int(11) DEFAULT NULL,
  `observacao` text
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `empresa_parametros`
--

CREATE TABLE `empresa_parametros` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `grupo` varchar(80) NOT NULL,
  `chave` varchar(160) NOT NULL,
  `valor` text,
  `tipo` varchar(30) NOT NULL DEFAULT 'string',
  `descricao` varchar(255) DEFAULT NULL,
  `grupo_financeiro` tinyint(1) NOT NULL DEFAULT '0',
  `usuario_atualizacao_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estrutura para tabela `escala_motorista`
--

CREATE TABLE `escala_motorista` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `motorista_id` int(11) NOT NULL,
  `data_escala` date NOT NULL,
  `status_escala` varchar(60) NOT NULL DEFAULT 'Pendente',
  `status_presenca` varchar(60) NOT NULL DEFAULT 'Não se aplica',
  `base_operacional_id` int(11) DEFAULT NULL,
  `base_operacao` varchar(120) DEFAULT NULL,
  `horario_apresentacao` time DEFAULT NULL,
  `observacao_supervisor` varchar(255) DEFAULT NULL,
  `usuario_supervisor_id` int(11) DEFAULT NULL,
  `presenca_confirmada_em` datetime DEFAULT NULL,
  `presenca_confirmada_por` varchar(30) DEFAULT NULL,
  `usuario_confirmacao_id` int(11) DEFAULT NULL,
  `falta_automatica` char(1) NOT NULL DEFAULT 'N',
  `falta_marcada_em` datetime DEFAULT NULL,
  `falta_motivo` varchar(255) DEFAULT NULL,
  `falta_revertida` char(1) NOT NULL DEFAULT 'N',
  `usuario_reversao_id` int(11) DEFAULT NULL,
  `motivo_reversao` varchar(255) DEFAULT NULL,
  `data_reversao` datetime DEFAULT NULL,
  `data_criacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_atualizacao` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `fila_cancelados_base`
--

CREATE TABLE `fila_cancelados_base` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `escala_id` int(11) NOT NULL,
  `motorista_id` int(11) NOT NULL,
  `base_operacional_id` int(11) DEFAULT NULL,
  `base_operacao` varchar(120) DEFAULT NULL,
  `data_fila` date NOT NULL,
  `hora_confirmacao` datetime NOT NULL,
  `posicao_fila` int(11) NOT NULL,
  `status_fila` varchar(60) NOT NULL DEFAULT 'Aguardando rota',
  `confirmado_por` varchar(30) NOT NULL DEFAULT 'Motorista',
  `usuario_confirmacao_id` int(11) DEFAULT NULL,
  `latitude_confirmacao` decimal(12,8) DEFAULT NULL,
  `longitude_confirmacao` decimal(13,8) DEFAULT NULL,
  `distancia_base_metros` decimal(10,2) DEFAULT NULL,
  `geolocalizacao_validada` char(1) NOT NULL DEFAULT 'N',
  `qr_code_validado` char(1) NOT NULL DEFAULT 'N',
  `qr_token_id` int(11) DEFAULT NULL,
  `selfie_path` varchar(255) DEFAULT NULL,
  `usuario_acao_id` int(11) DEFAULT NULL,
  `observacao` varchar(255) DEFAULT NULL,
  `data_criacao` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_atualizacao` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `google_drive_pastas_sgr`
--

CREATE TABLE `google_drive_pastas_sgr` (
  `id` bigint(20) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `folder_key` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `folder_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `folder_id` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `parent_folder_id` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `categoria` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ano` int(11) DEFAULT NULL,
  `mes` int(11) DEFAULT NULL,
  `motorista_id` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `historico_ajudante_pagamentos`
--

CREATE TABLE `historico_ajudante_pagamentos` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `data_operacao` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `tipo_operacao` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `lancamento_ajudante_id` int(11) DEFAULT NULL,
  `ajudante_id` int(11) DEFAULT NULL,
  `rota_id` int(11) DEFAULT NULL,
  `identi_rota` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `status_anterior` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status_novo` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `valor_operacao` decimal(10,2) NOT NULL DEFAULT '0.00',
  `motivo` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `observacao` text COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `historico_operacoes`
--

CREATE TABLE `historico_operacoes` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `data_operacao` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `tipo_operacao` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rota_id` int(11) DEFAULT NULL,
  `nota_fiscal_id` int(11) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `status_anterior` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status_novo` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `motivo` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `observacao` text COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `justificativas_ausencia_motorista`
--

CREATE TABLE `justificativas_ausencia_motorista` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `escala_id` int(11) NOT NULL,
  `motorista_id` int(11) NOT NULL,
  `base_operacional_id` int(11) DEFAULT NULL,
  `data_escala` date NOT NULL,
  `horario_previsto` time DEFAULT NULL,
  `motivo` varchar(120) NOT NULL,
  `observacao_motorista` text NOT NULL,
  `anexo_path` varchar(255) DEFAULT NULL,
  `status_justificativa` varchar(40) NOT NULL DEFAULT 'Pendente de análise',
  `observacao_supervisor` text,
  `usuario_analise_id` int(11) DEFAULT NULL,
  `data_envio` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_analise` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estrutura para tabela `lancamentos_ajudantes`
--

CREATE TABLE `lancamentos_ajudantes` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `data_lancamento` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ajudante_id` int(11) NOT NULL,
  `valor_total` decimal(10,2) NOT NULL DEFAULT '0.00',
  `status_pagamento` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Pendente',
  `data_pagamento` timestamp NULL DEFAULT NULL,
  `usuario_pagamento_id` int(11) DEFAULT NULL,
  `data_estorno_pagamento` timestamp NULL DEFAULT NULL,
  `motivo_estorno_pagamento` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `data_estorno_lancamento` timestamp NULL DEFAULT NULL,
  `motivo_estorno_lancamento` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `usuario_estorno_id` int(11) DEFAULT NULL,
  `observacao` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `lancamento_ajudante_rotas`
--

CREATE TABLE `lancamento_ajudante_rotas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `lancamento_ajudante_id` int(11) NOT NULL,
  `rota_id` int(11) NOT NULL,
  `identi_rota` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor_ajudante` decimal(10,2) NOT NULL DEFAULT '0.00',
  `data_vinculo` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `motorista_nf_rotas`
--

CREATE TABLE `motorista_nf_rotas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `motorista_nf_id` int(11) NOT NULL,
  `rota_id` int(11) NOT NULL,
  `valor_rota` decimal(10,2) NOT NULL DEFAULT '0.00',
  `data_vinculo` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `motorista_notas_fiscais`
--

CREATE TABLE `motorista_notas_fiscais` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `motorista_id` int(11) NOT NULL,
  `tipo_documento_pagamento` varchar(30) NOT NULL DEFAULT 'XML',
  `numero_nf` varchar(50) NOT NULL,
  `chave_acesso` varchar(120) NOT NULL,
  `data_emissao` date DEFAULT NULL,
  `valor_total` decimal(10,2) NOT NULL DEFAULT '0.00',
  `valor_bruto` decimal(12,2) DEFAULT NULL,
  `valor_liquido` decimal(12,2) DEFAULT NULL,
  `prestador_cpf_cnpj` varchar(20) DEFAULT NULL,
  `tomador_cpf_cnpj` varchar(20) DEFAULT NULL,
  `status_nf` varchar(40) NOT NULL DEFAULT 'Enviada',
  `nome_arquivo_xml` varchar(255) DEFAULT NULL,
  `data_envio` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_aprovacao` datetime DEFAULT NULL,
  `usuario_aprovacao_id` int(11) DEFAULT NULL,
  `data_pagamento` datetime DEFAULT NULL,
  `data_estorno_pagamento` datetime DEFAULT NULL,
  `motivo_estorno_pagamento` varchar(255) DEFAULT NULL,
  `usuario_estorno_pagamento_id` int(11) DEFAULT NULL,
  `usuario_pagamento_id` int(11) DEFAULT NULL,
  `data_recusa` datetime DEFAULT NULL,
  `motivo_recusa` varchar(255) DEFAULT NULL,
  `usuario_recusa_id` int(11) DEFAULT NULL,
  `observacao` text
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Estrutura para tabela `movimentacoes_caixa`
--

CREATE TABLE `movimentacoes_caixa` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `conta_caixa_id` int(11) NOT NULL,
  `titulo_financeiro_id` int(11) DEFAULT NULL,
  `tipo_movimentacao` varchar(20) NOT NULL,
  `data_movimentacao` date NOT NULL,
  `valor_movimentacao` decimal(15,2) NOT NULL DEFAULT '0.00',
  `forma_pagamento` varchar(60) DEFAULT NULL,
  `historico` text,
  `observacao` text,
  `comprovante_arquivo_id` int(11) DEFAULT NULL,
  `usuario_criacao_id` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `comprovante_url` varchar(255) DEFAULT NULL,
  `status_movimentacao` varchar(30) NOT NULL DEFAULT 'Ativa',
  `status_conciliacao` varchar(30) DEFAULT 'Pendente',
  `data_conciliacao` datetime DEFAULT NULL,
  `usuario_conciliacao_id` int(11) DEFAULT NULL,
  `observacao_conciliacao` text,
  `estorno_de_movimentacao_id` int(11) DEFAULT NULL,
  `motivo_estorno` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estrutura para tabela `notas_fiscais`
--

CREATE TABLE `notas_fiscais` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `data_importacao` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `numero_nf` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `chave_acesso` varchar(44) COLLATE utf8mb4_unicode_ci NOT NULL,
  `data_emissao` date NOT NULL,
  `valor_total` decimal(10,2) NOT NULL DEFAULT '0.00',
  `status_nf` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Faturada',
  `data_estorno` timestamp NULL DEFAULT NULL,
  `motivo_estorno` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `usuario_estorno_id` int(11) DEFAULT NULL,
  `emitente_id` int(11) NOT NULL,
  `tomador_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `nota_fiscal_rotas`
--

CREATE TABLE `nota_fiscal_rotas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `nota_fiscal_id` int(11) NOT NULL,
  `rota_id` int(11) NOT NULL,
  `valor_rota_faturado` decimal(10,2) NOT NULL DEFAULT '0.00',
  `data_vinculo` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `perfil_permissoes`
--

CREATE TABLE `perfil_permissoes` (
  `id` int(11) NOT NULL,
  `perfil_de_acesso` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `menu_codigo` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `acao_codigo` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'visualizar',
  `empresa_id` int(11) NOT NULL DEFAULT '0',
  `permitido` tinyint(1) DEFAULT '1',
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `perfis_acesso`
--

CREATE TABLE `perfis_acesso` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `codigo` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nome` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descricao` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `perfil_sistema` tinyint(1) NOT NULL DEFAULT '0',
  `ativo` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `pessoas`
--

CREATE TABLE `pessoas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `data_cadastro` date NOT NULL,
  `nome_completo` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `apelido` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cpf_cnpj` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `telefone` varchar(35) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tipo_cadastro` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo_prestador` varchar(60) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `permite_acesso_portal` char(1) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'N',
  `status_cadastro` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Ativo',
  `cep` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rua` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `numero` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bairro` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cidade` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `uf` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `observacao` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `rotas`
--

CREATE TABLE `rotas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `data_lancamento` date NOT NULL,
  `identi_rota` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor_rota` decimal(10,2) NOT NULL DEFAULT '0.00',
  `valor_km` decimal(10,2) NOT NULL DEFAULT '0.00',
  `outras_despesas` decimal(10,2) NOT NULL DEFAULT '0.00',
  `tipo_rota` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `transportadora_id` int(11) DEFAULT NULL,
  `motorista_id` int(11) DEFAULT NULL,
  `situacao_rota` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Pendente',
  `status_motorista` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Pendente Aprovação',
  `data_aprovacao_motorista` datetime DEFAULT NULL,
  `usuario_aprovacao_motorista_id` int(11) DEFAULT NULL,
  `data_inclusao` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `rotas_divergencias_motorista`
--

CREATE TABLE `rotas_divergencias_motorista` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `rota_id` int(11) NOT NULL,
  `motorista_id` int(11) NOT NULL,
  `usuario_motorista_id` int(11) DEFAULT NULL,
  `tipo_divergencia` varchar(120) NOT NULL,
  `descricao` text NOT NULL,
  `status_divergencia` varchar(40) NOT NULL DEFAULT 'Aberta',
  `resultado_operacao` varchar(120) DEFAULT NULL,
  `observacao_operacao` text,
  `usuario_operacao_id` int(11) DEFAULT NULL,
  `resolvido_em` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estrutura para tabela `sistema_acoes`
--

CREATE TABLE `sistema_acoes` (
  `id` int(11) NOT NULL,
  `codigo` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nome` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ativo` tinyint(1) DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `sistema_menus`
--

CREATE TABLE `sistema_menus` (
  `id` int(11) NOT NULL,
  `modulo_id` int(11) DEFAULT NULL,
  `menu_pai_id` int(11) DEFAULT NULL,
  `grupo_menu` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `codigo` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `titulo` varchar(160) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descricao` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `endpoint` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rota_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `icone` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ordem` int(11) DEFAULT '0',
  `ativo` tinyint(1) DEFAULT '1',
  `visivel_menu` tinyint(1) DEFAULT '1',
  `exige_empresa` tinyint(1) NOT NULL DEFAULT '1',
  `somente_super_admin` tinyint(1) NOT NULL DEFAULT '0',
  `somente_suporte` tinyint(1) NOT NULL DEFAULT '0',
  `liberar_admin_empresas` tinyint(1) NOT NULL DEFAULT '0',
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `sistema_modulos`
--

CREATE TABLE `sistema_modulos` (
  `id` int(11) NOT NULL,
  `codigo` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nome` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descricao` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `icone` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ordem` int(11) DEFAULT '0',
  `ativo` tinyint(1) DEFAULT '1',
  `visivel_menu` tinyint(1) NOT NULL DEFAULT '1',
  `somente_super_admin` tinyint(1) NOT NULL DEFAULT '0',
  `somente_suporte` tinyint(1) NOT NULL DEFAULT '0',
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `titulos_financeiros`
--

CREATE TABLE `titulos_financeiros` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `tipo_titulo` varchar(20) NOT NULL,
  `origem` varchar(40) NOT NULL DEFAULT 'MANUAL',
  `origem_id` int(11) DEFAULT NULL,
  `pessoa_id` int(11) NOT NULL,
  `numero_documento` varchar(80) NOT NULL,
  `descricao` varchar(255) NOT NULL,
  `historico` text,
  `valor_original` decimal(15,2) NOT NULL DEFAULT '0.00',
  `valor_desconto` decimal(15,2) NOT NULL DEFAULT '0.00',
  `valor_acrescimo` decimal(15,2) NOT NULL DEFAULT '0.00',
  `valor_liquido` decimal(15,2) NOT NULL DEFAULT '0.00',
  `data_emissao` date NOT NULL,
  `data_competencia` date DEFAULT NULL,
  `data_vencimento` date NOT NULL,
  `forma_pagamento` varchar(60) DEFAULT NULL,
  `conta_caixa_prevista_id` int(11) DEFAULT NULL,
  `status_titulo` varchar(40) NOT NULL DEFAULT 'Aberto',
  `observacao` text,
  `usuario_criacao_id` int(11) DEFAULT NULL,
  `usuario_cancelamento_id` int(11) DEFAULT NULL,
  `data_cancelamento` datetime DEFAULT NULL,
  `motivo_cancelamento` text,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  `conta_caixa_baixa_id` int(11) DEFAULT NULL,
  `data_baixa` date DEFAULT NULL,
  `valor_baixado` decimal(15,2) DEFAULT NULL,
  `usuario_baixa_id` int(11) DEFAULT NULL,
  `observacao_baixa` text,
  `comprovante_url` varchar(255) DEFAULT NULL,
  `data_estorno` datetime DEFAULT NULL,
  `motivo_estorno` text,
  `usuario_estorno_id` int(11) DEFAULT NULL,
  `destino_estorno` varchar(30) DEFAULT NULL,
  `tratativa_pos_estorno_aplicada` tinyint(1) NOT NULL DEFAULT '0',
  `tipo_tratativa_pos_estorno` varchar(80) DEFAULT NULL,
  `data_tratativa_pos_estorno` datetime DEFAULT NULL,
  `usuario_tratativa_pos_estorno_id` int(11) DEFAULT NULL,
  `motivo_tratativa_pos_estorno` text,
  `observacao_tratativa_pos_estorno` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estrutura para tabela `titulos_financeiros_vinculos`
--

CREATE TABLE `titulos_financeiros_vinculos` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `titulo_financeiro_id` int(11) NOT NULL,
  `tipo_vinculo` varchar(40) NOT NULL,
  `origem_tabela` varchar(80) DEFAULT NULL,
  `origem_id` int(11) DEFAULT NULL,
  `descricao` varchar(255) DEFAULT NULL,
  `valor_vinculo` decimal(15,2) NOT NULL DEFAULT '0.00',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estrutura para tabela `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `base_operacional_id` int(11) DEFAULT NULL,
  `is_super_admin` tinyint(1) NOT NULL DEFAULT '0',
  `data_cadastro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `pessoa_id` int(11) DEFAULT NULL,
  `login` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status_usuario` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Ativo',
  `senha_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `perfil_de_acesso` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Operacional',
  `perfil_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `usuario_empresas_acesso`
--

CREATE TABLE `usuario_empresas_acesso` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `empresa_padrao` tinyint(1) NOT NULL DEFAULT '0',
  `ativo` tinyint(1) DEFAULT '1',
  `criado_por_usuario_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estrutura para tabela `usuario_permissoes`
--

CREATE TABLE `usuario_permissoes` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `menu_codigo` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `acao_codigo` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'visualizar',
  `empresa_id` int(11) NOT NULL DEFAULT '0',
  `permitido` tinyint(1) DEFAULT '1',
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Índices para tabelas despejadas
--

--
-- Índices de tabela `arquivos_sistema`
--
ALTER TABLE `arquivos_sistema`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_arq_empresa_origem` (`empresa_id`,`origem`,`origem_id`),
  ADD KEY `idx_arq_motorista` (`motorista_id`),
  ADD KEY `idx_arq_drive_file` (`drive_file_id`(191)),
  ADD KEY `idx_arq_status` (`status_arquivo`),
  ADD KEY `idx_arq_created_at` (`created_at`);

--
-- Índices de tabela `auditoria_checkin_base`
--
ALTER TABLE `auditoria_checkin_base`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_audit_empresa_data` (`empresa_id`,`data_tentativa`),
  ADD KEY `idx_audit_motorista` (`empresa_id`,`motorista_id`),
  ADD KEY `idx_audit_base` (`empresa_id`,`base_operacional_id`),
  ADD KEY `idx_audit_resultado` (`resultado`),
  ADD KEY `idx_audit_escala` (`escala_id`),
  ADD KEY `idx_audit_qr_token` (`qr_token_id`);

--
-- Índices de tabela `auditoria_financeira`
--
ALTER TABLE `auditoria_financeira`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_auditoria_fin_empresa_data` (`empresa_id`,`created_at`),
  ADD KEY `idx_auditoria_fin_acao` (`acao`),
  ADD KEY `idx_auditoria_fin_modulo` (`modulo`),
  ADD KEY `idx_auditoria_fin_usuario` (`usuario_id`),
  ADD KEY `idx_auditoria_fin_titulo` (`titulo_financeiro_id`),
  ADD KEY `idx_auditoria_fin_mov` (`movimentacao_caixa_id`),
  ADD KEY `idx_auditoria_fin_pessoa` (`pessoa_id`),
  ADD KEY `idx_auditoria_fin_entidade` (`entidade_tipo`,`entidade_id`);

--
-- Índices de tabela `auditoria_permissoes`
--
ALTER TABLE `auditoria_permissoes`
  ADD PRIMARY KEY (`id`);

--
-- Índices de tabela `auditoria_supervisor`
--
ALTER TABLE `auditoria_supervisor`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_auditoria_sup_empresa` (`empresa_id`),
  ADD KEY `fk_auditoria_sup_usuario` (`usuario_id`);

--
-- Índices de tabela `bases_operacionais`
--
ALTER TABLE `bases_operacionais`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_bases_empresa` (`empresa_id`),
  ADD KEY `idx_bases_status` (`status_base`);

--
-- Índices de tabela `base_qr_tokens`
--
ALTER TABLE `base_qr_tokens`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_base_qr_empresa_base` (`empresa_id`,`base_operacional_id`),
  ADD KEY `idx_base_qr_codigo` (`codigo_token`),
  ADD KEY `idx_base_qr_status_exp` (`status_token`,`data_expiracao`);

--
-- Índices de tabela `ciencia_escala_motorista`
--
ALTER TABLE `ciencia_escala_motorista`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_ciencia_escala_motorista` (`empresa_id`,`motorista_id`,`escala_id`),
  ADD KEY `idx_ciencia_empresa_motorista` (`empresa_id`,`motorista_id`),
  ADD KEY `idx_ciencia_escala` (`escala_id`);

--
-- Índices de tabela `configuracoes_disponibilidade`
--
ALTER TABLE `configuracoes_disponibilidade`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_config_disp_empresa` (`empresa_id`),
  ADD KEY `idx_config_disp_empresa` (`empresa_id`);

--
-- Índices de tabela `configuracoes_escala_motorista`
--
ALTER TABLE `configuracoes_escala_motorista`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_config_escala_empresa` (`empresa_id`),
  ADD KEY `idx_config_escala_empresa` (`empresa_id`);

--
-- Índices de tabela `contas_caixa`
--
ALTER TABLE `contas_caixa`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_contas_caixa_empresa` (`empresa_id`),
  ADD KEY `idx_contas_caixa_status` (`status_conta`),
  ADD KEY `idx_contas_caixa_empresa_status` (`empresa_id`,`status_conta`);

--
-- Índices de tabela `disponibilidade_motorista`
--
ALTER TABLE `disponibilidade_motorista`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_disp_motorista_dia` (`empresa_id`,`motorista_id`,`data_disponibilidade`),
  ADD KEY `idx_disp_empresa_data` (`empresa_id`,`data_disponibilidade`),
  ADD KEY `idx_disp_motorista_data` (`motorista_id`,`data_disponibilidade`),
  ADD KEY `idx_disp_status` (`status_disponibilidade`);

--
-- Índices de tabela `empresas`
--
ALTER TABLE `empresas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_empresas_slug` (`slug`);

--
-- Índices de tabela `empresa_parametros`
--
ALTER TABLE `empresa_parametros`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_empresa_parametro_chave` (`empresa_id`,`chave`),
  ADD KEY `idx_empresa_parametros_empresa_grupo` (`empresa_id`,`grupo`),
  ADD KEY `idx_empresa_parametros_financeiro` (`empresa_id`,`grupo_financeiro`);

--
-- Índices de tabela `escala_motorista`
--
ALTER TABLE `escala_motorista`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_escala_motorista_dia` (`empresa_id`,`motorista_id`,`data_escala`),
  ADD KEY `idx_escala_empresa_data` (`empresa_id`,`data_escala`),
  ADD KEY `idx_escala_motorista_data` (`motorista_id`,`data_escala`),
  ADD KEY `idx_escala_status` (`status_escala`),
  ADD KEY `idx_escala_presenca` (`status_presenca`),
  ADD KEY `idx_escala_base_operacional` (`base_operacional_id`);

--
-- Índices de tabela `fila_cancelados_base`
--
ALTER TABLE `fila_cancelados_base`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_fila_escala_motorista` (`empresa_id`,`escala_id`,`motorista_id`),
  ADD KEY `idx_fila_empresa_data` (`empresa_id`,`data_fila`),
  ADD KEY `idx_fila_base_data` (`empresa_id`,`base_operacional_id`,`data_fila`),
  ADD KEY `idx_fila_status` (`status_fila`),
  ADD KEY `idx_fila_ordem` (`empresa_id`,`data_fila`,`base_operacional_id`,`posicao_fila`);

--
-- Índices de tabela `google_drive_pastas_sgr`
--
ALTER TABLE `google_drive_pastas_sgr`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_drive_folder_key` (`folder_key`),
  ADD KEY `idx_drive_pastas_empresa` (`empresa_id`),
  ADD KEY `idx_drive_pastas_folder_id` (`folder_id`);

--
-- Índices de tabela `historico_ajudante_pagamentos`
--
ALTER TABLE `historico_ajudante_pagamentos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_hap_tipo` (`tipo_operacao`),
  ADD KEY `idx_hap_lancamento` (`lancamento_ajudante_id`),
  ADD KEY `idx_hap_ajudante` (`ajudante_id`),
  ADD KEY `idx_hap_rota` (`rota_id`),
  ADD KEY `idx_hap_usuario` (`usuario_id`);

--
-- Índices de tabela `historico_operacoes`
--
ALTER TABLE `historico_operacoes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_hist_tipo` (`tipo_operacao`),
  ADD KEY `idx_hist_rota` (`rota_id`),
  ADD KEY `idx_hist_nota` (`nota_fiscal_id`),
  ADD KEY `idx_hist_usuario` (`usuario_id`);

--
-- Índices de tabela `justificativas_ausencia_motorista`
--
ALTER TABLE `justificativas_ausencia_motorista`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_justificativa_escala_motorista` (`empresa_id`,`escala_id`,`motorista_id`),
  ADD KEY `idx_justificativa_empresa_data_status` (`empresa_id`,`data_escala`,`status_justificativa`),
  ADD KEY `idx_justificativa_base` (`base_operacional_id`),
  ADD KEY `idx_justificativa_motorista` (`motorista_id`);

--
-- Índices de tabela `lancamentos_ajudantes`
--
ALTER TABLE `lancamentos_ajudantes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_lanc_ajudante` (`ajudante_id`),
  ADD KEY `idx_lanc_status` (`status_pagamento`),
  ADD KEY `idx_lanc_data` (`data_lancamento`);

--
-- Índices de tabela `lancamento_ajudante_rotas`
--
ALTER TABLE `lancamento_ajudante_rotas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_rota_um_ajudante` (`rota_id`),
  ADD KEY `idx_lar_lancamento` (`lancamento_ajudante_id`),
  ADD KEY `idx_lar_rota` (`rota_id`);

--
-- Índices de tabela `motorista_nf_rotas`
--
ALTER TABLE `motorista_nf_rotas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_motorista_nf_documento_rota` (`empresa_id`,`motorista_nf_id`,`rota_id`),
  ADD KEY `idx_mnfr_empresa` (`empresa_id`),
  ADD KEY `idx_mnfr_nf` (`motorista_nf_id`),
  ADD KEY `idx_mnfr_rota` (`rota_id`),
  ADD KEY `idx_motorista_nf_rotas_rota` (`rota_id`);

--
-- Índices de tabela `motorista_notas_fiscais`
--
ALTER TABLE `motorista_notas_fiscais`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_mnf_empresa` (`empresa_id`),
  ADD KEY `idx_mnf_motorista` (`motorista_id`),
  ADD KEY `idx_mnf_status` (`status_nf`),
  ADD KEY `idx_motorista_nf_chave_empresa` (`empresa_id`,`chave_acesso`);

--
-- Índices de tabela `movimentacoes_caixa`
--
ALTER TABLE `movimentacoes_caixa`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_mov_caixa_empresa` (`empresa_id`),
  ADD KEY `idx_mov_caixa_conta` (`conta_caixa_id`),
  ADD KEY `idx_mov_caixa_titulo` (`titulo_financeiro_id`),
  ADD KEY `idx_mov_caixa_data` (`data_movimentacao`),
  ADD KEY `idx_mov_caixa_estorno_de` (`estorno_de_movimentacao_id`),
  ADD KEY `idx_mov_caixa_conciliacao` (`empresa_id`,`conta_caixa_id`,`status_conciliacao`,`data_movimentacao`),
  ADD KEY `idx_mov_caixa_conciliacao_mov` (`empresa_id`,`status_movimentacao`,`status_conciliacao`,`data_movimentacao`);

--
-- Índices de tabela `notas_fiscais`
--
ALTER TABLE `notas_fiscais`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_notas_chave_acesso` (`chave_acesso`),
  ADD KEY `idx_notas_numero_nf` (`numero_nf`),
  ADD KEY `idx_notas_data_emissao` (`data_emissao`),
  ADD KEY `idx_notas_emitente` (`emitente_id`),
  ADD KEY `idx_notas_tomador` (`tomador_id`);

--
-- Índices de tabela `nota_fiscal_rotas`
--
ALTER TABLE `nota_fiscal_rotas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_nota_rota` (`nota_fiscal_id`,`rota_id`),
  ADD UNIQUE KEY `uk_rota_unica_faturamento` (`rota_id`),
  ADD KEY `idx_nfr_nota` (`nota_fiscal_id`),
  ADD KEY `idx_nfr_rota` (`rota_id`);

--
-- Índices de tabela `perfil_permissoes`
--
ALTER TABLE `perfil_permissoes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_perfil_menu_acao_empresa` (`perfil_de_acesso`,`menu_codigo`,`acao_codigo`,`empresa_id`),
  ADD KEY `idx_perfil_permissoes_menu` (`menu_codigo`),
  ADD KEY `idx_perfil_permissoes_empresa` (`empresa_id`);

--
-- Índices de tabela `perfis_acesso`
--
ALTER TABLE `perfis_acesso`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_perfis_acesso_codigo` (`codigo`),
  ADD UNIQUE KEY `uk_perfis_empresa_codigo` (`empresa_id`,`codigo`),
  ADD KEY `idx_perfis_acesso_ativo` (`ativo`),
  ADD KEY `idx_perfis_empresa` (`empresa_id`),
  ADD KEY `idx_perfis_ativo` (`ativo`);

--
-- Índices de tabela `pessoas`
--
ALTER TABLE `pessoas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_pessoas_cpf_cnpj` (`cpf_cnpj`),
  ADD KEY `idx_pessoas_nome` (`nome_completo`),
  ADD KEY `idx_pessoas_tipo` (`tipo_cadastro`),
  ADD KEY `idx_pessoas_status` (`status_cadastro`),
  ADD KEY `idx_pessoas_categoria_prestador` (`empresa_id`,`tipo_cadastro`,`tipo_prestador`,`status_cadastro`);

--
-- Índices de tabela `rotas`
--
ALTER TABLE `rotas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_rotas_data_lancamento` (`data_lancamento`),
  ADD KEY `idx_rotas_identi_rota` (`identi_rota`),
  ADD KEY `idx_rotas_tipo_rota` (`tipo_rota`),
  ADD KEY `idx_rotas_situacao` (`situacao_rota`),
  ADD KEY `idx_rotas_transportadora` (`transportadora_id`),
  ADD KEY `idx_rotas_motorista` (`motorista_id`);

--
-- Índices de tabela `rotas_divergencias_motorista`
--
ALTER TABLE `rotas_divergencias_motorista`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_div_rota` (`rota_id`),
  ADD KEY `idx_div_empresa_status` (`empresa_id`,`status_divergencia`),
  ADD KEY `idx_div_motorista` (`motorista_id`);

--
-- Índices de tabela `sistema_acoes`
--
ALTER TABLE `sistema_acoes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `codigo` (`codigo`);

--
-- Índices de tabela `sistema_menus`
--
ALTER TABLE `sistema_menus`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `codigo` (`codigo`),
  ADD KEY `idx_sistema_menus_pai` (`menu_pai_id`),
  ADD KEY `idx_sistema_menus_endpoint` (`endpoint`),
  ADD KEY `idx_sistema_menus_grupo` (`grupo_menu`);

--
-- Índices de tabela `sistema_modulos`
--
ALTER TABLE `sistema_modulos`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `codigo` (`codigo`);

--
-- Índices de tabela `titulos_financeiros`
--
ALTER TABLE `titulos_financeiros`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_titulos_empresa` (`empresa_id`),
  ADD KEY `idx_titulos_empresa_status` (`empresa_id`,`status_titulo`),
  ADD KEY `idx_titulos_empresa_tipo` (`empresa_id`,`tipo_titulo`),
  ADD KEY `idx_titulos_empresa_origem` (`empresa_id`,`origem`,`origem_id`),
  ADD KEY `idx_titulos_pessoa` (`pessoa_id`),
  ADD KEY `idx_titulos_vencimento` (`data_vencimento`),
  ADD KEY `idx_titulos_documento` (`numero_documento`),
  ADD KEY `idx_titulos_baixa_conta` (`conta_caixa_baixa_id`),
  ADD KEY `idx_titulos_data_baixa` (`data_baixa`);

--
-- Índices de tabela `titulos_financeiros_vinculos`
--
ALTER TABLE `titulos_financeiros_vinculos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_titulos_vinculos_empresa` (`empresa_id`),
  ADD KEY `idx_titulos_vinculos_titulo` (`titulo_financeiro_id`),
  ADD KEY `idx_titulos_vinculos_origem` (`origem_tabela`,`origem_id`);

--
-- Índices de tabela `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_usuarios_login` (`login`),
  ADD UNIQUE KEY `uk_usuarios_pessoa_id` (`pessoa_id`),
  ADD KEY `idx_usuarios_status` (`status_usuario`),
  ADD KEY `idx_usuarios_perfil` (`perfil_de_acesso`),
  ADD KEY `fk_usuarios_empresa` (`empresa_id`),
  ADD KEY `idx_usuarios_perfil_id` (`perfil_id`);

--
-- Índices de tabela `usuario_empresas_acesso`
--
ALTER TABLE `usuario_empresas_acesso`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_usuario_empresa_acesso` (`usuario_id`,`empresa_id`),
  ADD UNIQUE KEY `uk_usuario_empresa` (`usuario_id`,`empresa_id`),
  ADD KEY `idx_usuario_empresas_empresa` (`empresa_id`),
  ADD KEY `idx_usuario_empresas_usuario` (`usuario_id`);

--
-- Índices de tabela `usuario_permissoes`
--
ALTER TABLE `usuario_permissoes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_usuario_menu_acao_empresa` (`usuario_id`,`menu_codigo`,`acao_codigo`,`empresa_id`),
  ADD KEY `idx_usuario_permissoes_menu` (`menu_codigo`),
  ADD KEY `idx_usuario_permissoes_empresa` (`empresa_id`);

--
-- AUTO_INCREMENT para tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela `arquivos_sistema`
--
ALTER TABLE `arquivos_sistema`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de tabela `auditoria_checkin_base`
--
ALTER TABLE `auditoria_checkin_base`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de tabela `auditoria_financeira`
--
ALTER TABLE `auditoria_financeira`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=512;

--
-- AUTO_INCREMENT de tabela `auditoria_permissoes`
--
ALTER TABLE `auditoria_permissoes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de tabela `auditoria_supervisor`
--
ALTER TABLE `auditoria_supervisor`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT de tabela `bases_operacionais`
--
ALTER TABLE `bases_operacionais`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de tabela `base_qr_tokens`
--
ALTER TABLE `base_qr_tokens`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- AUTO_INCREMENT de tabela `ciencia_escala_motorista`
--
ALTER TABLE `ciencia_escala_motorista`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de tabela `configuracoes_disponibilidade`
--
ALTER TABLE `configuracoes_disponibilidade`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de tabela `configuracoes_escala_motorista`
--
ALTER TABLE `configuracoes_escala_motorista`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de tabela `contas_caixa`
--
ALTER TABLE `contas_caixa`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de tabela `disponibilidade_motorista`
--
ALTER TABLE `disponibilidade_motorista`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT de tabela `empresas`
--
ALTER TABLE `empresas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de tabela `empresa_parametros`
--
ALTER TABLE `empresa_parametros`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=923;

--
-- AUTO_INCREMENT de tabela `escala_motorista`
--
ALTER TABLE `escala_motorista`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=40;

--
-- AUTO_INCREMENT de tabela `fila_cancelados_base`
--
ALTER TABLE `fila_cancelados_base`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de tabela `google_drive_pastas_sgr`
--
ALTER TABLE `google_drive_pastas_sgr`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `historico_ajudante_pagamentos`
--
ALTER TABLE `historico_ajudante_pagamentos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `historico_operacoes`
--
ALTER TABLE `historico_operacoes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=378;

--
-- AUTO_INCREMENT de tabela `justificativas_ausencia_motorista`
--
ALTER TABLE `justificativas_ausencia_motorista`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de tabela `lancamentos_ajudantes`
--
ALTER TABLE `lancamentos_ajudantes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `lancamento_ajudante_rotas`
--
ALTER TABLE `lancamento_ajudante_rotas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `motorista_nf_rotas`
--
ALTER TABLE `motorista_nf_rotas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- AUTO_INCREMENT de tabela `motorista_notas_fiscais`
--
ALTER TABLE `motorista_notas_fiscais`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de tabela `movimentacoes_caixa`
--
ALTER TABLE `movimentacoes_caixa`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `notas_fiscais`
--
ALTER TABLE `notas_fiscais`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `nota_fiscal_rotas`
--
ALTER TABLE `nota_fiscal_rotas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `perfil_permissoes`
--
ALTER TABLE `perfil_permissoes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6275;

--
-- AUTO_INCREMENT de tabela `perfis_acesso`
--
ALTER TABLE `perfis_acesso`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=69;

--
-- AUTO_INCREMENT de tabela `pessoas`
--
ALTER TABLE `pessoas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de tabela `rotas`
--
ALTER TABLE `rotas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `rotas_divergencias_motorista`
--
ALTER TABLE `rotas_divergencias_motorista`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de tabela `sistema_acoes`
--
ALTER TABLE `sistema_acoes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=694;

--
-- AUTO_INCREMENT de tabela `sistema_menus`
--
ALTER TABLE `sistema_menus`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2793;

--
-- AUTO_INCREMENT de tabela `sistema_modulos`
--
ALTER TABLE `sistema_modulos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=442;

--
-- AUTO_INCREMENT de tabela `titulos_financeiros`
--
ALTER TABLE `titulos_financeiros`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `titulos_financeiros_vinculos`
--
ALTER TABLE `titulos_financeiros_vinculos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT de tabela `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de tabela `usuario_empresas_acesso`
--
ALTER TABLE `usuario_empresas_acesso`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=70;

--
-- AUTO_INCREMENT de tabela `usuario_permissoes`
--
ALTER TABLE `usuario_permissoes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restrições para tabelas despejadas
--

--
-- Restrições para tabelas `auditoria_supervisor`
--
ALTER TABLE `auditoria_supervisor`
  ADD CONSTRAINT `fk_auditoria_sup_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_auditoria_sup_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON UPDATE CASCADE;

--
-- Restrições para tabelas `historico_ajudante_pagamentos`
--
ALTER TABLE `historico_ajudante_pagamentos`
  ADD CONSTRAINT `fk_hap_ajudante` FOREIGN KEY (`ajudante_id`) REFERENCES `pessoas` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_hap_lancamento` FOREIGN KEY (`lancamento_ajudante_id`) REFERENCES `lancamentos_ajudantes` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_hap_rota` FOREIGN KEY (`rota_id`) REFERENCES `rotas` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_hap_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;

--
-- Restrições para tabelas `historico_operacoes`
--
ALTER TABLE `historico_operacoes`
  ADD CONSTRAINT `fk_hist_nota` FOREIGN KEY (`nota_fiscal_id`) REFERENCES `notas_fiscais` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_hist_rota` FOREIGN KEY (`rota_id`) REFERENCES `rotas` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_hist_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;

--
-- Restrições para tabelas `lancamentos_ajudantes`
--
ALTER TABLE `lancamentos_ajudantes`
  ADD CONSTRAINT `fk_lancamentos_ajudante` FOREIGN KEY (`ajudante_id`) REFERENCES `pessoas` (`id`) ON UPDATE CASCADE;

--
-- Restrições para tabelas `lancamento_ajudante_rotas`
--
ALTER TABLE `lancamento_ajudante_rotas`
  ADD CONSTRAINT `fk_lar_lancamento` FOREIGN KEY (`lancamento_ajudante_id`) REFERENCES `lancamentos_ajudantes` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_lar_rota` FOREIGN KEY (`rota_id`) REFERENCES `rotas` (`id`) ON UPDATE CASCADE;

--
-- Restrições para tabelas `notas_fiscais`
--
ALTER TABLE `notas_fiscais`
  ADD CONSTRAINT `fk_notas_emitente` FOREIGN KEY (`emitente_id`) REFERENCES `pessoas` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_notas_tomador` FOREIGN KEY (`tomador_id`) REFERENCES `pessoas` (`id`) ON UPDATE CASCADE;

--
-- Restrições para tabelas `nota_fiscal_rotas`
--
ALTER TABLE `nota_fiscal_rotas`
  ADD CONSTRAINT `fk_nfr_nota_fiscal` FOREIGN KEY (`nota_fiscal_id`) REFERENCES `notas_fiscais` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_nfr_rota` FOREIGN KEY (`rota_id`) REFERENCES `rotas` (`id`) ON UPDATE CASCADE;

--
-- Restrições para tabelas `rotas`
--
ALTER TABLE `rotas`
  ADD CONSTRAINT `fk_rotas_transportadora` FOREIGN KEY (`transportadora_id`) REFERENCES `pessoas` (`id`) ON UPDATE CASCADE;

--
-- Restrições para tabelas `rotas_divergencias_motorista`
--
ALTER TABLE `rotas_divergencias_motorista`
  ADD CONSTRAINT `fk_div_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `fk_div_motorista` FOREIGN KEY (`motorista_id`) REFERENCES `pessoas` (`id`),
  ADD CONSTRAINT `fk_div_rota` FOREIGN KEY (`rota_id`) REFERENCES `rotas` (`id`);

--
-- Restrições para tabelas `usuarios`
--
ALTER TABLE `usuarios`
  ADD CONSTRAINT `fk_usuarios_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_usuarios_pessoa` FOREIGN KEY (`pessoa_id`) REFERENCES `pessoas` (`id`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
