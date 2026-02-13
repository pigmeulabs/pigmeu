# API REST

**Versão:** 0.1.0  
**Última Atualização:** 2026-02-14  
**Base URL:** `http://localhost:8000`

---

## 1. Visão Geral

A API do Pigmeu Copilot é construída com **FastAPI** e segue os padrões REST. Oferece documentação automática via Swagger UI e ReDoc.

### 1.1 URLs de Documentação

| Tipo | URL |
|------|-----|
| Swagger UI | `/docs` |
| ReDoc | `/redoc` |
| OpenAPI JSON | `/openapi.json` |

### 1.2 Formato de Resposta

**Sucesso:**

```json
{
  "id": "507f1f77bcf86cd799439011",
  "title": "Designing Data-Intensive Applications",
  "status": "pending_scrape"
}
```

**Erro:**

```json
{
  "detail": "Submission not found"
}
```

### 1.3 Códigos de Status HTTP

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 201 | Criado com sucesso |
| 202 | Aceito (processamento assíncrono) |
| 204 | Sucesso sem conteúdo (delete) |
| 400 | Requisição inválida |
| 404 | Recurso não encontrado |
| 422 | Erro de validação |
| 500 | Erro interno do servidor |

---

## 2. Endpoints

### 2.1 Health Check

#### GET /health

Verifica se a API está funcionando.

**Response:**

```json
{
  "status": "ok",
  "app": "Pigmeu Copilot API",
  "environment": "development"
}
```

---

### 2.2 Submissões (Ingest)

#### POST /submit

Submete um novo livro para processamento.

**Request Body:**

```json
{
  "title": "Designing Data-Intensive Applications",
  "author_name": "Martin Kleppmann",
  "amazon_url": "https://amazon.com/dp/1449373321",
  "goodreads_url": "https://goodreads.com/book/show/23463279",
  "author_site": "https://martin.kleppmann.com",
  "other_links": [],
  "textual_information": "Livro sobre sistemas distribuídos",
  "run_immediately": true,
  "schedule_execution": null,
  "pipeline_id": "book_review_v2",
  "main_category": "Technology",
  "content_schema_id": null,
  "article_status": null,
  "user_approval_required": false
}
```

**Campos Obrigatórios:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `title` | string | Título do livro (mín. 1 caractere) |
| `author_name` | string | Nome do autor (mín. 1 caractere) |
| `amazon_url` | string (URL) | URL do livro na Amazon |

**Campos Opcionais:**

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `goodreads_url` | URL | null | URL do Goodreads |
| `author_site` | URL | null | Site do autor |
| `other_links` | URL[] | [] | Links adicionais |
| `textual_information` | string | null | Informações extras |
| `run_immediately` | boolean | true | Iniciar processamento |
| `schedule_execution` | datetime | null | Agendar processamento |
| `pipeline_id` | string | "book_review_v2" | ID do pipeline |
| `main_category` | string | null | Categoria principal |
| `content_schema_id` | string | null | Schema de conteúdo |
| `article_status` | string | null | Status inicial do artigo |
| `user_approval_required` | boolean | false | Requer aprovação |

**Response (201):**

```json
{
  "id": "507f1f77bcf86cd799439011",
  "title": "Designing Data-Intensive Applications",
  "author_name": "Martin Kleppmann",
  "amazon_url": "https://amazon.com/dp/1449373321",
  "goodreads_url": "https://goodreads.com/book/show/23463279",
  "author_site": "https://martin.kleppmann.com",
  "other_links": [],
  "textual_information": "Livro sobre sistemas distribuídos",
  "run_immediately": true,
  "schedule_execution": null,
  "pipeline_id": "book_review_v2",
  "main_category": "Technology",
  "content_schema_id": null,
  "article_status": null,
  "user_approval_required": false,
  "status": "pending_scrape",
  "created_at": "2026-02-14T10:00:00Z",
  "updated_at": "2026-02-14T10:00:00Z"
}
```

**Erros:**

| Código | Condição |
|--------|----------|
| 400 | Livro já submetido (duplicado) |
| 422 | Dados inválidos |
| 500 | Erro interno |

---

### 2.3 Tarefas (Tasks)

#### GET /tasks

Lista todas as submissões com paginação e filtros.

