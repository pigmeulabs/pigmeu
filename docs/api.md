# API

Atualizado em: 2026-02-13
Base local padrao: `http://localhost:8000`

## 1. Convencoes gerais

- Protocolo: HTTP + JSON.
- Implementacao: FastAPI (`src/app.py`, `src/api/*`).
- Autenticacao: nao implementada.
- IDs: ObjectId serializado como string nas respostas.
- Erros: usam `detail` (string ou objeto/lista).

## 2. Endpoints de sistema

### 2.1 `GET /`

Retorna metadados basicos da API:

- `message`
- `docs`
- `openapi_schema`

### 2.2 `GET /health`

Health check da aplicacao:

- `status` (`ok` quando saudavel)
- `app`
- `environment`

### 2.3 `GET /stats`

Alias operacional de estatisticas agregadas de submissao.

Resposta (mesma de `/tasks/stats`):

- `total_tasks`
- `by_status` (mapa status -> quantidade)
- `success_rate`
- `failed_tasks`

### 2.4 `GET /ui`

Serve a SPA operacional (`src/static/index.html`).

## 3. Endpoints de submissao

Router: `src/api/ingest.py` (`/submit`).

### 3.1 `POST /submit`

Cria nova submissao de review de livro.

Payload base (`SubmissionCreate`):

- obrigatorios:
  - `title` (string)
  - `author_name` (string)
  - `amazon_url` (URL)
- opcionais:
  - `goodreads_url`, `author_site` (URL)
  - `other_links` (lista URL)
  - `textual_information` (string)
  - `run_immediately` (bool, default `true`)
  - `schedule_execution` (datetime; obrigatorio se `run_immediately=false`)
  - `pipeline_id` (default `book_review_v2`)
  - `main_category`
  - `content_schema_id`
  - `article_status`
  - `user_approval_required` (bool)

Validacoes e regras:

- dispara bootstrap de defaults (pipelines/credentials/content schema) antes de validar pipeline;
- rejeita `pipeline_id` inexistente (`422`);
- rejeita duplicidade por `amazon_url` (`400`);
- valida regra de agendamento (`run_immediately=false` exige `schedule_execution`).

Efeito colateral:

- se `run_immediately=true`, enfileira `start_pipeline`.

Resposta `201` (`SubmissionResponse`):

- dados da submissao criada + `status` inicial + timestamps.

### 3.2 `GET /submit/health`

Health especifico do modulo de submissao.

## 4. Endpoints de tasks

Router: `src/api/tasks.py` (`/tasks`).

### 4.1 `GET /tasks/health`

Health especifico do modulo de tasks.

### 4.2 `GET /tasks/stats`

Estatisticas agregadas de submissao (mesmo contrato de `/stats`).

### 4.3 `GET /tasks`

Lista tasks/submissoes com paginacao e filtros.

Query params:

- `skip` (default `0`, min `0`)
- `limit` (default `20`, min `1`, max `100`)
- `status` (opcional)
- `search` (opcional; busca em `title` e `author_name`)

Resposta:

- `tasks` (lista serializada)
- `total`
- `skip`
- `limit`
- `count`

### 4.4 `GET /tasks/{submission_id}`

Retorna detalhe operacional completo da task.

Resposta agregada:

- `submission`
- `book`
- `summaries`
- `knowledge_base`
- `article`
- `draft`
- `progress` (etapas resumidas)
- `pipeline` (metadados e steps visiveis)

Observacao:

- resposta aplica sanitizacao recursiva para tipos nao JSON (ex.: ObjectId).

### 4.5 `PATCH /tasks/{submission_id}`

Atualiza submissao e/ou livro.

Payload aceito:

- `submission`: campos livres aplicados em `submissions`.
- `book.extracted`: merge em `books.extracted` via `create_or_update`.

Resposta:

- `submission` atualizado
- `book` atualizado (ou `null`)
- `progress`

### 4.6 `DELETE /tasks/{submission_id}`

Exclui submissao e dados correlatos.

Efeitos colaterais:

- remove drafts e artigos vinculados por `book_id` e/ou `submission_id`;
- remove `summaries`, `knowledge_base`, `book` e `submission`.

Resposta: `204`.

### 4.7 `POST /tasks/{submission_id}/generate_context`

