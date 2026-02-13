# Workers e Pipelines

**Versão:** 0.1.0  
**Última Atualização:** 2026-02-14

---

## 1. Visão Geral

O sistema utiliza **Celery** como framework de processamento assíncrono, com **Redis** como broker e backend. Os workers executam tarefas em background, permitindo que a API responda rapidamente enquanto o processamento pesado ocorre de forma assíncrona.

### 1.1 Arquitetura de Workers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API FastAPI                                     │
│                                                                              │
│   POST /submit ──────────────► start_pipeline.delay() ──────┐               │
│   POST /tasks/{id}/retry ────► start_pipeline.delay() ──────┤               │
│   POST /tasks/{id}/retry_step ► _enqueue_stage_retry() ─────┤               │
│                                                              │               │
└──────────────────────────────────────────────────────────────┼───────────────┘
                                                               │
                                                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              REDIS (Broker)                                  │
│                                                                              │
│   Queue: celery                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Task Messages (JSON)                                                │   │
│   │  - start_pipeline                                                    │   │
│   │  - scrape_amazon_task                                                │   │
│   │  - generate_context_task                                             │   │
│   │  - generate_article_task                                             │   │
│   │  - publish_article_task                                              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                                               │
                                                               │ dequeue
                                                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CELERY WORKERS                                     │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Worker Process (concurrency=2)                                      │   │
│   │                                                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │scraper_tasks │  │article_tasks │  │publishing    │              │   │
│   │  │              │  │              │  │_tasks        │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Configuração do Celery

### 2.1 Arquivo Principal

**Arquivo:** [`src/workers/worker.py`](../../src/workers/worker.py)

```python
from celery import Celery
from src.config import settings

app = Celery(
    "pigmeu",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_ignore_result=True,
)

# Importar tasks para registro
import src.workers.scraper_tasks
import src.workers.article_tasks
import src.workers.publishing_tasks
import src.workers.link_tasks
```

### 2.2 Configurações

| Configuração | Valor | Descrição |
|--------------|-------|-----------|
| `task_serializer` | json | Serialização de tasks |
| `result_serializer` | json | Serialização de resultados |
| `task_time_limit` | 1800s | Timeout máximo (30 min) |
| `task_track_started` | true | Rastreia início da task |
| `task_ignore_result` | true | Não armazena resultado |

### 2.3 Execução

```bash
# Desenvolvimento
celery -A src.workers.worker worker --loglevel=info --concurrency=2

# Docker
docker-compose -f infra/docker-compose.yml up worker
```

---

## 3. Módulos de Tasks

### 3.1 scraper_tasks

**Arquivo:** [`src/workers/scraper_tasks.py`](../../src/workers/scraper_tasks.py)

Tasks de scraping e processamento de dados.

| Task | Descrição |
|------|-----------|
| `start_scraping_pipeline` | Inicia pipeline completo |
| `scrape_amazon_task` | Scraping da Amazon |
| `process_additional_links_task` | Processa links adicionais |
| `consolidate_bibliographic_task` | Consolida dados bibliográficos |
| `internet_research_task` | Pesquisa web |
| `generate_context_task` | Gera contexto via IA |

**Exemplo de Task:**

```python
@shared_task(name="scrape_amazon_task")
def scrape_amazon_task(submission_id: str, amazon_url: str):
    """Scraping da Amazon."""
    return asyncio.run(_scrape_amazon_async(submission_id, amazon_url))

async def _scrape_amazon_async(submission_id: str, amazon_url: str):
    # 1. Atualizar status
    db = await get_db()
    repo = SubmissionRepository(db)
    await repo.update_status(submission_id, SubmissionStatus.SCRAPING_AMAZON)
    
    # 2. Executar scraping
    scraper = AmazonScraper()
    await scraper.initialize()
    try:
        data = await scraper.scrape(amazon_url)
        
        # 3. Salvar dados
        book_repo = BookRepository(db)
        await book_repo.create_or_update(submission_id, extracted=data)
        
        # 4. Atualizar status
        await repo.update_status(submission_id, SubmissionStatus.SCRAPED)
        
    finally:
        await scraper.cleanup()
```

### 3.2 article_tasks

**Arquivo:** [`src/workers/article_tasks.py`](../../src/workers/article_tasks.py)

