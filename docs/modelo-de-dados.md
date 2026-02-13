# Modelo de Dados

Atualizado em: 2026-02-13
Banco: MongoDB
Camada de acesso: `src/db/repositories.py`

## 1. Visao geral

O sistema utiliza modelagem orientada a documentos para armazenar:

- comando inicial de trabalho (`submissions`);
- artefatos produzidos em cada etapa (`books`, `summaries`, `knowledge_base`, `articles`, `articles_drafts`);
- configuracoes operacionais (`credentials`, `prompts`, `content_schemas`, `pipeline_configs`).

## 2. Colecoes ativas

- `submissions`
- `books`
- `summaries`
- `knowledge_base`
- `articles`
- `articles_drafts`
- `credentials`
- `prompts`
- `content_schemas`
- `pipeline_configs` (gerenciada por repository; sem indice explicitamente criado em migracao atual)

## 3. Entidades e campos

## 3.1 `submissions`

Origem principal:

- criada em `SubmissionRepository.create`.

Campos tipicos:

- `_id`: ObjectId
- `title`: string
- `author_name`: string
- `amazon_url`: string
- `goodreads_url`: string|null
- `author_site`: string|null
- `other_links`: string[]
- `textual_information`: string|null
- `run_immediately`: bool
- `schedule_execution`: datetime|null
- `pipeline_id`: string (default `book_review_v2`)
- `main_category`: string|null
- `content_schema_id`: string|null
- `article_status`: string|null
- `user_approval_required`: bool
- `status`: string (`SubmissionStatus`)
- `current_step`: string
- `attempts`: objeto (mapa de tentativas)
- `errors`: array
- `created_at`: datetime UTC
- `updated_at`: datetime UTC

Campos adicionais dinamicos por fluxo:

- `book_id`
- `article_id`
- `links_total`
- `links_processed`
- `started_at`
- `pipeline_version`
- `published_url`

## 3.2 `books`

Origem principal:

- `BookRepository.create_or_update`.

Campos:

- `_id`: ObjectId
- `submission_id`: ObjectId (1:1 com submissao)
- `extracted`: objeto com metadados e enriquecimentos de etapas
- `last_updated`: datetime UTC

Estruturas relevantes em `extracted`:

- dados Amazon (titulo, autores, isbn, paginas, preco, rating, etc.)
- `link_bibliographic_candidates`: array
- `additional_links_total`, `additional_links_processed`, `additional_links_processed_at`
- `consolidated_bibliographic`
- `consolidated_sources_count`, `consolidated_at`
- `web_research`:
  - `research_markdown`
  - `topics`
  - `key_insights`
  - `sources`
  - `generated_at`

## 3.3 `summaries`

Origem:

- `SummaryRepository.create` (links adicionais e link worker).

Campos:

- `_id`: ObjectId
- `book_id`: ObjectId
- `source_url`: string
- `source_domain`: string|null
- `summary_text`: string
- `topics`: string[]
- `key_points`: string[]
- `credibility`: string|null
- `created_at`: datetime UTC

Campos extras frequentes:

- `pipeline_stage`
- `bibliographic_data`
- `content_excerpt`

## 3.4 `knowledge_base`

Origem:

- `KnowledgeBaseRepository.create_or_update`.

Campos:

- `_id`: ObjectId
- `book_id`: ObjectId|null
- `submission_id`: ObjectId|null
- `markdown_content`: string
- `topics_index`: string[]
- `created_at`: datetime UTC
- `updated_at`: datetime UTC

Selecao de update:

- prioriza `book_id` quando presente;
- fallback por `submission_id` quando nao ha `book_id`.

## 3.5 `articles`

Origem:

- `ArticleRepository.create`
- update por API (`/articles/{id}`)
- update de publicacao (`publish_article_task`).

Campos:

- `_id`: ObjectId
- `book_id`: ObjectId
- `submission_id`: ObjectId|null
- `title`: string
- `content`: string (markdown)
- `word_count`: int
- `status`: string (`draft`, `in_review`, `approved`, `published`, etc.)
- `validation_report`: objeto
- `topics_used`: array
- `wordpress_post_id`: string|null
- `wordpress_url`: string|null
- `published_at`: datetime|null
- `wordpress_categories`: int[] (quando publicado)
- `wordpress_tags`: int[] (quando publicado)
- `meta_description`: string|null
- `created_at`: datetime UTC
- `updated_at`: datetime UTC

## 3.6 `articles_drafts`

Origem:

- `ArticleRepository.save_draft`.

Campos:

- `_id`: ObjectId
- `article_id`: ObjectId (indice unico)
- `content`: string
- `created_at`: datetime UTC
- `updated_at`: datetime UTC

## 3.7 `credentials`

Origem:

- CRUD via `/settings/credentials`.
- bootstrap automatico de defaults.

Campos:

- `_id`: ObjectId
- `service`: string (`openai`, `groq`, `mistral`, `claude`, `wordpress`, ...)
- `name`: string
- `url`: string|null
- `key`: string
- `encrypted`: bool
- `username_email`: string|null
- `active`: bool
- `created_at`: datetime UTC
- `updated_at`: datetime UTC
- `last_used_at`: datetime|null

## 3.8 `prompts`

Origem:

- CRUD via `/settings/prompts`.
- auto-criacao de prompts auxiliares em workers, quando ausentes.

Campos:

