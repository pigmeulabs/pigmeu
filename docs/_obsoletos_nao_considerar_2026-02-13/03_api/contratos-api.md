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

Query params:
- `service` (string)
- `active` (bool)

### `GET /settings/credentials/{cred_id}`
Retorna detalhe mascarado.

### `POST /settings/credentials`
Cria credencial.

Request:
```json
{
  "service": "openai",
  "name": "OpenAI Primary",
  "key": "sk-...",
  "username_email": "optional",
  "encrypted": true,
  "active": true
}
```

### `PATCH /settings/credentials/{cred_id}`
Atualiza `key`, `name`, `username_email`, `active`.

### `DELETE /settings/credentials/{cred_id}`
Exclui credencial.

## Settings - Prompts

### `GET /settings/prompts`
Lista prompts.

Query params:
- `active` (bool)
- `purpose` (string)
- `search` (string)
- `provider` (string, opcional)

### `GET /settings/prompts/{prompt_id}`
Detalhe de prompt.

### `POST /settings/prompts`
Cria prompt.

Request:
```json
{
  "name": "Book Review Generator",
  "short_description": "Gera artigo de review",
  "purpose": "article",
  "provider": "openai",
  "credential_id": "<credential_id>",
  "model_id": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 2000,
  "system_prompt": "...",
  "user_prompt": "...",
  "active": true
}
```

### `PATCH /settings/prompts/{prompt_id}`
Atualiza campos do prompt.

### `DELETE /settings/prompts/{prompt_id}`
Exclui prompt.

## Endpoints auxiliares para UI de Prompt

### `GET /settings/providers`
Lista provedores disponíveis para seleção em UI.

Response exemplo:
```json
{
  "providers": ["openai", "groq", "mistral", "claude"]
}
```

### `GET /settings/providers/{provider}/models`
Lista modelos disponíveis para o `provider` selecionado.

Response exemplo:
```json
{
  "provider": "openai",
  "models": ["gpt-4o", "gpt-4o-mini"]
}
```

### `GET /settings/credentials?service={provider}&active=true`
Lista credenciais ativas para preencher o seletor `Credential` no modal de prompt.