Tasks de geração de artigos.

| Task | Descrição |
|------|-----------|
| `generate_article_task` | Gera artigo final |

**Fluxo da Task:**

```python
@shared_task(name="generate_article_task")
def generate_article_task(submission_id: str):
    """Gera artigo a partir do contexto."""
    return asyncio.run(_generate_article_async(submission_id))

async def _generate_article_async(submission_id: str):
    # 1. Carregar dados
    db = await get_db()
    # ... carregar submission, book, knowledge_base
    
    # 2. Resolver configuração de IA
    config = await _resolve_article_generation_config(
        pipeline_repo, prompt_repo, credential_repo, pipeline_id
    )
    
    # 3. Gerar artigo via ArticleStructurer
    structurer = ArticleStructurer()
    article_content = await structurer.generate_article(
        book_data=book_data,
        knowledge_base=kb,
        llm_config=config,
    )
    
    # 4. Salvar artigo
    article_repo = ArticleRepository(db)
    article_id = await article_repo.create(
        book_id=book_id,
        title=article_title,
        content=article_content,
        word_count=word_count,
        status=ArticleStatus.DRAFT,
    )
    
    # 5. Atualizar status
    await repo.update_status(submission_id, SubmissionStatus.READY_FOR_REVIEW)
```

### 3.3 publishing_tasks

**Arquivo:** [`src/workers/publishing_tasks.py`](../../src/workers/publishing_tasks.py)

Tasks de publicação.

| Task | Descrição |
|------|-----------|
| `publish_article_task` | Publica artigo no WordPress |

**Fluxo da Task:**

```python
@shared_task(name="publish_article_task")
def publish_article_task(article_id: str, submission_id: str):
    """Publica artigo no WordPress."""
    return asyncio.run(_publish_async(article_id, submission_id))

async def _publish_async(article_id: str, submission_id: str):
    # 1. Carregar artigo e credenciais
    # 2. Conectar ao WordPress
    # 3. Upload de imagem de capa (se houver)
    # 4. Criar post
    # 5. Atualizar artigo com URL do post
    # 6. Atualizar status da submissão
```

### 3.4 link_tasks

**Arquivo:** [`src/workers/link_tasks.py`](../../src/workers/link_tasks.py)

Tasks de processamento de links.

| Task | Descrição |
|------|-----------|
| `process_link_task` | Processa um link individual |

---

## 4. Pipeline Book Review v2

### 4.1 Definição dos Steps

```python
BOOK_REVIEW_PIPELINE_TEMPLATE = {
    "name": "Book Review",
    "slug": "book-review",
    "version": "2.0",
    "steps": [
        {
            "id": "amazon_scrape",
            "name": "Amazon link scrape",
            "type": "scraping",
            "uses_ai": False,
            "delay_seconds": 0,
        },
        {
            "id": "additional_links_scrape",
            "name": "Additional links scrape",
            "type": "scraping+llm",
            "uses_ai": True,
            "ai": {
                "provider": "mistral",
                "model_id": "mistral-large-latest",
                "default_prompt_purpose": "book_review_link_bibliography_extract",
            },
        },
        {
            "id": "summarize_additional_links",
            "name": "Summarize additional links",
            "type": "llm",
            "uses_ai": True,
            "ai": {
                "provider": "groq",
                "model_id": "llama-3.3-70b-versatile",
                "default_prompt_purpose": "book_review_link_summary",
            },
        },
        {
            "id": "consolidate_book_data",
            "name": "Consolidate book data",
            "type": "data-processing",
            "uses_ai": False,
        },
        {
            "id": "internet_research",
            "name": "Internet research",
            "type": "search+llm",
            "uses_ai": True,
            "ai": {
                "provider": "groq",
                "model_id": "llama-3.3-70b-versatile",
                "default_prompt_purpose": "book_review_web_research",
            },
        },
        {
            "id": "context_generation",
            "name": "Generate context",
            "type": "llm",
            "uses_ai": True,
            "ai": {
                "provider": "groq",
                "model_id": "llama-3.3-70b-versatile",
                "default_prompt_purpose": "context",
            },
        },
        {
            "id": "article_generation",
            "name": "Generate article",
            "type": "llm",
            "uses_ai": True,
            "ai": {
                "provider": "openai",
                "model_id": "gpt-4",
                "default_prompt_purpose": "article",
            },
        },
    ],
}
```