**Query Parameters:**

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `skip` | int | 0 | Pular registros |
| `limit` | int | 20 | Limite de registros (1-100) |
| `status` | string | null | Filtrar por status |
| `search` | string | null | Buscar por título/autor |

**Response:**

```json
{
  "tasks": [
    {
      "id": "507f1f77bcf86cd799439011",
      "title": "Designing Data-Intensive Applications",
      "author_name": "Martin Kleppmann",
      "amazon_url": "https://amazon.com/dp/1449373321",
      "status": "ready_for_review",
      "created_at": "2026-02-14T10:00:00Z"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 20,
  "count": 1
}
```

---

#### GET /tasks/stats

Retorna estatísticas agregadas das tarefas.

**Response:**

```json
{
  "total_tasks": 42,
  "by_status": {
    "pending_scrape": 5,
    "context_generation": 2,
    "ready_for_review": 10,
    "published": 20,
    "failed": 5
  },
  "success_rate": 0.7143,
  "failed_tasks": 5
}
```

---

#### GET /tasks/{submission_id}

Retorna detalhes completos de uma tarefa.

**Response:**

```json
{
  "submission": {
    "id": "507f1f77bcf86cd799439011",
    "title": "Designing Data-Intensive Applications",
    "author_name": "Martin Kleppmann",
    "status": "ready_for_review",
    "pipeline_id": "book_review_v2"
  },
  "book": {
    "id": "507f1f77bcf86cd799439012",
    "submission_id": "507f1f77bcf86cd799439011",
    "extracted": {
      "title": "Designing Data-Intensive Applications",
      "authors": ["Martin Kleppmann"],
      "asin": "1449373321",
      "isbn_13": "9781449373327",
      "rating": 4.8
    }
  },
  "summaries": [
    {
      "id": "507f1f77bcf86cd799439013",
      "source_url": "https://goodreads.com/...",
      "summary_text": "Resumo do conteúdo...",
      "topics": ["distributed systems", "databases"]
    }
  ],
  "knowledge_base": {
    "markdown_content": "# Contexto consolidado..."
  },
  "article": {
    "id": "507f1f77bcf86cd799439014",
    "title": "Designing Data-Intensive Applications: Uma Análise Completa",
    "content": "## Introdução\n\n...",
    "word_count": 1100,
    "status": "draft"
  },
  "draft": null,
  "progress": {
    "current_stage": "ready_for_review",
    "steps": [
      {"stage": "pending_scrape", "label": "Scraping metadata...", "completed": true},
      {"stage": "pending_context", "label": "Generating context...", "completed": true},
      {"stage": "pending_article", "label": "Creating article...", "completed": true},
      {"stage": "ready_for_review", "label": "Ready for review", "completed": true}
    ]
  },
  "pipeline": {
    "id": "book_review_v2",
    "name": "Book Review",
    "steps": [...]
  }
}
```

---

#### POST /tasks/{submission_id}/generate_context

Dispara geração de contexto manualmente.

**Response (202):**

```json
{
  "status": "queued",
  "task": "generate_context",
  "submission_id": "507f1f77bcf86cd799439011"
}
```

---

#### POST /tasks/{submission_id}/generate_article

Dispara geração de artigo manualmente.

**Response (202):**

```json
{
  "status": "queued",
  "task": "generate_article",
  "submission_id": "507f1f77bcf86cd799439011"
}
```

---

#### POST /tasks/{submission_id}/retry

Reinicia o pipeline completo desde o início.

**Response (202):**

```json
{
  "status": "queued",
  "task": "retry",
  "submission_id": "507f1f77bcf86cd799439011"
}
```

---

#### POST /tasks/{submission_id}/retry_step

Reinicia a partir de um step específico.

**Request Body:**

```json
{
  "stage": "context_generation"
}
```

**Stages Válidos:**

| Stage | Descrição |
|-------|-----------|
| `amazon_scrape` | Reinicia do scraping da Amazon |
| `additional_links_scrape` | Reinicia do scraping de links |
| `summarize_additional_links` | Reinicia resumos |
| `consolidate_book_data` | Reinicia consolidação |
| `internet_research` | Reinicia pesquisa web |
| `context_generation` | Reinicia geração de contexto |
| `article_generation` | Reinicia geração de artigo |

