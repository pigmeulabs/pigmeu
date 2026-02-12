# Contratos de API

Base local: `http://localhost:8000`

## Convenções
- Formato: JSON.
- Autenticação: não implementada.
- IDs: `ObjectId` serializado em string.

## Endpoints de sistema

### `GET /health`
- Retorna status da API.

### `GET /`
- Retorna metadados de entrada (docs/openapi).

### `GET /ui`
- Retorna dashboard web.

### `GET /stats`
- Alias operacional para métricas agregadas de submissions.

## Submissions

### `POST /submit`
Cria submission.

Request:
```json
{
  "title": "string",
  "author_name": "string",
  "amazon_url": "https://...",
  "goodreads_url": "https://...",
  "author_site": "https://...",
  "other_links": ["https://..."],
  "textual_information": "string",
  "run_immediately": true,
  "schedule_execution": "2026-02-12T18:00:00Z",
  "main_category": "Technology",
  "article_status": "draft",
  "user_approval_required": false
}
```

Response `201`:
```json
{
  "id": "...",
  "status": "pending_scrape",
  "created_at": "...",
  "updated_at": "..."
}
```

### `GET /submit/health`
Health do módulo de ingestão.

## Tasks

### `GET /tasks/health`
Health do módulo tasks.

### `GET /tasks/stats`
Métricas agregadas de submissions.

### `GET /tasks`
Lista paginada.

Query params:
- `skip` (int)
- `limit` (int)
- `status` (string)
- `search` (string)

### `GET /tasks/{submission_id}`
Retorna submission + book + knowledge_base + article + draft + progresso.

### `PATCH /tasks/{submission_id}`
Atualiza dados de submission e/ou `book.extracted`.

Body:
```json
{
  "submission": {"title": "Novo"},
  "book": {"extracted": {"theme": "..."}}
}
```

### `POST /tasks/{submission_id}/generate_context`
Enfileira geração de contexto.

### `POST /tasks/{submission_id}/generate_article`
Enfileira geração de artigo.

### `POST /tasks/{submission_id}/retry`
Reseta para `pending_scrape` e reenfileira pipeline.

### `POST /tasks/{submission_id}/draft_article`
Salva draft de artigo.

Body:
```json
{"content": "# Draft ..."}
```

### `POST /tasks/{submission_id}/publish_article`
Enfileira publicação WordPress.

## Artigos

### `PATCH /articles/{article_id}`
Atualiza campos permitidos do artigo.

Campos aceitos:
- `title`
- `content`
- `status`
- `validation_report`
- `wordpress_post_id`
- `wordpress_url`

## Settings - Credentials

### `GET /settings/credentials`
Lista credenciais com máscara de chave.

Filtros:
- `service`
- `active`

### `GET /settings/credentials/{cred_id}`
Retorna detalhe mascarado.

### `POST /settings/credentials`
Cria credencial.

### `PATCH /settings/credentials/{cred_id}`
Atualiza `key`, `name`, `username_email`, `active`.

### `DELETE /settings/credentials/{cred_id}`
Exclui credencial.

## Settings - Prompts

### `GET /settings/prompts`
Lista prompts.

Filtros:
- `active`
- `purpose`
- `search`

### `GET /settings/prompts/{prompt_id}`
Detalhe de prompt.

### `POST /settings/prompts`
Cria prompt.

### `PATCH /settings/prompts/{prompt_id}`
Atualiza campos do prompt.

### `DELETE /settings/prompts/{prompt_id}`
Exclui prompt.
