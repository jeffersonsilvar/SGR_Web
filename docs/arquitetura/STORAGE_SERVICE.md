# StorageService — contrato único de arquivos do SGR Web

## Decisão

Todo novo fluxo de upload do SGR deve utilizar `app_modules.storage.StorageService`.
Módulos de negócio não devem chamar Google Drive, S3 ou outro provider diretamente.

O provider atual é Google Drive. A abstração existe para permitir troca futura por
S3, Cloudflare R2, Azure Blob, Google Cloud Storage ou outro provider sem reescrever
as regras de cada módulo.

## Regras obrigatórias

1. Arquivos permanentes são armazenados pelo provider configurado.
2. Armazenamento local só pode ser temporário durante processamento.
3. Não existe fallback local silencioso para arquivos permanentes.
4. Todo arquivo permanente deve possuir registro em `arquivos_sistema`.
5. `arquivos_sistema` deve registrar empresa, origem, registro de origem, tipo,
   provider, identificador externo, SHA-256, versão e usuário responsável quando aplicável.
6. O acesso do usuário ocorre por rota protegida do SGR; arquivos privados não são
   publicados diretamente no provider.
7. As regras de isolamento multiempresa continuam sendo responsabilidade da rota ou
   serviço consumidor antes de entregar o arquivo.
8. O XML fiscal original nunca é substituído por uma representação visual.

## Contrato de gravação

Para uploads Flask/Werkzeug, preferir:

```python
storage = StorageService()
info = storage.armazenar_upload(
    cur,
    arquivo=arquivo,
    empresa_id=empresa_id,
    empresa_nome=empresa_nome,
    categoria="Categoria",
    subcategoria="Subcategoria",
    pasta_registro=f"registro_{registro_id}",
    origem="ORIGEM_DO_MODULO",
    origem_id=registro_id,
    tipo_arquivo="TIPO_DO_ARQUIVO",
    pessoa_id=pessoa_id,
    criado_por_usuario_id=usuario_id,
)
```

Quando o módulo já possui um arquivo temporário no filesystem, pode chamar
`armazenar_arquivo(...)` diretamente.

## Contrato de leitura

O consumidor busca primeiro os metadados autorizados em `arquivos_sistema` e então
usa:

```python
storage = StorageService(provider=arquivo["storage_provider"])
conteudo = storage.baixar_arquivo(arquivo)
```

Isso evita que módulos conheçam `drive_file_id`, SDK do Google ou URLs públicas.

## Migração progressiva dos módulos

A adoção será progressiva para reduzir risco em fluxos legados. Prioridade:

- Documentos Fiscais — XML/PDF de NF-e, NFS-e e CT-e;
- Financeiro — comprovantes de baixa e documentos financeiros;
- Portal do Prestador — XML/PDF e documentos enviados por prestadores;
- Operação — check-in/selfie e justificativas de ausência;
- Ocorrências — anexos;
- Entregas — fotos e assinaturas;
- demais módulos com upload.

Novos fluxos não devem criar outro mecanismo de armazenamento paralelo.

## Visualização fiscal

A representação visual de NF-e, NFS-e e CT-e é uma camada de apresentação. O XML
original continua privado e imutável no StorageService.

Fluxo:

```text
XML original privado
        ↓
StorageService
        ↓
parser fiscal
        ↓
visualização auxiliar no SGR
```

A tela deve identificar explicitamente que a representação é auxiliar e permitir o
download do XML original.

## Transações externas

Banco de dados e storage externo não participam da mesma transação ACID. Portanto,
um upload bem-sucedido seguido de rollback do banco pode criar arquivo órfão no
provider. Antes da conclusão definitiva da infraestrutura, deve existir compensação
por exclusão do objeto externo ou rotina segura de reconciliação de órfãos.

Essa limitação não autoriza fallback local silencioso.