**Response (202):**

```json
{
  "status": "queued",
  "task": "retry_step",
  "submission_id": "507f1f77bcf86cd799439011",
  "stage": "context_generation"
}
```

---

#### DELETE /tasks/{submission_id}

Remove uma submissão e todos os dados relacionados.

**Response (204):** Sem conteúdo

---

#### POST /tasks/{submission_id}/draft_article

Salva um rascunho do artigo.

**Request Body:**

```json
{
  "content": "## Título Editado\n\nConteúdo editado manualmente..."
}
```

**Response (200):**

```json
{
  "status": "saved",
  "draft_id": "507f1f77bcf86cd799439015",
  "article_id": "507f1f77bcf86cd799439014",
  "submission_id": "507f1f77bcf86cd799439011"
}
```

---

#### POST /tasks/{submission_id}/publish_article

Publica o artigo no WordPress.

**Response (202):**

```json
{
  "status": "queued",
  "celery_task_id": "abc123",
  "article_id": "507f1f77bcf86cd799439014",
  "submission_id": "507f1f77bcf86cd799439011"
}
```

**Erros:**

| Código | Condição |
|--------|----------|
| 400 | Submissão requer aprovação antes de publicar |

---

#### PATCH /tasks/{submission_id}

Atualiza dados da submissão ou livro.

**Request Body:**

```json
{
  "submission": {
    "title": "Novo Título"
  },
  "book": {
    "extracted": {
      "rating": 4.9
    }
  }
}
```

**Response (200):**

```json
{
  "submission": { ... },
  "book": { ... },
  "progress": { ... }
}
```

---

### 2.4 Settings

#### GET /settings/credentials

Lista todas as credenciais.

**Response:**

```json
[
  {
    "id": "507f1f77bcf86cd799439020",
    "service": "openai",
    "name": "OpenAI Principal",
    "active": true,
    "created_at": "2026-02-14T10:00:00Z"
  }
]
```

---

#### POST /settings/credentials

Cria uma nova credencial.

**Request Body:**

```json
{
  "service": "openai",
  "key": "sk-...",
  "encrypted": false,
  "name": "OpenAI Principal",
  "url": null,
  "username_email": null,
  "active": true
}
```

**Response (201):**

```json
{
  "id": "507f1f77bcf86cd799439020",
  "service": "openai",
  "name": "OpenAI Principal",
  "active": true
}
```

---

#### PATCH /settings/credentials/{credential_id}

Atualiza uma credencial.

**Request Body:**

```json
{
  "active": false
}
```

---

#### DELETE /settings/credentials/{credential_id}

Remove uma credencial.

**Response (204):** Sem conteúdo

---

#### GET /settings/prompts

Lista todos os prompts.

**Response:**

```json
[
  {
    "id": "507f1f77bcf86cd799439030",
    "name": "SEO-Optimized Article Writer",
    "purpose": "article",
    "category": "Book Review",
    "provider": "openai",
    "model_id": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2500,
    "active": true
  }
]
```

---

#### POST /settings/prompts

Cria um novo prompt.

**Request Body:**

```json
{
  "name": "Meu Prompt Customizado",
  "purpose": "custom_purpose",
  "category": "Custom",
  "provider": "groq",
  "short_description": "Descrição do prompt",
  "system_prompt": "Você é um assistente...",
  "user_prompt": "Task: {{task}}\n\nContexto: {{context}}",
  "model_id": "llama-3.3-70b-versatile",
  "temperature": 0.5,
  "max_tokens": 2000,
  "expected_output_format": "{ \"result\": \"string\" }",
  "active": true
}
```

---

#### PATCH /settings/prompts/{prompt_id}

Atualiza um prompt.

---

#### DELETE /settings/prompts/{prompt_id}

Remove um prompt.

---

#### GET /settings/prompt-categories

Lista categorias de prompts.

**Response:**

```json
["Book Review", "Social Media", "SEO Tools", "Custom"]
```

---

#### GET /settings/content-schemas

Lista schemas de conteúdo.

**Response:**

