# Modelo de Dados

**Versão:** 0.1.0  
**Última Atualização:** 2026-02-14

---

## 1. Visão Geral

O Pigmeu Copilot utiliza **MongoDB** como banco de dados principal. O modelo de dados é orientado a documentos, com coleções que representam as entidades do sistema e seus relacionamentos.

### 1.1 Diagrama Entidade-Relacionamento

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  submissions    │       │     books       │       │    articles     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ _id (ObjectId)  │───┐   │ _id (ObjectId)  │───┐   │ _id (ObjectId)  │
│ title           │   │   │ submission_id   │◄──┘   │ book_id         │◄──┐
│ author_name     │   │   │ extracted       │       │ submission_id   │   │
│ amazon_url      │   │   │ last_updated    │       │ title           │   │
│ status          │   │   └─────────────────┘       │ content         │   │
│ pipeline_id     │   │                             │ word_count      │   │
│ ...             │   │                             │ status          │   │
└─────────────────┘   │                             │ wordpress_url   │   │
                      │                             └─────────────────┘   │
                      │                                                   │
                      │   ┌─────────────────┐       ┌─────────────────┐   │
                      │   │   summaries     │       │ knowledge_base  │   │
                      │   ├─────────────────┤       ├─────────────────┤   │
                      │   │ _id (ObjectId)  │       │ _id (ObjectId)  │   │
                      └──►│ book_id         │       │ book_id         │◄──┘
                          │ source_url      │       │ submission_id   │
                          │ summary_text    │       │ markdown_content│
                          │ topics          │       │ topics_index    │
                          └─────────────────┘       └─────────────────┘

┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  credentials    │   │    prompts      │   │ content_schemas │
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ _id (ObjectId)  │   │ _id (ObjectId)  │   │ _id (ObjectId)  │
│ service         │   │ name            │   │ name            │
│ name            │   │ purpose         │   │ target_type     │
│ key             │   │ provider        │   │ toc_template    │
│ active          │   │ system_prompt   │   │ min_total_words │
└─────────────────┘   │ user_prompt     │   │ max_total_words │
                      └─────────────────┘   └─────────────────┘

