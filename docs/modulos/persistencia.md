# Modulo: Persistencia e Repositorios

Atualizado em: 2026-02-13

## 1. Responsabilidade

Implementar acesso a dados de forma padronizada e segura para API e workers, incluindo:

- conexao MongoDB resiliente ao contexto assicrono;
- criacao de colecoes/indices;
- repositories especializados por agregado;
- injeção de dependencias para FastAPI.

## 2. Componentes

## 2.1 Conexao (`src/db/connection.py`)

- gerencia singleton de client/database Motor;
- detecta troca de event loop e recria conexao quando necessario;
- expoe:
  - `get_mongo_client()`
  - `get_database()`
  - `get_db()` (alias)
  - `close_mongo_client()`

Importancia:

- workers Celery usam `asyncio.run()` por task; sem esse tratamento haveria erros de loop/handle invalido.

## 2.2 Migracoes (`src/db/migrations.py`)

- cria colecoes base se nao existirem;
- garante indices de busca/ordenacao/unicidade nas colecoes principais;
- executada no startup da API via lifespan (`src/app.py`).

## 2.3 Repositories (`src/db/repositories.py`)

Implementa repositorios por agregado:

- `SubmissionRepository`
- `BookRepository`
- `SummaryRepository`
- `KnowledgeBaseRepository`
- `ArticleRepository`
- `CredentialRepository`
- `PromptRepository`
- `ContentSchemaRepository`
- `PipelineConfigRepository`

## 2.4 Dependencias FastAPI (`src/api/dependencies.py`)

- fabrica instancias de repositories por request;
- desacopla rotas da criacao de conexao.

## 3. Comportamentos de repositorio relevantes

## 3.1 Timestamps padrao

- updates sempre incluem `updated_at`.
- criacoes usam `utcnow()` timezone-aware.

## 3.2 Conversao de IDs

- helper `_to_object_id` converte string/ObjectId com seguranca.
- repositorios retornam `None` para IDs invalidos em vez de quebrar fluxo.

## 3.3 Merge incremental de `books.extracted`

- `BookRepository.create_or_update` faz merge em `extracted`, preservando dados existentes e adicionando novas chaves de etapa.

## 3.4 Draft 1:1 por artigo

- `ArticleRepository.save_draft` usa colecao `articles_drafts` com indice unico em `article_id`.

## 3.5 Filtros inteligentes de prompt

- `PromptRepository.list_all` aplica filtros compostos por categoria/provider;
- provider pode ser inferido por `model_id` quando faltante.

## 3.6 Pipeline como documento versionavel

- `PipelineConfigRepository.create_or_update` permite sobrescrever config de pipeline sem migracao de codigo.

## 4. Integracao com camadas superiores

- API consome repositories para CRUD e comandos operacionais.
- Workers consomem repositories para transicoes de status e persistencia de artefatos de etapa.
- UI consome dados processados via API, sem acesso direto ao banco.

## 5. Garantias e limites

Garantias:

- unicidade de `submissions.amazon_url`.
- consistencia de relacionamento 1:1 entre `submission` e `book` por indice unico.
- busca e listagem otimizadas por indices das colecoes principais.

Limites:

- `pipeline_configs` nao possui indice explicito em migracao atual;
- flag `encrypted` de credencial e informativa (sem criptografia aplicada no repository).

## 6. Impacto arquitetural

Este modulo e o fundamento de consistencia do sistema: sem ele, nao ha estado rastreavel de pipeline, nem capacidade de retry/operacao segura baseada em artefatos persistidos por etapa.