Enfileira geracao de contexto (`generate_context_task`).

Efeito:

- atualiza status para `context_generation`.

Resposta `202`:

- `status: queued`
- `task: generate_context`
- `submission_id`

### 4.8 `POST /tasks/{submission_id}/generate_article`

Enfileira geracao de artigo (`generate_article_task`).

Efeito:

- atualiza status para `pending_article`.

Resposta `202`:

- `status: queued`
- `task: generate_article`
- `submission_id`

### 4.9 `POST /tasks/{submission_id}/retry`

Retry completo da submissao a partir do inicio do pipeline.

Efeito:

- seta status `pending_scrape`, limpa erros e define `current_step=retry_pending`;
- enfileira `start_pipeline`.

Resposta `202`:

- `status: queued`
- `task: retry`
- `submission_id`

### 4.10 `POST /tasks/{submission_id}/retry_step`

Retry a partir de etapa especifica, com limpeza de artefatos posteriores.

Payload:

- `stage` (obrigatorio).

Etapas aceitas (normalizadas):

- `amazon_scrape`, `pending_scrape`
- `additional_links_scrape`
- `summarize_additional_links`
- `consolidate_book_data`
- `internet_research`
- `context_generation`, `pending_context`
- `article_generation`, `pending_article`, `ready_for_review`

Efeitos:

- limpeza seletiva por etapa (summaries/kb/articles/drafts/campos extraidos);
- atualiza status coerente com etapa;
- limpa `errors`;
- enfileira task da etapa alvo.

Resposta `202`:

- `status: queued`
- `task: retry_step`
- `submission_id`
- `stage` normalizada.

### 4.11 `POST /tasks/{submission_id}/draft_article`

Salva rascunho para artigo da submissao.

Payload:

- `content` (string nao vazia).

Pre-condicoes:

- submissao existe;
- book existe;
- artigo existe para o book.

Efeito:

- cria/atualiza `articles_drafts`;
- define status do artigo como `draft`.

Resposta `200`:

- `status: saved`
- `draft_id`
- `article_id`
- `submission_id`

### 4.12 `POST /tasks/{submission_id}/publish_article`

Enfileira publicacao no WordPress (`publish_article_task`).

Pre-condicoes:

- submissao/book/artigo existem;
- se `user_approval_required=true`, status da submissao deve ser `approved` ou `ready_for_review`.

Resposta `202`:

- `status: queued`
- `celery_task_id`
- `article_id`
- `submission_id`

## 5. Endpoint de artigo

Router: `src/api/articles.py` (`/articles`).

### 5.1 `PATCH /articles/{article_id}`

Atualiza artigo por ID.

Campos permitidos:

- `title`
- `content`
- `status`
- `validation_report`
- `wordpress_post_id`
- `wordpress_url`

Comportamento:

- ignora campos nao permitidos;
- se nenhum campo valido for enviado, retorna `422`.

Resposta `200`:

- snapshot do artigo apos update (`id`, `book_id`, `submission_id`, `title`, `content`, `status`, `word_count`, `updated_at`).

## 6. Endpoints de settings

Router: `src/api/settings.py` (`/settings`).

### 6.1 Credentials

#### `GET /settings/credentials`

Lista credenciais (com mascaramento de segredo).

Filtros opcionais:

- `service`
- `active`

Resposta:

- lista de credenciais mascaradas (campo `key` reduzido).

#### `GET /settings/credentials/{cred_id}`

Detalhe de credencial mascarada.

#### `POST /settings/credentials`

Cria credencial (`CredentialCreate`).

Campos principais:

- `service`
- `key`
- `encrypted`
- `name`
- `url`
- `username_email`
- `active`

#### `PATCH /settings/credentials/{cred_id}`

Atualiza credencial (`CredentialUpdate`).

#### `DELETE /settings/credentials/{cred_id}`

Exclui credencial (`204`).

### 6.2 WordPress categories

#### `GET /settings/wordpress/categories`

Lista categorias de WordPress por credencial.

Query:

- `credential_id` (opcional).

Comportamento:

- se `credential_id` ausente, escolhe credencial WordPress ativa default;
- pagina em lotes de 100 categorias;
- tenta com auth e, para 400/401/403, tenta leitura publica sem auth;
- atualiza `last_used_at` da credencial selecionada.