┌─────────────────┐   ┌─────────────────┐
│pipeline_configs │   │ articles_drafts │
├─────────────────┤   ├─────────────────┤
│ _id (ObjectId)  │   │ _id (ObjectId)  │
│ pipeline_id     │   │ article_id      │
│ name            │   │ content         │
│ slug            │   │ created_at      │
│ steps[]         │   │ updated_at      │
└─────────────────┘   └─────────────────┘
```

---

## 2. Coleções

### 2.1 submissions

Armazena as submissões de livros para processamento.

**Schema:**

```javascript
{
  "_id": ObjectId,
  "title": String,                    // Título do livro (obrigatório)
  "author_name": String,              // Nome do autor (obrigatório)
  "amazon_url": String,               // URL da Amazon (obrigatório)
  "goodreads_url": String | null,     // URL do Goodreads (opcional)
  "author_site": String | null,       // Site do autor (opcional)
  "other_links": [String],            // Links adicionais
  "textual_information": String | null, // Informações textuais extras
  "run_immediately": Boolean,         // Iniciar processamento imediatamente
  "schedule_execution": Date | null,  // Agendamento
  "pipeline_id": String,              // ID do pipeline (default: "book_review_v2")
  "main_category": String | null,     // Categoria principal
  "content_schema_id": String | null, // Schema de conteúdo
  "article_status": String | null,    // Status inicial do artigo
  "user_approval_required": Boolean,  // Requer aprovação antes de publicar
  "article_id": ObjectId | null,      // Referência ao artigo gerado
  "status": String,                   // Status atual (enum SubmissionStatus)
  "current_step": String,             // Step atual do pipeline
  "attempts": {                       // Contador de tentativas por step
    "amazon_scrape": Number,
    "context_generation": Number,
    // ...
  },
  "errors": [                         // Histórico de erros
    {
      "step": String,
      "message": String,
      "timestamp": Date
    }
  ],
  "created_at": Date,
  "updated_at": Date
}
```

**Índices:**

```javascript
{ "amazon_url": 1 }                   // Verificação de duplicados
{ "status": 1 }                       // Filtro por status
{ "created_at": -1 }                  // Ordenação por data
```

**Enum de Status (SubmissionStatus):**

| Valor | Descrição |
|-------|-----------|
| `pending_scrape` | Aguardando scraping |
| `scraping_amazon` | Scraping Amazon em andamento |
| `scraping_goodreads` | Scraping Goodreads em andamento |
| `scraped` | Scraping concluído |
| `pending_context` | Aguardando geração de contexto |
| `context_generation` | Gerando contexto |
| `context_generated` | Contexto gerado |
| `pending_article` | Aguardando geração de artigo |
| `article_generated` | Artigo gerado |
| `ready_for_review` | Pronto para revisão |
| `approved` | Aprovado |
| `published` | Publicado |
| `scraping_failed` | Falha no scraping |
| `failed` | Falha genérica |

---

### 2.2 books

Armazena os dados extraídos dos livros.

**Schema:**

```javascript
{
  "_id": ObjectId,
  "submission_id": ObjectId,          // Referência à submissão
  "extracted": {                      // Dados extraídos de todas as fontes
    // Dados da Amazon
    "title": String,
    "authors": [String],
    "asin": String,
    "isbn_10": String,
    "isbn_13": String,
    "price_book": Number,
    "price_ebook": Number,
    "rating": Number,
    "rating_count": Number,
    "pages": Number,
    "language": String,
    "publisher": String,
    "publication_date": String,
    "cover_image_url": String,
    "description": String,
    
    // Dados do Goodreads
    "goodreads_rating": Number,
    "goodreads_rating_count": Number,
    "goodreads_genres": [String],
    
    // Dados de links adicionais
    "link_bibliographic_candidates": [
      {
        "url": String,
        "bibliographic_data": Object
      }
    ],
    "additional_links_total": Number,
    "additional_links_processed": Number,
    "additional_links_processed_at": Date,
    
    // Dados consolidados
    "consolidated_bibliographic": Object,
    "consolidated_sources_count": Number,
    "consolidated_at": Date,
    
    // Pesquisa web
    "web_research": {
      "topics": [String],
      "themes": [String],
      "target_audience": String,
      "researched_at": Date
    }
  },
  "last_updated": Date
}
```

**Índices:**

```javascript
{ "submission_id": 1 }                // Busca por submissão
```

---

### 2.3 summaries

Armazena resumos de links adicionais processados.

**Schema:**

```javascript
{
  "_id": ObjectId,
  "book_id": ObjectId,                // Referência ao livro
  "source_url": String,               // URL da fonte
  "source_domain": String,            // Domínio extraído
  "summary_text": String,             // Texto do resumo
  "topics": [String],                 // Tópicos identificados
  "key_points": [String],             // Pontos-chave
  "credibility": String,              // "alta" | "media" | "baixa"
  "bibliographic_data": Object | null, // Dados bibliográficos extraídos
  "created_at": Date
}
```

**Índices:**

```javascript
{ "book_id": 1 }                      // Busca por livro
```

---

### 2.4 knowledge_base

Armazena a base de conhecimento consolidada para geração de artigos.

**Schema:**

```javascript
{
  "_id": ObjectId,
  "book_id": ObjectId | null,         // Referência ao livro
  "submission_id": ObjectId | null,   // Referência à submissão (alternativa)
  "markdown_content": String,         // Conteúdo em Markdown
  "topics_index": [String],           // Índice de tópicos
  "created_at": Date,
  "updated_at": Date
}
```

**Índices:**

```javascript
{ "book_id": 1 },
{ "submission_id": 1 }
```

---

### 2.5 articles

Armazena os artigos gerados.

**Schema:**

```javascript
{
  "_id": ObjectId,
  "book_id": ObjectId,                // Referência ao livro
  "submission_id": ObjectId | null,   // Referência à submissão
  "title": String,                    // Título do artigo
  "content": String,                  // Conteúdo em Markdown
  "word_count": Number,               // Contagem de palavras
  "status": String,                   // Status (enum ArticleStatus)
  "wordpress_post_id": String | null, // ID do post no WordPress
  "wordpress_url": String | null,     // URL do post publicado
  "validation_report": Object | null, // Relatório de validação
  "topics_used": [Object],            // Tópicos utilizados
  "approved_at": Date | null,
  "rejection_feedback": String | null,
  "rejection_timestamp": Date | null,
  "published_at": Date | null,
  "created_at": Date,
  "updated_at": Date
}
```

**Índices:**

```javascript
{ "book_id": 1 },
{ "submission_id": 1 },
{ "status": 1 }
```

**Enum de Status (ArticleStatus):**

| Valor | Descrição |
|-------|-----------|
| `draft` | Rascunho |
| `in_review` | Em revisão |
| `approved` | Aprovado |
| `published` | Publicado |
| `archived` | Arquivado |

---

### 2.6 articles_drafts

Armazena rascunhos de artigos editados manualmente.

**Schema:**

```javascript
{
  "_id": ObjectId,
  "article_id": ObjectId,             // Referência ao artigo
  "content": String,                  // Conteúdo do rascunho
  "created_at": Date,
  "updated_at": Date
}
```

**Índices:**

```javascript
{ "article_id": 1 }
```

---

### 2.7 credentials

Armazena credenciais de serviços externos.

**Schema:**

```javascript
{
  "_id": ObjectId,
  "service": String,                  // Tipo de serviço (enum ServiceType)
  "name": String,                     // Nome amigável
  "key": String,                      // API key ou senha
  "encrypted": Boolean,               // Se já está criptografada
  "url": String | null,               // URL do serviço (WordPress)
  "username_email": String | null,    // Username ou email
  "active": Boolean,                  // Credencial ativa
  "last_used_at": Date | null,
  "created_at": Date,
  "updated_at": Date
}
```

**Índices:**

```javascript
{ "service": 1, "active": 1 },
{ "name": 1, "active": 1 }
```

**Enum de Serviços (ServiceType):**

| Valor | Descrição |
|-------|-----------|
| `openai` | OpenAI API |
| `groq` | Groq API |
| `mistral` | Mistral API |
| `claude` | Claude/Anthropic API |
| `wordpress` | WordPress |
| `amazon_pa_api` | Amazon Product Advertising API |

---

### 2.8 prompts

Armazena templates de prompts para LLM.

**Schema:**

```javascript
{
  "_id": ObjectId,
  "name": String,                     // Nome do prompt
  "purpose": String,                  // Identificador de propósito
  "category": String,                 // Categoria (ex: "Book Review")
  "provider": String | null,          // Provedor preferido
  "short_description": String | null, // Descrição curta
  "system_prompt": String | null,     // Prompt de sistema
  "user_prompt": String | null,       // Template de prompt do usuário
  "model_id": String | null,          // ID do modelo
  "temperature": Number,              // Temperatura (0.0-2.0)
  "max_tokens": Number,               // Máximo de tokens
  "expected_output_format": String | null, // Formato esperado
  "schema_example": String | null,    // Exemplo de schema
  "active": Boolean,
  "created_at": Date,
  "updated_at": Date
}
```

**Índices:**

```javascript
{ "purpose": 1, "active": 1 },
{ "name": 1 }
```

**Purposes Comuns:**

| Purpose | Uso |
|---------|-----|
| `context` | Geração de contexto |
| `article` | Geração de artigo |
| `book_review_link_bibliography_extract` | Extração bibliográfica |
| `book_review_link_summary` | Resumo de links |
| `book_review_web_research` | Pesquisa web |
| `topic_extraction` | Extração de tópicos |

---

### 2.9 content_schemas

Armazena schemas de estrutura de conteúdo.

**Schema:**

```javascript
{
  "_id": ObjectId,
  "name": String,                     // Nome do schema
  "target_type": String,              // Tipo alvo (ex: "book_review")
  "description": String | null,       // Descrição
  "min_total_words": Number | null,   // Mínimo de palavras
  "max_total_words": Number | null,   // Máximo de palavras
  "toc_template": [                   // Template de sumário
    {
      "heading": String,
      "type": String,                 // "h2" | "h3"
      "min_words": Number,
      "subsections": [Object]
    }
  ],
  "internal_links_count": Number,     // Links internos
  "external_links_count": Number,     // Links externos
  "active": Boolean,
  "created_at": Date,
  "updated_at": Date
}
```

---

### 2.10 pipeline_configs

Armazena configurações de pipelines de processamento.

**Schema:**

```javascript
{
  "_id": ObjectId,
  "pipeline_id": String,              // ID único do pipeline
  "name": String,                     // Nome legível
  "slug": String,                     // Slug para URL
  "description": String | null,       // Descrição
  "usage_type": String,               // Tipo de uso
  "version": String,                  // Versão
  "steps": [                          // Lista de steps
    {
      "id": String,                   // ID do step
      "name": String,                 // Nome
      "description": String,          // Descrição
      "type": String,                 // "scraping" | "llm" | "data-processing"
      "uses_ai": Boolean,             // Usa IA
      "delay_seconds": Number,        // Delay antes de executar
      "ai": {                         // Config de IA (se uses_ai=true)
        "provider": String,
        "model_id": String,
        "credential_id": ObjectId | null,
        "prompt_id": ObjectId | null,
        "default_credential_name": String,
        "default_prompt_purpose": String
      }
    }
  ],
  "created_at": Date,
  "updated_at": Date
}
```

**Pipeline Padrão (book_review_v2):**

| Step | Tipo | Usa IA | Descrição |
|------|------|--------|-----------|
| `amazon_scrape` | scraping | Não | Extrai metadados da Amazon |
| `additional_links_scrape` | scraping+llm | Sim | Processa links adicionais |
| `summarize_additional_links` | llm | Sim | Resume links |
| `consolidate_book_data` | data-processing | Não | Consolida dados |
| `internet_research` | search+llm | Sim | Pesquisa web |
| `context_generation` | llm | Sim | Gera contexto |
| `article_generation` | llm | Sim | Gera artigo |

---

## 3. Relacionamentos

### 3.1 Diagrama de Relacionamentos

```
submissions (1) ────────────► books (1)
    │                            │
    │                            ├──► summaries (N)
    │                            │
    │                            ├──► knowledge_base (1)
    │                            │
    │                            └──► articles (1)
    │                                      │
    │                                      └──► articles_drafts (1)
    │
    └──► pipeline_configs (N:1, por pipeline_id)
    