### 4.2 Fluxo de Execução

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE: BOOK REVIEW v2                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐                                                         │
│  │ 1. amazon_scrape│                                                         │
│  │    (scraping)   │                                                         │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────┐                                                 │
│  │ 2. additional_links     │                                                 │
│  │    _scrape (scraping+llm)│                                                │
│  └────────┬────────────────┘                                                 │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────┐                                                 │
│  │ 3. summarize_additional │                                                 │
│  │    _links (llm)         │                                                 │
│  └────────┬────────────────┘                                                 │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────┐                                                 │
│  │ 4. consolidate_book_data│                                                 │
│  │    (data-processing)    │                                                 │
│  └────────┬────────────────┘                                                 │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────┐                                                 │
│  │ 5. internet_research    │                                                 │
│  │    (search+llm)         │                                                 │
│  └────────┬────────────────┘                                                 │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────┐                                                 │
│  │ 6. context_generation   │                                                 │
│  │    (llm)                │                                                 │
│  └────────┬────────────────┘                                                 │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────┐                                                 │
│  │ 7. article_generation   │                                                 │
│  │    (llm)                │                                                 │
│  └────────┬────────────────┘                                                 │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────┐                                                 │
│  │ 8. publishing (opcional)│                                                 │
│  │    (wordpress)          │                                                 │
│  └─────────────────────────┘                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Detalhes de Cada Step

#### Step 1: amazon_scrape

**Tipo:** scraping  
**Usa IA:** Não

**Operações:**
1. Inicializa Playwright browser
2. Navega para URL da Amazon
3. Extrai metadados do livro
4. Salva na coleção `books`
5. Atualiza status para `scraped`

**Dados Extraídos:**
- title, authors, asin, isbn_10, isbn_13
- price_book, price_ebook
- rating, rating_count
- pages, language, publisher, publication_date
- cover_image_url, description

---

#### Step 2: additional_links_scrape

**Tipo:** scraping+llm  
**Usa IA:** Sim (Mistral)

**Operações:**
1. Processa `goodreads_url`, `author_site`, `other_links`
2. Para cada link:
   - Faz scraping do conteúdo
   - Usa LLM para extrair dados bibliográficos
3. Salva candidatos em `link_bibliographic_candidates`

---

#### Step 3: summarize_additional_links

**Tipo:** llm  
**Usa IA:** Sim (Groq)

**Operações:**
1. Para cada link processado:
   - Usa LLM para gerar resumo
   - Identifica tópicos e pontos-chave
2. Salva resumos na coleção `summaries`

---

#### Step 4: consolidate_book_data

**Tipo:** data-processing  
**Usa IA:** Não

**Operações:**
1. Consolida dados de todas as fontes
2. Remove duplicatas
3. Resolve conflitos (prioriza Amazon)
4. Atualiza `book.extracted`

---

#### Step 5: internet_research

**Tipo:** search+llm  
**Usa IA:** Sim (Groq)

**Operações:**
1. Realiza pesquisa web sobre livro/autor
2. Usa LLM para sintetizar informações
3. Identifica temas e público-alvo
4. Salva em `book.extracted.web_research`

---

#### Step 6: context_generation

**Tipo:** llm  
**Usa IA:** Sim (Groq)

**Operações:**
1. Consolida todas as informações coletadas
2. Usa LLM para gerar base de conhecimento
3. Cria índice de tópicos
4. Salva na coleção `knowledge_base`

---

#### Step 7: article_generation

**Tipo:** llm  
**Usa IA:** Sim (OpenAI/Groq)

**Operações:**
1. Carrega contexto da `knowledge_base`
2. Usa LLM para gerar artigo estruturado
3. Valida contagem de palavras
4. Salva na coleção `articles`
5. Atualiza status para `ready_for_review`

---

## 5. Resolução de Configuração de IA

### 5.1 Prioridade de Configuração

```
1. Step do Pipeline (ai.provider, ai.model_id)
2. Prompt associado (model_id, temperature, max_tokens)
3. Credencial associada (api_key)
4. Defaults do sistema
```

### 5.2 Código de Resolução