- `_id`: ObjectId
- `name`: string (unico)
- `purpose`: string
- `category`: string
- `provider`: string
- `short_description`: string|null
- `system_prompt`: string
- `user_prompt`: string
- `expected_output_format`: string|null
- `schema_example`: string|null
- `model_id`: string
- `temperature`: float
- `max_tokens`: int
- `active`: bool
- `version`: int
- `created_at`: datetime UTC
- `updated_at`: datetime UTC

## 3.9 `content_schemas`

Origem:

- CRUD via `/settings/content-schemas`.
- bootstrap de schema default.

Campos:

- `_id`: ObjectId
- `name`: string (unico)
- `target_type`: string (ex.: `book_review`)
- `description`: string|null
- `min_total_words`: int|null
- `max_total_words`: int|null
- `toc_template`: array de itens
- `internal_links_count`: int
- `external_links_count`: int
- `active`: bool
- `created_at`: datetime UTC
- `updated_at`: datetime UTC

Estrutura de item em `toc_template`:

- `level`: `h2`|`h3`
- `title_template`: string
- `content_mode`: `specific`|`dynamic`
- `specific_content_hint`: string|null
- `min_paragraphs`, `max_paragraphs`: int|null
- `min_words`, `max_words`: int|null
- `source_fields`: string[]
- `prompt_id`: string|null
- `position`: int

## 3.10 `pipeline_configs`

Origem:

- `PipelineConfigRepository.create_or_update` (bootstrap e updates de settings).

Campos principais:

- `_id`: ObjectId
- `pipeline_id`: string
- `name`, `slug`, `description`, `usage_type`, `version`
- `steps`: array
- `created_at`: datetime UTC
- `updated_at`: datetime UTC

Estrutura de step:

- `id`, `name`, `description`, `type`
- `uses_ai`: bool
- `delay_seconds`: int
- `ai` (quando aplicavel):
  - `provider`
  - `model_id`
  - `credential_id`
  - `prompt_id`
  - `default_credential_name`
  - `default_prompt_purpose`

## 4. Relacionamentos logicos

- `submissions (1) -> (1) books` por `books.submission_id` unico.
- `books (1) -> (N) summaries` por `summaries.book_id`.
- `books (1) -> (0..1) knowledge_base` (pratica de upsert por book).
- `books (1) -> (N) articles` (historico de geracoes).
- `articles (1) -> (0..1) articles_drafts` por `article_id` unico.
- `submissions (1) -> (N) articles` via `submission_id`.

## 5. Indices e migracoes

Definidos em `src/db/migrations.py`.

### 5.1 `submissions`

- `(status ASC, created_at DESC)`
- `(pipeline_id ASC, created_at DESC)`
- text index em `(title, author_name)`
- unico em `amazon_url`

### 5.2 `books`

- unico em `submission_id`
- unico sparse em `extracted.isbn`

### 5.3 `summaries`

- `(book_id ASC, created_at DESC)`
- `source_domain`

### 5.4 `knowledge_base`

- `book_id` sparse
- `submission_id` sparse

### 5.5 `articles`

- `(book_id ASC, created_at DESC)`
- `(submission_id ASC, created_at DESC)` sparse
- `wordpress_post_id` sparse

### 5.6 `articles_drafts`

- unico em `article_id`

### 5.7 `credentials`

- `(service, active)`
- `name`
- `(service, url)` sparse

### 5.8 `prompts`

- unico em `name`
- `(purpose, active)`
- `(category, active)`
- `(provider, active)`
- `model_id`

### 5.9 `content_schemas`

- unico em `name`
- `(target_type, active)`
- `updated_at DESC`

Observacao:

- `pipeline_configs` nao recebe indice explicito em `run_migrations`; colecao e criada sob demanda pelo repository.

## 6. Regras de consistencia aplicadas no codigo

- submissao duplicada por `amazon_url` bloqueada na API e reforcada por indice unico.
- updates de repository sempre aplicam `updated_at`.
- retry por etapa remove artefatos posteriores para evitar incoerencia de cadeia.
- `ArticleRepository.get_by_book` retorna o mais recente por `created_at DESC`.
- `PromptRepository.list_all` aplica normalizacao/fallback de provider por modelo quando necessario.

## 7. Limpeza de dados por retry de etapa

Implementado em `_cleanup_from_stage` (`src/api/tasks.py`).

- `amazon_scrape`
  - remove book + summaries + knowledge_base + articles + drafts.
- `additional_links_scrape` e `summarize_additional_links`
  - remove summaries/kb/articles/drafts e limpa campos de links/consolidacao/web_research em `books.extracted`.
- `consolidate_book_data`
  - remove kb/articles/drafts e limpa campos de consolidacao/web_research.
- `internet_research`
  - remove kb/articles/drafts e limpa `web_research`.
- `context_generation`
  - remove kb/articles/drafts.
- `article_generation`
  - remove articles/drafts.

## 8. Serializacao para API

A camada API usa sanitizacao recursiva (`_sanitize_for_response`) para converter tipos nao JSON (principalmente ObjectId) em string.

## 9. Consideracoes operacionais

- a conexao Motor e recriada quando o event loop muda (`src/db/connection.py`), prevenindo erros em workers Celery baseados em `asyncio.run()`.
- dados de configuracao (prompts, credentials, pipelines) influenciam diretamente o comportamento do runtime sem redeploy.
