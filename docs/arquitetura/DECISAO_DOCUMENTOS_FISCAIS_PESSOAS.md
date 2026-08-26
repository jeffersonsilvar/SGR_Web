# Decisão arquitetural — Documentos Fiscais, Pessoas e normalização textual

## Status

Aceita para o Projeto D0 / SGR Web.

## Princípios

1. **Pessoa é o cadastro mestre.** Documentos Fiscais, Financeiro, Rotas e futuros portais não criam cadastros paralelos de fornecedor, motorista, ajudante ou cliente.
2. **Todo documento fiscal efetivado deve estar vinculado a uma Pessoa da mesma empresa.** Um XML pode ser lido e mantido como rascunho temporário, mas não pode ser concluído em `documentos_fiscais` sem `pessoa_id` válido.
3. **XML é a fonte estruturada preferencial.** NF-e e NFS-e compatíveis devem preencher automaticamente número, série, chave, emissão, competência, emitente, destinatário, valor e descrição quando disponíveis.
4. **O arquivo original é preservado.** A normalização visual nunca substitui a evidência fiscal original; o XML/PDF armazenado permanece disponível para auditoria.
5. **Fornecedor inexistente bloqueia a conclusão da importação.** O usuário deve cadastrar a Pessoa pelo CPF/CNPJ e, depois, retomar/concluir a importação.
6. **CNPJ terá consulta cadastral inteligente no módulo Pessoas.** A integração com fonte oficial/serviço autorizado será responsabilidade do domínio Pessoas, não do módulo Documentos.
7. **CPF não pressupõe consulta pública de dados cadastrais completos.** Pessoa Física continuará com cadastro manual/validado, salvo futura integração legalmente adequada.
8. **Documento aprovado gera obrigação, não pagamento.** O fluxo é Documento → Título Financeiro → Baixa → Caixa.

## Normalização de apresentação

O Projeto D0 adotará, quando o módulo Pessoas/Configurações for revisado, o parâmetro geral:

`cadastros.normalizacao_texto`

Valores previstos:

- `ORIGINAL`: exibe/cadastra conforme informado pela fonte;
- `PADRONIZADO`: normaliza capitalização para apresentação, preservando o valor original em sua fonte/auditoria;
- `MAIUSCULO`: apresentação em caixa alta quando exigido pela empresa.

`PADRONIZADO` é o padrão recomendado. Não é camelCase de programação; trata-se de capitalização consistente para nomes empresariais, pessoas e descrições cadastrais, com tratamento de preposições e siglas/sufixos jurídicos.

Exemplo:

`ROTA CERTA SERVICOS LOGISTICOS LTDA` → `Rota Certa Servicos Logisticos Ltda`

O XML original continua inalterado.

## Fluxo de importação inteligente

```text
Upload XML
  → detectar modelo fiscal
  → extrair campos
  → preservar XML original
  → localizar Pessoa por CPF/CNPJ + empresa
     → encontrada: vincular
     → não encontrada: bloquear conclusão e solicitar cadastro
  → validar chave duplicada
  → confirmar importação
  → Documento = Recebido
  → análise/aprovação
  → geração controlada de Título Financeiro
```

## Responsabilidades futuras

### Documentos Fiscais
- parser/importação fiscal;
- integridade do documento;
- vínculo obrigatório com Pessoa;
- workflow documental;
- origem do título financeiro.

### Pessoas
- cadastro mestre PF/PJ;
- consulta inteligente de CNPJ;
- normalização cadastral configurável;
- validação de duplicidade por CPF/CNPJ;
- dados oficiais e endereços.

### Financeiro
- títulos;
- baixa;
- estorno;
- movimentações de caixa;
- conciliação.