credentials (N) ────────────► pipeline_configs (via steps.ai.credential_id)
prompts (N) ─────────────────► pipeline_configs (via steps.ai.prompt_id)
content_schemas (N) ─────────► submissions (via content_schema_id)
```

### 3.2 Regras de Integridade

| Relacionamento | Regra |
|----------------|-------|
| submission → book | Um livro pertence a uma submissão |
| book → summaries | Múltiplos resumos por livro |
| book → knowledge_base | Uma base de conhecimento por livro |
| book → article | Um artigo principal por livro |
| article → draft | Um rascunho por artigo |

---

## 4. Migrações

### 4.1 Sistema de Migrações

**Arquivo:** [`src/db/migrations.py`](../../src/db/migrations.py)

```python
async def run_migrations():
    """Executa migrações pendentes."""
    # Cria índices
    # Atualiza schemas
    # Popula dados iniciais
```

### 4.2 Migrações Executadas

1. Criação de índices básicos
2. População de pipeline padrão
3. Criação de prompts padrão
4. Criação de schemas de conteúdo padrão

---

## 5. Consultas Comuns

### 5.1 Buscar Submissão com Dados Relacionados

```python
submission = await submission_repo.get_by_id(submission_id)
book = await book_repo.get_by_submission(submission_id)
summaries = await summary_repo.get_by_book(str(book["_id"]))
kb = await kb_repo.get_by_book(str(book["_id"]))
article = await article_repo.get_by_book(str(book["_id"]))
```

### 5.2 Listar Tarefas por Status

```python
submissions, total = await submission_repo.list_all(
    skip=0,
    limit=20,
    status="ready_for_review"
)
```

### 5.3 Verificar Duplicados

```python
existing_id = await submission_repo.check_duplicate(amazon_url)
```

### 5.4 Estatísticas de Tarefas

```python
stats = await submission_repo.stats()
# Retorna: { total_tasks, by_status, success_rate, failed_tasks }
```

---

## 6. Backup e Restore

### 6.1 Backup

```bash
# MongoDB dump
mongodump --uri="$MONGODB_URI" --out=./backups/backup_$(date +%Y%m%d)

# Backup de coleções específicas
mongodump --uri="$MONGODB_URI" --collection=submissions --db=pigmeu
```

### 6.2 Restore

```bash
mongorestore --uri="$MONGODB_URI" ./backups/backup_20260214/
```

---

## Próximos Passos

- [API REST](./04-api-rest.md)
- [Workers e Pipelines](./05-workers-pipelines.md)
