# Blueprint 17.3 — Auditoria dos consumidores legados restantes

## Objetivo

Classificar os usos restantes de `tipo_cadastro = 'Motorista'` / `tipo_prestador` para evitar substituições mecânicas que alterem a semântica de Portal, histórico, escala ou fila.

A regra arquitetural da Blueprint 17 permanece:

- `pessoas` é o cadastro mestre;
- `pessoa_vinculos` representa papéis operacionais;
- `usuarios.pessoa_id` representa identidade/autenticação e não deve ser confundido com papel;
- `motorista_id` pode continuar como nome físico legado nesta etapa, mas semanticamente aponta para `pessoas.id` quando o contexto exigir o papel MOTORISTA;
- vínculo ativo deve ser usado em operações atuais; histórico não pode desaparecer apenas porque um vínculo foi inativado depois.

## Classificação

### 1. Guarda de acesso do Portal Motorista

**Situação:** existe validação de sessão/usuário que ainda confirma Motorista por `tipo_cadastro` / `tipo_prestador` antes de permitir acesso ao portal.

**Classificação:** REDESENHAR.

**Motivo:** o destino arquitetural é Portal Prestador, capaz de atender mais de um papel operacional. Trocar diretamente a condição por `MOTORISTA` perpetuaria a restrição conceitual do portal e dificultaria Ajudante/outros prestadores.

**Ação:** manter temporariamente até existir uma política explícita de acesso ao Portal Prestador baseada em capacidade + vínculos permitidos.

---

### 2. Helper `buscar_motorista_logado`

**Situação:** resolve a Pessoa vinculada ao usuário e ainda exige classificação legada de Motorista.

**Classificação:** REDESENHAR.

**Motivo:** o helper mistura identidade autenticada com papel operacional. O desenho futuro deve primeiro resolver a Pessoa da sessão e depois verificar o papel/capacidade exigido pelo caso de uso.

**Ação:** não migrar isoladamente. Substituir no futuro por composição do tipo `pessoa_logada()` + `pessoa_possui_vinculo(...)` ou política equivalente.

---

### 3. Listagem operacional simples de Motoristas ativos

**Situação:** ainda há consulta que lista Pessoas ativas como Motoristas usando campos legados, sem componente histórico.

**Classificação:** MIGRAR AGORA.

**Motivo:** quando a finalidade é selecionar um Motorista atual para uma operação, a fonte correta já é `pessoa_vinculos` com `MOTORISTA` ativo.

**Ação:** localizar o consumidor exato e migrar com teste restrito ao handler, preservando tenant e status da Pessoa.

---

### 4. `query_motoristas` para seleção/filtro operacional

**Situação:** consulta monta uma lista de Motoristas ativos, inclusive com tratamento de Super Admin/empresa, ainda por `tipo_cadastro = 'Motorista'`.

**Classificação:** MIGRAR AGORA.

**Motivo:** é uma lista de candidatos atuais, não histórico. Deve seguir a mesma semântica já adotada em lançamento/edição/visualização de rotas.

**Ação:** migrar para `EXISTS pessoa_vinculos` preservando exatamente a lógica multiempresa existente.

---

### 5. Escala de Motoristas

**Situação:** consulta de escala usa `mot.tipo_cadastro = 'Motorista'` junto de `escala_motorista` e `ciencia_escala_motorista`.

**Classificação:** MIGRAR COM CUIDADO.

**Motivo:** para montar candidatos atuais de escala, o papel MOTORISTA deve vir de `pessoa_vinculos`. Porém registros de escala já existentes são históricos e não devem desaparecer se o vínculo for posteriormente inativado.

**Ação:** separar semanticamente "candidatos atuais para escala" de "Motoristas já presentes em escala/histórico" antes da substituição.

---

### 6. Histórico de Motoristas

**Situação:** consulta combina `tipo_cadastro = 'Motorista'` com IDs encontrados em `escala_motorista` e outros registros operacionais.

**Classificação:** MANTER / REDESENHAR.

**Motivo:** a própria consulta demonstra intenção histórica: uma Pessoa deve continuar aparecendo se possui atividade passada, mesmo que não seja mais Motorista ativo. Trocar tudo por vínculo ativo criaria perda de visibilidade histórica.

**Ação:** no redesenho, usar algo equivalente a `vínculo MOTORISTA (ativo ou histórico) OR existência de atividade operacional histórica`, sem apagar a segunda condição.

---

### 7. Fila / score / auditoria operacional de Motoristas

**Situação:** consulta agrega Pessoas por `tipo_cadastro = 'Motorista'` ou presença em `escala_motorista`, `fila_cancelados_base` e `auditoria_checkin_base`.

**Classificação:** REDESENHAR.

**Motivo:** há duas populações diferentes no mesmo SELECT: candidatos atuais e pessoas com rastros históricos. Um filtro simples de vínculo ativo mudaria o conjunto de dados e poderia apagar ex-Motoristas das análises.

**Ação:** separar candidato atual de participante histórico antes de migrar a origem do papel.

## Ordem recomendada

1. Migrar o consumidor operacional simples remanescente (item 3).
2. Migrar `query_motoristas` de seleção/filtro atual (item 4).
3. Revisar Escala distinguindo cadastro atual de histórico (item 5).
4. Tratar Portal Motorista somente dentro do redesenho Portal Prestador (itens 1 e 2).
5. Manter Histórico/Fila sem substituição cega até definir consulta com preservação de ex-Motoristas (itens 6 e 7).

## Critério de encerramento da 17.3

A Blueprint 17.3 pode ser considerada concluída quando:

- não houver uso legado em seleção/validação de papel operacional atual onde `pessoa_vinculos` já seja a fonte correta;
- Portal tenha uma decisão explícita de política de acesso sem confundir login com papel;
- consultas históricas preservem pessoas que tiveram atividade mesmo após inativação do vínculo;
- Escala diferencie candidato atual de registro histórico;
- testes cubram tenant, vínculo ativo e preservação histórica nos pontos migrados.