Resposta:

- `credential_id`, `credential_name`, `credential_url`
- `categories` (id, name, slug)
- `count`

Erros relevantes:

- `404` sem credencial ativa;
- `422` credencial invalida/inativa/servico nao-wordpress;
- `502` erro remoto WordPress.

### 6.3 Content schemas

#### `GET /settings/content-schemas`

Lista schemas de conteudo.

Filtros:

- `active`
- `target_type`
- `search`

#### `GET /settings/content-schemas/{schema_id}`

Detalhe de schema.

#### `POST /settings/content-schemas`

Cria schema (`ContentSchemaCreate`).

#### `PATCH /settings/content-schemas/{schema_id}`

Atualiza schema (`ContentSchemaUpdate`).

Regras:

- exige pelo menos um campo no payload;
- valida coerencia `min_total_words <= max_total_words`.

#### `DELETE /settings/content-schemas/{schema_id}`

Exclui schema (`204`).

### 6.4 Pipelines

#### `GET /settings/pipelines`

Lista pipelines em formato card.

Comportamento:

- garante bootstrap de defaults antes de listar.

Resposta por item:

- `id`, `name`, `slug`, `description`, `usage_type`, `version`
- `steps_count`, `ai_steps_count`

#### `GET /settings/pipelines/{pipeline_id}`

Detalhe completo de pipeline para configuracao.

Resposta inclui:

- metadados do pipeline
- `steps` com dados de AI e delay
- `available_credentials`
- `available_prompts`

#### `PATCH /settings/pipelines/{pipeline_id}/steps/{step_id}`

Atualiza configuracao de etapa.

Payload aceito:

- `credential_id`
- `prompt_id`
- `delay_seconds`

Regras:

- pelo menos um campo entre os tres deve existir;
- `credential_id/prompt_id` apenas para step `uses_ai=true`;
- valida existencia dos IDs;
- `delay_seconds` inteiro entre `0` e `86400`.

Resposta:

- `status: ok`
- `pipeline_id`
- `step` atualizado (projecao detalhada)

### 6.5 Prompts

#### `GET /settings/prompts`

Lista prompts com filtros:

- `active`, `purpose`, `category`, `provider`, `name`, `search`.

Observacao:

- provider e inferido quando ausente, com heuristica por `model_id`.

#### `GET /settings/prompt-categories`

Lista categorias disponiveis de prompts.

Fonte:

- categoria fixa `Book Review`;
- nomes de `content_schemas`;
- categorias ja existentes em `prompts`.

#### `GET /settings/prompts/{prompt_id}`

Detalhe de prompt.

#### `POST /settings/prompts`

Cria prompt (`PromptCreate`).

Normalizacoes:

- `provider` para lowercase;
- `category` com fallback para `Book Review`.

#### `PATCH /settings/prompts/{prompt_id}`

Atualiza prompt (`PromptUpdate`).

#### `DELETE /settings/prompts/{prompt_id}`

Exclui prompt (`204`).

## 7. Codigos HTTP e erros recorrentes

Sucesso:

- `200`: leitura e update sincrono.
- `201`: criacao de recurso.
- `202`: comando assicrono enfileirado.
- `204`: exclusao sem corpo.

Erros:

- `400`: regra de negocio invalida (ex.: duplicidade submit; publish sem aprovacao).
- `404`: recurso nao encontrado.
- `422`: payload/regra de validacao invalida.
- `500`: falha interna de processamento.
- `502`: falha em dependencia externa (WordPress categories).

## 8. Side effects importantes por endpoint

- `/submit`
  - pode criar defaults de sistema e enfileirar pipeline.
- `/tasks/*retry*`
  - alteram status e podem apagar artefatos persistidos.
- `/tasks/{id}/publish_article`
  - apenas enfileira; publicacao real ocorre no worker.
- `/settings/pipelines/*`
  - altera comportamento de execucao sem deploy.
- `/settings/wordpress/categories`
  - atualiza `last_used_at` da credencial.

## 9. Referencias de implementacao

- Registro de rotas: `src/app.py`
- Submissoes: `src/api/ingest.py`
- Tasks: `src/api/tasks.py`
- Settings: `src/api/settings.py`
- Articles: `src/api/articles.py`
- Stats alias: `src/api/operations.py`
