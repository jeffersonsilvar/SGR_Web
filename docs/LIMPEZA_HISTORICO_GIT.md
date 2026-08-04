# Limpeza de arquivos sensíveis do histórico Git

Excluir `.env`, tokens e credenciais no commit atual não os remove dos commits antigos. Antes de tornar o repositório público:

1. Revogue e gere novamente as credenciais expostas.
2. Faça um clone espelho do repositório.
3. Use `git-filter-repo` para remover os caminhos sensíveis de todo o histórico.
4. Envie o histórico reescrito com `--force`.
5. Confirme no GitHub que os arquivos não aparecem em commits antigos.

Exemplo, executado em um clone separado:

```bash
git filter-repo \
  --path .env \
  --path instance/credentials_google_drive.json \
  --path instance/token_google_drive.json \
  --path instance/token_google_drive_antigo.json \
  --path .idea \
  --path __pycache__ \
  --invert-paths
```

Depois:

```bash
git push --force --all
git push --force --tags
```

> A reescrita muda os hashes dos commits. Faça backup e avise qualquer colaborador antes de executar.
