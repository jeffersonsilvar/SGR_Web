# Regras de Negócio

Este documento reúne as regras identificadas a partir da visão atual do SGR Web.

## Escala e disponibilidade

1. O motorista pode informar ou alterar sua disponibilidade dentro do prazo definido pela empresa.
2. Após o encerramento do prazo, alterações podem ser bloqueadas.
3. A empresa organiza a escala com base nas informações disponíveis.
4. Motoristas podem ficar como escalados ou cancelados.
5. Cancelados podem ser convocados a comparecer à base para oportunidades adicionais.

## Check-in

1. O check-in pode exigir presença dentro do raio da base.
2. A comprovação pode utilizar localização, selfie e QR Code.
3. O registro deve manter data, hora e vínculo com a base.
4. O check-in pode influenciar a fila de cancelados e o score.

## Rotas

1. Toda rota deve estar vinculada a uma empresa e a um motorista.
2. A rota deve possuir informações suficientes para conferência operacional e financeira.
3. O motorista deve conseguir consultar suas rotas.
4. Divergências devem ser tratadas antes da liberação financeira.
5. Rotas liberadas podem compor o valor da NFSe.

## Divergências

1. O motorista pode contestar valor, tipo ou ausência de rota.
2. A empresa deve analisar a divergência.
3. A resolução deve manter histórico.
4. A rota só deve seguir para faturamento após o tratamento adequado.

## NFSe e documentos

1. O envio de NFSe ocorre após a liberação das rotas.
2. O valor total da nota deve corresponder ao total das rotas liberadas.
3. O emitente deve ser compatível com o prestador e com a empresa.
4. Documentos duplicados devem ser bloqueados ou sinalizados.
5. O financeiro pode aprovar ou recusar documentos divergentes.
6. O motivo da recusa deve ficar disponível ao prestador.

## Títulos e pagamentos

1. A aprovação da NFSe pode gerar um título automaticamente.
2. O título deve ser vinculado ao titular do documento.
3. O vencimento deve seguir configuração prévia.
4. Pagamentos, baixas e estornos devem possuir histórico.
5. O prestador deve conseguir consultar pagamentos liberados ao seu perfil.

## Acessos

1. Cada usuário acessa somente os menus permitidos.
2. Motoristas acessam apenas o portal correspondente.
3. Usuários internos visualizam somente empresas autorizadas.
4. Permissões devem ser validadas no backend.
5. Ações críticas devem ser auditadas.

## Score

1. O score considera desempenho operacional.
2. Pode utilizar disponibilidade, escalas, presenças e faltas.
3. A fórmula e os pesos ainda precisam ser formalizados.
4. O score deve ser interpretado como apoio à gestão, não como decisão automática isolada.

## Multiempresa

1. Dados de empresas diferentes devem permanecer isolados.
2. Usuários devem acessar apenas empresas autorizadas.
3. Relatórios e operações devem respeitar o contexto da empresa selecionada.
4. Bases operacionais pertencem a uma empresa.

## Regras ainda pendentes de validação

- fórmula completa do score;
- níveis de aprovação financeira;
- política de cancelamento;
- ordenação da fila;
- estados de rotas e documentos;
- regras de conciliação;
- política de retenção de auditorias;
- critérios exatos para cada modalidade de check-in.
