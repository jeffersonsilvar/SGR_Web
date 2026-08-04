<div align="center">



\# SGR Web



\### Sistema de Gestão de Rotas



Plataforma web multiempresa disponibilizada por assinatura para centralização de operações logísticas, gestão de prestadores de serviço, controle de rotas, escalas, documentos e processos financeiros.



> Projeto autoral em evolução, criado a partir de necessidades reais observadas em operações de transportadoras que prestam serviços para grandes operadores logísticos.



</div>



\---



\## Índice



\- \[Sobre o projeto](#sobre-o-projeto)

\- \[Origem do SGR Web](#origem-do-sgr-web)

\- \[O problema](#o-problema)

\- \[A solução](#a-solução)

\- \[Objetivos](#objetivos)

\- \[Público-alvo](#público-alvo)

\- \[Perfis de acesso](#perfis-de-acesso)

\- \[Escopo funcional](#escopo-funcional)

\- \[Principais benefícios](#principais-benefícios)

\- \[Diferenciais](#diferenciais)

\- \[Evolução do projeto](#evolução-do-projeto)

\- \[Visão de longo prazo](#visão-de-longo-prazo)

\- \[Acesso à plataforma](#acesso-à-plataforma)

\- \[Tecnologias](#tecnologias)

\- \[Arquitetura atual](#arquitetura-atual)

\- \[Estrutura do projeto](#estrutura-do-projeto)

\- \[Banco de dados](#banco-de-dados)

\- \[Configuração do ambiente](#configuração-do-ambiente)

\- \[Ambiente de desenvolvimento](#ambiente-de-desenvolvimento)

\- \[Integração com Google Drive](#integração-com-google-drive)

\- \[Deploy no Render](#deploy-no-render)

\- \[Segurança](#segurança)

\- \[Limitações técnicas atuais](#limitações-técnicas-atuais)

\- \[Plano de evolução técnica](#plano-de-evolução-técnica)

\- \[Status do projeto](#status-do-projeto)

\- \[Autor](#autor)



\---



\## Sobre o projeto



O \*\*SGR Web — Sistema de Gestão de Rotas\*\* é uma plataforma web multiempresa criada para centralizar e digitalizar processos operacionais, administrativos e financeiros de empresas de logística.



A solução foi pensada para atender transportadoras que trabalham com diferentes operadores e plataformas de entrega, permitindo que cada empresa gerencie suas bases operacionais, usuários, prestadores de serviço, motoristas, escalas, rotas, documentos e movimentações financeiras em um único ambiente.



O sistema busca substituir controles manuais espalhados entre planilhas, formulários, mensagens, anotações e arquivos isolados por uma operação integrada, rastreável e acessível por computador, celular ou tablet.



\---



\## Origem do SGR Web



O SGR Web surgiu a partir da experiência prática em operações de transportadoras que prestam serviços para a Amazon Flex.



Durante essa vivência, foram observadas dificuldades recorrentes tanto para as empresas quanto para os prestadores de serviço.



Em algumas operações, os motoristas tinham acesso limitado às informações sobre:



\- disponibilidade semanal;

\- escalas e cancelamentos;

\- rotas realizadas;

\- valores de cada rota;

\- faturamento acumulado;

\- envio e aprovação de notas fiscais;

\- previsão e confirmação de pagamentos;

\- divergências operacionais;

\- posição em filas de prestadores cancelados.



Em outros casos, grande parte do processo era controlada por meio de Google Sheets, Google Forms, planilhas do Excel, prints enviados por mensagens e até anotações manuais.



O projeto começou como uma ferramenta de controle financeiro pessoal, voltada ao registro de recebimentos, despesas com combustível e pagamentos de ajudantes. Com o amadurecimento da ideia, evoluiu para uma plataforma gerencial mais ampla, com recursos voltados à operação completa de transportadoras.



\---



\## O problema



Antes do SGR Web, vários processos dependiam de controles manuais e informações distribuídas em diferentes ferramentas.



\### Para a empresa



Entre os principais desafios estavam:



\- criação recorrente de formulários e planilhas para organizar escalas;

\- lançamento manual de rotas;

\- conferência separada de documentos e pagamentos;

\- dificuldade para acompanhar divergências;

\- ausência de uma visão consolidada da operação;

\- retrabalho para corrigir informações incorretas ou duplicadas;

\- dificuldade para comprovar presenças, faltas e check-ins;

\- baixa rastreabilidade sobre alterações realizadas;

\- risco de perda ou esquecimento de rotas;

\- dependência de controles informais para filas e cancelamentos.



\### Para o prestador de serviço



Os principais problemas observados incluíam:



\- pouca visibilidade sobre as rotas realizadas;

\- dificuldade para acompanhar valores a receber;

\- ausência de retorno claro sobre notas fiscais aprovadas ou recusadas;

\- necessidade de procurar presencialmente a equipe da empresa;

\- preenchimento repetitivo de informações em formulários;

\- incerteza sobre sua posição em filas de cancelados;

\- dificuldade para contestar rotas ou valores divergentes;

\- dependência de prints e mensagens para conferir o faturamento;

\- falta de transparência sobre o andamento dos pagamentos.



\### Riscos do processo manual



Esse cenário podia gerar:



\- erros de digitação;

\- duplicidade de registros;

\- perda de informações;

\- pagamento incorreto;

\- falta de evidências para auditoria;

\- tratamento desigual entre prestadores;

\- dificuldade para comprovar presença na base;

\- aumento do retrabalho operacional;

\- atrasos no fechamento financeiro;

\- baixa confiança entre empresa e prestadores de serviço.



\---



\## A solução



O SGR Web centraliza os principais processos da operação logística em uma única plataforma.



Por meio do sistema, a empresa pode:



\- cadastrar suas bases operacionais;

\- gerenciar usuários e perfis de acesso;

\- cadastrar motoristas, prestadores e ajudantes;

\- criar e acompanhar escalas;

\- lançar rotas;

\- registrar cancelamentos;

\- organizar filas de prestadores;

\- acompanhar check-ins;

\- controlar divergências de rota;

\- receber e validar notas fiscais;

\- gerar títulos financeiros;

\- acompanhar pagamentos;

\- registrar movimentações de caixa;

\- consultar relatórios;

\- manter históricos e auditorias.



O prestador de serviço, por sua vez, utiliza um portal próprio para acompanhar sua rotina, consultar informações e realizar ações sem depender constantemente da equipe administrativa.



\---



\## Objetivos



O SGR Web tem como objetivos:



\- centralizar informações operacionais e financeiras;

\- reduzir o uso de planilhas e formulários isolados;

\- automatizar tarefas repetitivas;

\- diminuir erros de preenchimento;

\- melhorar a comunicação entre empresa e prestadores;

\- aumentar a transparência da operação;

\- permitir rastreabilidade das movimentações;

\- facilitar auditorias;

\- organizar documentos e notas fiscais;

\- apoiar a tomada de decisão;

\- reduzir o retrabalho das equipes;

\- preparar a operação para crescimento;

\- permitir o atendimento de múltiplas empresas e bases operacionais.



\---



\## Público-alvo



O sistema foi pensado principalmente para:



\- transportadoras;

\- operadores logísticos;

\- empresas terceirizadas de entrega;

\- empresas que administram motoristas e prestadores de serviço;

\- operações com múltiplas bases de carregamento;

\- equipes que ainda dependem de planilhas para controlar rotas, escalas e pagamentos.



O projeto considera cenários em que uma transportadora pode prestar serviços para diferentes operadores, como Amazon, Mercado Livre, Shopee e outras empresas do setor.



\---



\## Perfis de acesso



O SGR Web utiliza perfis e permissões para limitar o acesso de cada usuário conforme sua responsabilidade.



\### Administrador da empresa



Responsável pela administração geral da empresa dentro do sistema, incluindo configurações, usuários, acessos e visão consolidada da operação.



\### Supervisor ou gerente operacional



Pode acompanhar escalas, lançar rotas, controlar cancelamentos, verificar check-ins, acompanhar divergências e consultar informações operacionais.



\### Financeiro



Responsável pelo recebimento e validação de documentos, aprovação ou recusa de notas fiscais, geração de títulos, movimentações de caixa, pagamentos, conciliação e relatórios financeiros.



\### Motorista ou prestador de serviço



Acessa o Portal do Motorista para:



\- informar ou alterar disponibilidade;

\- consultar escalas;

\- acompanhar rotas realizadas;

\- realizar check-in quando aplicável;

\- enviar notas fiscais;

\- acompanhar documentos;

\- consultar pagamentos;

\- sinalizar divergências de rota.



\### Outros perfis



O sistema também pode contemplar acessos específicos para ajudantes, cadastro, RH, gestores e diretoria, conforme a estrutura da empresa e as permissões configuradas.



\---



\## Escopo funcional



O SGR Web reúne diferentes áreas da operação em uma única solução.



\### Operação de rotas



\- lançamento de novas rotas;

\- associação de rotas a motoristas;

\- visualização de rotas realizadas;

\- controle de rotas escaladas e canceladas;

\- histórico operacional;

\- central de pendências;

\- registro e acompanhamento de divergências.



\### Escala de motoristas



\- confirmação de disponibilidade;

\- registro de ausência;

\- configuração de horários-limite;

\- visualização de escala diária ou semanal;

\- identificação de motoristas escalados;

\- controle de prestadores cancelados;

\- apoio à formação de filas operacionais.



\### Check-in na base



O projeto contempla mecanismos para comprovação de presença na base operacional, incluindo:



\- validação por localização dentro do raio da base;

\- selfie;

\- leitura de QR Code disponível no local.



\### Portal do motorista



Ambiente destinado ao prestador de serviço para concentrar informações e ações relacionadas à sua rotina operacional e financeira.



\### Score do motorista



Recurso voltado ao acompanhamento de desempenho, considerando informações como:



\- disponibilidade;

\- frequência de escalas;

\- presenças;

\- faltas;

\- participação na operação.



\### Gestão documental



\- envio de notas fiscais de serviço;

\- vinculação de documentos às rotas;

\- validação de valores;

\- verificação da empresa emissora;

\- aprovação ou recusa;

\- consulta ao histórico dos documentos.



\### Gestão financeira



\- geração automática de títulos após aprovação da nota fiscal;

\- definição de vencimentos;

\- contas a pagar e a receber;

\- movimentações de caixa;

\- conciliação financeira;

\- acompanhamento de títulos vencidos, baixados, estornados ou pendentes;

\- pagamentos de motoristas e ajudantes;

\- relatórios financeiros.



\### Relatórios e auditorias



\- relatórios operacionais;

\- relatórios financeiros;

\- central gerencial;

\- históricos de movimentações;

\- auditoria de registros;

\- acompanhamento de check-ins;

\- histórico de pagamentos e estornos;

\- apoio à tomada de decisão.



\### Usuários e acessos



\- criação de usuários;

\- perfis de acesso;

\- controle de permissões;

\- configuração de menus;

\- limitação de funcionalidades conforme o perfil;

\- configuração do Portal do Motorista.



\---



\## Principais benefícios



\### Redução do retrabalho



O motorista pode atualizar informações e acompanhar sua rotina diretamente pelo portal, reduzindo solicitações manuais à equipe administrativa.



\### Mais transparência



Prestadores conseguem consultar rotas, valores, documentos, divergências e pagamentos com maior clareza.



\### Controle centralizado



Informações operacionais, financeiras e documentais ficam disponíveis em um único ambiente.



\### Rastreabilidade



Registros e movimentações podem ser acompanhados por históricos e auditorias.



\### Menos erros



A validação de informações ajuda a reduzir divergências em notas fiscais, valores e pagamentos.



\### Melhor gestão operacional



Escalas, presenças, cancelamentos e filas podem ser acompanhados de maneira estruturada.



\### Apoio à decisão



Relatórios e indicadores permitem que gestores tenham uma visão consolidada da empresa.



\### Escalabilidade organizacional



A estrutura multiempresa permite que a solução evolua para atender diferentes transportadoras, bases e operações.



\---



\## Diferenciais



Entre os diferenciais planejados e implementados no SGR Web estão:



\- estrutura multiempresa;

\- múltiplas bases operacionais;

\- portal exclusivo para motoristas e prestadores;

\- controle de escalas com horário-limite;

\- check-in vinculado à base operacional;

\- validação por localização, selfie e QR Code;

\- fila organizada de prestadores cancelados;

\- score de desempenho dos motoristas;

\- geração de mensagens para comunicação com escalados e cancelados;

\- contestação de rotas com valores divergentes;

\- validação de notas fiscais com base nas rotas liberadas;

\- conferência do valor total da nota;

\- verificação da empresa titular;

\- prevenção de documentos duplicados ou inconsistentes;

\- geração automática de títulos financeiros;

\- controle de pagamentos e movimentações;

\- históricos e auditorias;

\- centralização de relatórios gerenciais.



\---



\## Evolução do projeto



O SGR Web nasceu como um sistema de controle financeiro pessoal.



A primeira necessidade era registrar:



\- pagamentos recebidos por rotas;

\- receitas provenientes de diferentes transportadoras;

\- despesas com combustível;

\- pagamentos de ajudantes;

\- movimentações financeiras pessoais relacionadas à operação.



Com o tempo, o projeto passou a incorporar novas regras de negócio e evoluiu para uma plataforma gerencial.



Entre as melhorias já implementadas estão:



\- controle de usuários por perfil;

\- Portal do Motorista;

\- gestão de escalas;

\- controle de horário para alteração de disponibilidade;

\- lançamento e acompanhamento de rotas;

\- registro de divergências;

\- validação de notas fiscais;

\- geração automática de títulos;

\- liberação de rotas após aprovação;

\- gestão financeira;

\- relatórios;

\- históricos;

\- auditorias.



Essa evolução reflete a transformação de uma necessidade individual em uma solução voltada a operações logísticas mais amplas.



\---



\## Visão de longo prazo



A visão de longo prazo é transformar o SGR Web em uma plataforma que possa ser utilizada por transportadoras e empresas de logística para administrar toda a jornada do prestador de serviço.



Entre as possibilidades futuras estão:



\- oferecer o sistema para transportadoras reais;

\- ampliar o suporte a múltiplos operadores logísticos;

\- integrar informações por meio de APIs;

\- importar rotas automaticamente;

\- reduzir a necessidade de lançamentos manuais;

\- disponibilizar informações de diferentes operações em um único portal;

\- permitir que parceiros acompanhem suas rotas sem depender exclusivamente dos aplicativos dos operadores;

\- ampliar os recursos financeiros e de conciliação;

\- evoluir a arquitetura para facilitar manutenção e novas funcionalidades.



\---





\## Acesso à plataforma



O SGR Web é uma aplicação web disponibilizada no modelo de assinatura.



A empresa interessada não precisa instalar o sistema em seus computadores. Após a contratação e configuração do ambiente, os usuários autorizados acessam a plataforma diretamente pelo navegador, utilizando computador, tablet ou celular.



A aplicação está hospedada em ambiente web:



\*\*\[Acessar o SGR Web](https://sgr-web.onrender.com)\*\*



A rota inicial redireciona usuários não autenticados para a tela de login. O acesso completo depende de credenciais válidas e de um ambiente configurado para a empresa assinante.



> O repositório apresenta a documentação técnica do produto, mas não disponibiliza credenciais administrativas, dados reais ou acesso irrestrito ao sistema.



\---





\## Modelo de disponibilização



O SGR Web foi concebido como um produto web no modelo de assinatura.



\### Para a empresa cliente



A empresa contratante:



\- não precisa instalar o sistema localmente;

\- não precisa manter servidores próprios;

\- acessa a solução por meio do navegador;

\- recebe usuários e permissões conforme sua operação;

\- pode utilizar múltiplas bases operacionais;

\- acessa o sistema por computador, tablet ou celular;

\- utiliza a aplicação conforme o plano e as condições contratadas.



\### Responsabilidades técnicas



A manutenção da aplicação, atualizações, correções, infraestrutura, segurança e evolução do produto permanecem sob responsabilidade do fornecedor da plataforma, conforme o escopo comercial definido.



\### Observação sobre este repositório



As instruções técnicas presentes neste README são destinadas exclusivamente a:



\- manutenção do produto;

\- desenvolvimento;

\- testes;

\- homologação;

\- implantação em infraestrutura controlada;

\- análise técnica do portfólio.



Elas não representam um procedimento de instalação para empresas clientes.



\---



\## Tecnologias



\### Backend



\- \*\*Python\*\* — linguagem principal;

\- \*\*Flask\*\* — framework web;

\- \*\*Gunicorn\*\* — servidor WSGI utilizado em produção;

\- \*\*Werkzeug\*\* — segurança de senhas e utilitários HTTP;

\- \*\*MySQL Connector/Python\*\* — conexão direta com o banco MySQL;

\- \*\*python-dotenv\*\* — carregamento de variáveis de ambiente.



\### Frontend



\- \*\*HTML5\*\*;

\- \*\*CSS3\*\*;

\- \*\*JavaScript\*\*;

\- \*\*Jinja2\*\* — renderização dos templates do Flask.



\### Banco de dados



\- \*\*MySQL\*\*;

\- estrutura relacional composta atualmente por aproximadamente \*\*40 tabelas\*\*;

\- scripts públicos separados entre estrutura e dados demonstrativos:

&#x20; - `database/schema.sql`;

&#x20; - `database/seed\_demo.sql`.



O arquivo `schema.sql` foi exportado de um servidor MySQL 5.6.26. A compatibilidade com versões mais recentes deve ser validada antes de uma migração de ambiente.



\### Documentos, relatórios e arquivos



\- \*\*OpenPyXL\*\* — geração e manipulação de planilhas;

\- \*\*ReportLab\*\* — geração de documentos PDF;

\- \*\*Pillow\*\* — processamento de imagens;

\- \*\*qrcode\*\* — geração de QR Codes;

\- \*\*ElementTree\*\* — leitura de XML;

\- parser próprio para \*\*NFS-e/DANFSe\*\*.



\### Integrações



\- \*\*Google Drive API\*\*;

\- autenticação por OAuth ou Service Account;

\- armazenamento organizado por empresa, categoria e contexto do documento.



\### Infraestrutura



\- \*\*Git e GitHub\*\* — versionamento;

\- \*\*Render\*\* — hospedagem da aplicação;

\- \*\*Gunicorn\*\* — inicialização em produção por meio de `gunicorn app:app`.



\---



\## Arquitetura atual



O SGR Web utiliza atualmente uma arquitetura monolítica baseada em Flask.



```text

Navegador

&#x20;   │

&#x20;   ▼

Flask + Jinja2

&#x20;   │

&#x20;   ├── Autenticação e sessões

&#x20;   ├── Regras operacionais

&#x20;   ├── Gestão financeira

&#x20;   ├── Relatórios e auditorias

&#x20;   ├── Processamento de XML/PDF/planilhas

&#x20;   └── Integração opcional com Google Drive

&#x20;   │

&#x20;   ▼

MySQL

```



\### Camada de aplicação



O arquivo `app.py` concentra atualmente:



\- criação e configuração da aplicação Flask;

\- filtros Jinja;

\- autenticação;

\- sessões;

\- validações;

\- regras de negócio;

\- consultas SQL;

\- rotas;

\- geração de relatórios;

\- fluxos operacionais e financeiros.



A versão analisada possui aproximadamente:



\- \*\*22 mil linhas\*\* em `app.py`;

\- \*\*112 rotas Flask\*\*;

\- \*\*64 templates HTML\*\*;

\- \*\*40 tabelas\*\* no schema público.



Esses números demonstram a amplitude funcional do sistema, mas também evidenciam a principal dívida técnica atual: o alto acoplamento do arquivo principal.



\### Acesso ao banco de dados



A conexão com MySQL é centralizada em `database.py` e utiliza exclusivamente variáveis de ambiente.



A aplicação ainda executa consultas SQL diretamente nas rotas e funções auxiliares. Não existe, nesta versão, uma camada ORM ou Repository independente.



\### Configuração



O módulo `config.py`:



\- carrega as variáveis locais com `python-dotenv`;

\- exige uma `SECRET\_KEY`;

\- configura limite máximo de upload;

\- define a pasta local de arquivos.



\### Processamento de NFS-e



O módulo `danfse\_parser.py` implementa um parser próprio para:



\- XML de NFS-e e DANFSe;

\- diferentes namespaces;

\- normalização de CPF/CNPJ;

\- datas;

\- valores monetários;

\- informações de prestador, tomador e serviço.



\### Armazenamento de arquivos



O módulo `google\_drive\_storage.py` concentra a integração opcional com Google Drive, incluindo:



\- OAuth;

\- Service Account;

\- renovação de credenciais;

\- criação de hierarquia de pastas;

\- upload;

\- download;

\- obtenção de metadados;

\- registro dos arquivos no sistema.



Quando a integração não está disponível, a aplicação possui tratamento para evitar que a importação interrompa toda a inicialização.



\---



\## Estrutura do projeto



```text

SGR\_Web/

├── app.py

├── application.py

├── config.py

├── database.py

├── danfse\_parser.py

├── google\_drive\_storage.py

├── requirements.txt

├── Procfile

├── README.md

├── .env.example

├── .gitignore

│

├── database/

│   ├── schema.sql

│   └── seed\_demo.sql

│

├── docs/

│   ├── ESTRUTURA\_DO\_PROJETO.md

│   ├── LIMPEZA\_HISTORICO\_GIT.md

│   ├── PROXIMOS\_PASSOS.md

│   └── SEGURANCA\_E\_CONFIGURACAO.md

│

├── scripts/

│   ├── google\_drive\_oauth\_setup.py

│   └── testar\_google\_drive\_upload.py

│

├── static/

│   ├── css/

│   ├── js/

│   └── uploads/

│       └── .gitkeep

│

├── templates/

├── tests/

│   └── .gitkeep

│

└── instance/

&#x20;   └── .gitkeep

```



\### Arquivos principais



| Arquivo | Responsabilidade |

|---|---|

| `app.py` | Aplicação Flask, rotas e regras de negócio atuais |

| `application.py` | Ponte de compatibilidade para ambientes que utilizam `application:application` |

| `config.py` | Configuração carregada por variáveis de ambiente |

| `database.py` | Criação de conexões MySQL |

| `danfse\_parser.py` | Leitura e normalização de XML de NFS-e/DANFSe |

| `google\_drive\_storage.py` | Integração e armazenamento no Google Drive |

| `Procfile` | Comando de inicialização em produção |

| `requirements.txt` | Dependências Python |

| `.env.example` | Modelo público das variáveis necessárias |

| `.gitignore` | Proteção contra versionamento de segredos e arquivos privados |



\---



\## Banco de dados



O projeto utiliza MySQL.



\### Arquivos públicos



```text

database/

├── schema.sql

└── seed\_demo.sql

```



\- `schema.sql` contém somente a estrutura das tabelas, índices, chaves e relacionamentos;

\- `seed\_demo.sql` é reservado a dados completamente fictícios;

\- dumps reais, backups, documentos, credenciais e dados pessoais não devem ser versionados.



\### Criando o banco



Acesse o MySQL:



```bash

mysql -u root -p

```



Crie um banco com codificação UTF-8:



```sql

CREATE DATABASE sgr\_web

CHARACTER SET utf8mb4

COLLATE utf8mb4\_unicode\_ci;

```



Importe a estrutura:



```bash

mysql -u root -p sgr\_web < database/schema.sql

```



Caso existam dados fictícios no `seed\_demo.sql`:



```bash

mysql -u root -p sgr\_web < database/seed\_demo.sql

```



\### Observação



A estrutura contém tabelas com collations diferentes, refletindo a evolução histórica do projeto. A padronização completa para `utf8mb4` faz parte do roadmap técnico e deve ser executada com testes e backup.



\---



\## Configuração do ambiente



\### 1. Criar o arquivo `.env`



No Windows PowerShell:



```powershell

Copy-Item .env.example .env

```



No Linux ou macOS:



```bash

cp .env.example .env

```



\### 2. Configurar as variáveis



```env

\# Flask

FLASK\_ENV=development

FLASK\_DEBUG=1

SECRET\_KEY=gere-uma-chave-segura



\# MySQL

MYSQL\_HOST=localhost

MYSQL\_PORT=3306

MYSQL\_USER=sgr\_user

MYSQL\_PASSWORD=troque-esta-senha

MYSQL\_DATABASE=sgr\_web



\# Uploads

UPLOAD\_FOLDER=static/uploads

MAX\_CONTENT\_LENGTH\_MB=4



\# Google Drive — opcional

GOOGLE\_DRIVE\_ENABLED=false

GOOGLE\_DRIVE\_AUTH\_MODE=oauth

GOOGLE\_DRIVE\_CREDENTIALS\_FILE=instance/credentials\_google\_drive.json

GOOGLE\_DRIVE\_TOKEN\_FILE=instance/token\_google\_drive.json

GOOGLE\_DRIVE\_ROOT\_FOLDER\_NAME=SGR Web

```



Gere uma chave segura:



```bash

python -c "import secrets; print(secrets.token\_hex(32))"

```



Nunca envie o arquivo `.env` ao GitHub.



\---



\## Ambiente de desenvolvimento



> Esta seção é destinada apenas a desenvolvedores e mantenedores do projeto. Empresas assinantes utilizam o SGR Web diretamente pelo navegador e não precisam executar este procedimento.



\### Pré-requisitos



\- Python 3;

\- MySQL;

\- Git;

\- `pip`;

\- ambiente virtual recomendado.



\### 1. Clonar o repositório



```bash

git clone https://github.com/jeffersonsilvar/SGR\_Web.git

cd SGR\_Web

```



\### 2. Criar o ambiente virtual



Windows:



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

```



Linux ou macOS:



```bash

python3 -m venv .venv

source .venv/bin/activate

```



\### 3. Instalar as dependências



```bash

python -m pip install --upgrade pip

pip install -r requirements.txt

```



\### 4. Preparar o banco



Crie o banco e importe:



```bash

mysql -u root -p sgr\_web < database/schema.sql

```



\### 5. Configurar o `.env`



Copie `.env.example` para `.env` e informe as credenciais do banco local.



\### 6. Executar a aplicação



```bash

python app.py

```



Por padrão, a execução direta utiliza:



```text

http://localhost:8080

```



Também é possível iniciar com Flask:



Windows PowerShell:



```powershell

$env:FLASK\_APP = "app.py"

flask run

```



Linux ou macOS:



```bash

export FLASK\_APP=app.py

flask run

```



\### Produção local com Gunicorn



```bash

gunicorn app:app

```



> O Gunicorn não possui suporte nativo ao Windows. Em Windows, use `python app.py`, Flask ou um ambiente Linux/WSL para testar o servidor WSGI.



\---



\## Integração com Google Drive



A integração é opcional.



Para manter o sistema funcionando sem ela:



```env

GOOGLE\_DRIVE\_ENABLED=false

```



\### Modos suportados



```env

GOOGLE\_DRIVE\_AUTH\_MODE=oauth

```



ou:



```env

GOOGLE\_DRIVE\_AUTH\_MODE=service\_account

```



\### OAuth local



Os scripts auxiliares ficam em:



```text

scripts/

├── google\_drive\_oauth\_setup.py

└── testar\_google\_drive\_upload.py

```



As credenciais e tokens gerados devem ficar na pasta `instance/`, que está protegida pelo `.gitignore`.



Nunca publique:



\- `credentials\_google\_drive.json`;

\- `token\_google\_drive.json`;

\- Service Accounts;

\- refresh tokens;

\- JSON de credenciais;

\- conteúdo base64 de tokens.



Em hospedagens, os segredos devem ser configurados diretamente nas variáveis de ambiente da plataforma.



\---



\## Deploy no Render



A aplicação está configurada para iniciar com Gunicorn.



\### Comando de build



```bash

pip install -r requirements.txt

```



\### Comando de inicialização



```bash

gunicorn app:app

```



O `Procfile` também contém:



```text

web: gunicorn app:app --bind 0.0.0.0:$PORT

```



\### Variáveis necessárias no Render



Configure no painel do serviço:



```text

SECRET\_KEY

MYSQL\_HOST

MYSQL\_PORT

MYSQL\_USER

MYSQL\_PASSWORD

MYSQL\_DATABASE

UPLOAD\_FOLDER

MAX\_CONTENT\_LENGTH\_MB

```



Adicione também as variáveis do Google Drive quando a integração estiver habilitada.



\### Persistência de arquivos



O sistema não deve depender do disco efêmero do Render para documentos permanentes. Arquivos importantes devem ser enviados a um serviço externo, como o Google Drive configurado pelo projeto.



\---



\## Segurança



O repositório foi reorganizado para não versionar:



\- `.env`;

\- senhas;

\- tokens;

\- credenciais do Google;

\- uploads;

\- selfies;

\- notas fiscais;

\- justificativas;

\- dumps reais;

\- bancos locais;

\- arquivos de IDE;

\- caches Python.



\### Boas práticas obrigatórias



\- usar senhas diferentes por ambiente;

\- rotacionar credenciais expostas anteriormente;

\- armazenar segredos apenas em variáveis de ambiente;

\- manter `instance/` e `static/uploads/` fora do Git;

\- nunca publicar dados reais em `seed\_demo.sql`;

\- limitar permissões da conta do banco;

\- revisar logs para não expor dados pessoais;

\- criar backups antes de alterações no schema.



Documentação complementar:



```text

docs/SEGURANCA\_E\_CONFIGURACAO.md

docs/LIMPEZA\_HISTORICO\_GIT.md

```



\---



\## Limitações técnicas atuais



A versão atual possui as seguintes limitações conhecidas:



\- grande concentração de responsabilidades em `app.py`;

\- consultas SQL executadas diretamente nas rotas;

\- ausência de uma camada de serviços formal para todos os domínios;

\- ausência de ORM e migrations versionadas;

\- pasta de testes ainda sem uma suíte automatizada;

\- dependências do `requirements.txt` ainda não fixadas por versão;

\- tratamento de erros baseado parcialmente em `print` e `flash`;

\- schema com collations historicamente diferentes;

\- documentação funcional dos módulos ainda em construção;

\- ausência de conta pública de demonstração;

\- arquivos de frontend ainda pouco componentizados.



Esses pontos são tratados como roadmap, não como funcionalidades concluídas.



\---



\## Plano de evolução técnica



A modernização será realizada de forma gradual, preservando os endpoints e os fluxos existentes.



\### Fase 1 — Base segura e reproduzível



\- \[x] Remover segredos e dados pessoais;

\- \[x] criar `.env.example`;

\- \[x] criar `.gitignore`;

\- \[x] separar schema e dados demonstrativos;

\- \[x] publicar no Render;

\- \[x] documentar a fundação do produto;

\- \[ ] fixar versões das dependências;

\- \[ ] validar a instalação a partir de um clone limpo.



\### Fase 2 — Qualidade e testes



\- \[ ] criar `create\_app`;

\- \[ ] adicionar testes de inicialização;

\- \[ ] testar autenticação;

\- \[ ] testar permissões;

\- \[ ] testar rotas críticas;

\- \[ ] configurar logging estruturado;

\- \[ ] criar tratamento padronizado de erros.



\### Fase 3 — Modularização com Blueprints



Estrutura planejada:



```text

app/

├── \_\_init\_\_.py

├── extensions.py

├── auth/

├── empresas/

├── pessoas/

├── motoristas/

├── operacao/

├── financeiro/

├── relatorios/

├── auditoria/

├── services/

└── utils/

```



A migração será realizada módulo a módulo, evitando uma reescrita total.



\### Fase 4 — Persistência e banco



\- \[ ] criar camada de repositórios;

\- \[ ] padronizar transações;

\- \[ ] adicionar migrations;

\- \[ ] revisar índices e constraints;

\- \[ ] padronizar charset e collation;

\- \[ ] remover consultas duplicadas;

\- \[ ] otimizar o dashboard e relatórios.



\### Fase 5 — Entrega contínua



\- \[ ] adicionar testes no GitHub Actions;

\- \[ ] verificar formatação e qualidade do código;

\- \[ ] automatizar validações antes do deploy;

\- \[ ] documentar rollback;

\- \[ ] criar versionamento e changelog.



\---



\## Status do projeto



> \*\*Em desenvolvimento contínuo\*\*



O SGR Web é um projeto autoral em evolução.



Parte das funcionalidades já está implementada e outras continuam sendo aprimoradas. A arquitetura também passará por uma reorganização gradual para separar responsabilidades, modularizar os recursos e facilitar a manutenção do sistema.



A documentação técnica inicial já inclui:



\- tecnologias utilizadas;

\- arquitetura atual;

\- estrutura de diretórios;

\- banco de dados;

\- configuração do ambiente;

\- ambiente de desenvolvimento e execução técnica;

\- integração com Google Drive;

\- deploy no Render;

\- segurança;

\- limitações conhecidas;

\- plano de evolução técnica.



As próximas versões serão dedicadas a diagramas de fluxo, documentação detalhada dos módulos, capturas de tela, casos de uso, manual do usuário e licença do projeto.



\---



\## Autor



\*\*Jefferson Silva\*\*



Analista de Sistemas com experiência em implantação de ERP, melhoria de processos e suporte a operações empresariais, em transição para Desenvolvimento Backend com Python e Flask.



\- GitHub: \[@jeffersonsilvar](https://github.com/jeffersonsilvar)

\- LinkedIn: \[Jefferson Silva Lima](https://www.linkedin.com/in/jeffersonsilvarlima)



\---



<div align="center">



\*\*SGR Web — centralizando a operação logística, do planejamento ao pagamento.\*\*



</div>