```json
[
  {
    "id": "507f1f77bcf86cd799439040",
    "name": "Default Book Review",
    "target_type": "book_review",
    "min_total_words": 800,
    "max_total_words": 1333,
    "toc_template": [...],
    "active": true
  }
]
```

---

#### POST /settings/content-schemas

Cria um novo schema de conteúdo.

**Request Body:**

```json
{
  "name": "Extended Book Review",
  "target_type": "book_review",
  "description": "Schema para artigos mais longos",
  "min_total_words": 1500,
  "max_total_words": 2000,
  "toc_template": [
    {
      "heading": "Introdução",
      "type": "h2",
      "min_words": 100
    }
  ],
  "internal_links_count": 3,
  "external_links_count": 5,
  "active": true
}
```

---

#### GET /settings/pipelines

Lista configurações de pipelines.

**Response:**

```json
[
  {
    "id": "507f1f77bcf86cd799439050",
    "pipeline_id": "book_review_v2",
    "name": "Book Review",
    "slug": "book-review",
    "version": "2.0",
    "steps": [...]
  }
]
```

---

#### PATCH /settings/pipelines/{pipeline_id}

Atualiza configuração de um pipeline.

---

#### GET /settings/wordpress/categories

Lista categorias do WordPress.

**Response:**

```json
[
  {
    "id": 1,
    "name": "Uncategorized",
    "slug": "uncategorized"
  },
  {
    "id": 15,
    "name": "Technology",
    "slug": "technology"
  }
]
```

---

### 2.5 Artigos

#### GET /articles

Lista artigos.

**Query Parameters:**

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `skip` | int | 0 | Pular registros |
| `limit` | int | 20 | Limite de registros |
| `status` | string | null | Filtrar por status |

---

#### GET /articles/{article_id}

Retorna detalhes de um artigo.

---

#### POST /articles/{article_id}/approve

Aprova um artigo para publicação.

**Response (200):**

```json
{
  "status": "approved",
  "article_id": "507f1f77bcf86cd799439014",
  "approved_at": "2026-02-14T12:00:00Z"
}
```

---

#### POST /articles/{article_id}/reject

Rejeita um artigo.

**Request Body:**

```json
{
  "feedback": "Artigo precisa de revisão nos tópicos técnicos"
}
```

---

### 2.6 UI

#### GET /ui

Serve a interface web (SPA).

---

## 3. Exemplos de Uso

### 3.1 Submeter e Processar um Livro

```bash
# 1. Submeter livro
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Clean Code",
    "author_name": "Robert C. Martin",
    "amazon_url": "https://amazon.com/dp/0132350882"
  }'

# Response: { "id": "abc123", "status": "pending_scrape", ... }

# 2. Verificar status
curl http://localhost:8000/tasks/abc123

# 3. Quando ready_for_review, ver artigo
curl http://localhost:8000/tasks/abc123 | jq '.article'

# 4. Publicar
curl -X POST http://localhost:8000/tasks/abc123/publish_article
```

### 3.2 Listar Tarefas Prontas para Revisão

```bash
curl "http://localhost:8000/tasks?status=ready_for_review"
```

### 3.3 Retentar Tarefa Falhada

```bash
# Reiniciar do step específico
curl -X POST http://localhost:8000/tasks/abc123/retry_step \
  -H "Content-Type: application/json" \
  -d '{"stage": "context_generation"}'
```

### 3.4 Gerenciar Credenciais

```bash
# Listar
curl http://localhost:8000/settings/credentials

# Criar
curl -X POST http://localhost:8000/settings/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "service": "openai",
    "key": "sk-your-key",
    "name": "OpenAI Principal",
    "active": true
  }'

# Desativar
curl -X PATCH http://localhost:8000/settings/credentials/cred123 \
  -H "Content-Type: application/json" \
  -d '{"active": false}'
```

---

## 4. Autenticação

Atualmente a API não possui autenticação implementada. Em ambiente de produção, recomenda-se adicionar:

- API Key via header `X-API-Key`
- JWT Bearer Token
- OAuth2

---

## 5. Rate Limiting

A API não possui rate limiting próprio. No entanto, os scrapers respeitam limites das fontes externas.

---

## Próximos Passos

- [Workers e Pipelines](./05-workers-pipelines.md)
- [Scrapers e Integrações](./06-scrapers-integracoes.md)
