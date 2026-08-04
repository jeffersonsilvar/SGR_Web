# Estrutura atual do projeto

```text
SGR_Web/
├── app.py                       # Aplicação Flask monolítica atual
├── application.py               # Compatibilidade WSGI
├── config.py                    # Configurações via variáveis de ambiente
├── database.py                  # Conexão MySQL
├── danfse_parser.py             # Leitura e normalização de XML de NFSe
├── google_drive_storage.py      # Integração opcional com Google Drive
├── requirements.txt
├── Procfile
├── README.md
├── .env.example
├── .gitignore
├── database/
│   ├── schema.sql               # Estrutura do banco, sem dados reais
│   └── seed_demo.sql            # Dados fictícios de demonstração
├── docs/
├── scripts/
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/                 # Conteúdo ignorado pelo Git
├── templates/
├── tests/
└── instance/                    # Credenciais locais ignoradas pelo Git
```

## Decisão de refatoração

Nesta etapa, o `app.py` permanece na raiz para preservar o funcionamento em produção. A modularização será gradual, usando Flask Blueprints, após a criação de testes mínimos para autenticação, banco e fluxos críticos.
