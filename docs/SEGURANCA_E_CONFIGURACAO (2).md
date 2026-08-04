# Segurança e configuração local

1. Altere imediatamente as credenciais que já foram expostas em arquivos anteriores.
2. Copie `.env.example` para `.env`.
3. Preencha o `.env` com as credenciais locais.
4. Nunca faça commit do arquivo `.env`.
5. Importe `database/schema.sql` em um banco vazio.
6. Mantenha dados reais, documentos, selfies e notas fiscais fora do Git.

## Gerar uma SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Preparar o ambiente

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```