```python
async def _resolve_article_generation_config(
    pipeline_repo: PipelineConfigRepository,
    prompt_repo: PromptRepository,
    credential_repo: CredentialRepository,
    pipeline_id: str,
) -> Dict[str, Any]:
    config = {
        "provider": "openai",
        "model_id": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2500,
        # ...
    }
    
    # 1. Carregar pipeline
    pipeline_doc = await pipeline_repo.get_by_pipeline_id(pipeline_id)
    step_doc = find_step(pipeline_doc, "article_generation")
    ai_doc = step_doc.get("ai", {})
    
    # 2. Carregar prompt
    if ai_doc.get("prompt_id"):
        prompt_doc = await prompt_repo.get_by_id(ai_doc["prompt_id"])
    elif ai_doc.get("default_prompt_purpose"):
        prompt_doc = await prompt_repo.get_active_by_purpose(
            ai_doc["default_prompt_purpose"]
        )
    
    # 3. Carregar credencial
    if ai_doc.get("credential_id"):
        credential_doc = await credential_repo.get_by_id(
            ai_doc["credential_id"]
        )
    elif ai_doc.get("default_credential_name"):
        credential_doc = await credential_repo.get_active_by_name(
            ai_doc["default_credential_name"]
        )
    
    # 4. Merge de configurações
    config.update({
        "provider": ai_doc.get("provider") or prompt_doc.get("provider"),
        "model_id": ai_doc.get("model_id") or prompt_doc.get("model_id"),
        "api_key": credential_doc.get("key"),
        # ...
    })
    
    return config
```

---

## 6. Tratamento de Erros

### 6.1 Estratégia de Retry

```python
# Retry automático do Celery
@shared_task(
    name="scrape_amazon_task",
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
)
def scrape_amazon_task(submission_id: str, amazon_url: str):
    ...
```

### 6.2 Registro de Erros

```python
# No worker
try:
    # ... operação
except Exception as e:
    logger.error("Failed to process: %s", e, exc_info=True)
    
    # Salvar erro na submissão
    await repo.update_fields(submission_id, {
        "errors": [
            *existing_errors,
            {
                "step": current_step,
                "message": str(e),
                "timestamp": datetime.utcnow(),
            }
        ]
    })
    
    # Atualizar status
    await repo.update_status(submission_id, SubmissionStatus.FAILED)
```

### 6.3 Retry Manual via API

```bash
# Reiniciar pipeline completo
POST /tasks/{submission_id}/retry

# Reiniciar de step específico
POST /tasks/{submission_id}/retry_step
{"stage": "context_generation"}
```

---

## 7. Monitoramento

### 7.1 Logs

```python
import logging

logger = logging.getLogger(__name__)

# Níveis
logger.debug("Detailed information")
logger.info("Processing started")
logger.warning("Rate limit approaching")
logger.error("Failed to process", exc_info=True)
```

### 7.2 Flower (Opcional)

Interface web para monitoramento Celery:

```bash
pip install flower
celery -A src.workers.worker flower --port=5555
```

Acesso: http://localhost:5555

---

## 8. Defaults de IA

**Arquivo:** [`src/workers/ai_defaults.py`](../../src/workers/ai_defaults.py)

```python
# Provedores
PROVIDER_OPENAI = "openai"
PROVIDER_GROQ = "groq"
PROVIDER_MISTRAL = "mistral"
PROVIDER_CLAUDE = "claude"
DEFAULT_PROVIDER = PROVIDER_GROQ

# Modelos
MODEL_GROQ_LLAMA_3_3_70B = "llama-3.3-70b-versatile"
MODEL_MISTRAL_LARGE_LATEST = "mistral-large-latest"
MODEL_OPENAI_GPT_4 = "gpt-4"

# Defaults por propósito
BOOK_REVIEW_CONTEXT_PROVIDER = PROVIDER_GROQ
BOOK_REVIEW_CONTEXT_MODEL_ID = MODEL_GROQ_LLAMA_3_3_70B

BOOK_REVIEW_ARTICLE_PROVIDER = PROVIDER_OPENAI
BOOK_REVIEW_ARTICLE_MODEL_ID = MODEL_OPENAI_GPT_4
```

---

## Próximos Passos

- [Scrapers e Integrações](./06-scrapers-integracoes.md)
- [Frontend Dashboard](./07-frontend-dashboard.md)
