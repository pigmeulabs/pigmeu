# Arquitetura Técnica

**Versão:** 0.1.0  
**Última Atualização:** 2026-02-14

---

## 1. Visão Geral da Arquitetura

### 1.1 Diagrama de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTES                                        │
│                                                                              │
│    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│    │   Browser    │     │   API Client │     │    CI/CD     │              │
│    │  (Dashboard) │     │   (cURL)     │     │   (Scripts)  │              │
│    └──────┬───────┘     └──────┬───────┘     └──────┬───────┘              │
│           │                    │                    │                       │
└───────────┼────────────────────┼────────────────────┼───────────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI APPLICATION                                │
│                           (Porta 8000)                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         ROUTERS                                      │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │    │
│  │  │ /submit │ │ /tasks  │ │/settings│ │/articles│ │  /ui    │       │    │
│  │  │ ingest  │ │ tasks   │ │settings │ │articles │ │ static  │       │    │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │    │
│  └───────┼───────────┼───────────┼───────────┼───────────┼────────────┘    │
│          │           │           │           │           │                  │
│  ┌───────┴───────────┴───────────┴───────────┴───────────┴────────────┐    │
│  │                    DEPENDENCIES LAYER                               │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │  get_submission_repo, get_book_repo, get_article_repo, ...  │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│  ┌───────────────────────────────────┴──────────────────────────────────┐  │
│  │                    REPOSITORY LAYER                                   │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐        │  │
│  │  │Submission  │ │   Book     │ │  Article   │ │ Credential │        │  │
│  │  │Repository  │ │ Repository │ │ Repository │ │ Repository │        │  │
│  │  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘        │  │
│  └────────┼──────────────┼──────────────┼──────────────┼────────────────┘  │
│           │              │              │              │                    │
└───────────┼──────────────┼──────────────┼──────────────┼────────────────────┘
            │              │              │              │
            ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MONGODB                                         │
│                           (Porta 27017)                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │submissions │ │   books    │ │  articles  │ │credentials │ ...           │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           CELERY WORKERS                                     │
│                           (Background Tasks)                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         TASK MODULES                                  │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │    │
│  │  │scraper_tasks │ │article_tasks │ │publishing    │ │link_tasks  │  │    │
│  │  │              │ │              │ │_tasks        │ │            │  │    │
│  │  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └─────┬──────┘  │    │
│  └─────────┼────────────────┼────────────────┼───────────────┼─────────┘    │
│            │                │                │               │              │
│  ┌─────────┴────────────────┴────────────────┴───────────────┴─────────┐    │
│  │                    INTERNAL SERVICES                                  │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │    │
│  │  │   Amazon   │ │  Goodreads │ │    LLM     │ │ WordPress  │       │    │
│  │  │  Scraper   │ │  Scraper   │ │  Client    │ │  Client    │       │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
└──────────────────────────────────────┼───────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              REDIS                                           │
│                           (Porta 6379)                                       │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Broker + Backend para Celery                                       │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         SERVIÇOS EXTERNOS                                    │
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │   Amazon   │ │ Goodreads  │ │    LLM     │ │ WordPress  │               │
│  │   (Web)    │ │   (Web)    │ │   APIs     │ │   REST     │               │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Padrões Arquiteturais

| Padrão | Aplicação |
|--------|-----------|
| **Layered Architecture** | Separação entre API, Services, Repository, Data |
| **Async/Await** | Operações não-bloqueantes com Motor (MongoDB async) |
| **Task Queue** | Processamento assíncrono com Celery |
| **Repository Pattern** | Abstração de acesso a dados |
| **Dependency Injection** | FastAPI Depends para repositórios |
| **Event-Driven** | Tasks disparadas por eventos da API |

---

## 2. Componentes Detalhados

### 2.1 API FastAPI

**Arquivo Principal:** [`src/app.py`](../../src/app.py)

```python
# Estrutura da aplicação
app = FastAPI(
    title="Pigmeu Copilot API",
    version="0.1.0",
    lifespan=lifespan,  # Gerenciamento de ciclo de vida
)

# Routers incluídos
app.include_router(ingest.router)      # /submit
app.include_router(tasks.router)       # /tasks
app.include_router(settings_router.router)  # /settings
app.include_router(articles.router)    # /articles
app.include_router(operations.router)  # /operations
```

**Ciclo de Vida (Lifespan):**

1. **Startup:**
   - Executa migrações de banco de dados
   - Configura logging

2. **Shutdown:**
   - Fecha conexão com MongoDB

**Middlewares:**

- Arquivos estáticos: `/ui/static`
- Health check: `/health`

### 2.2 Camada de Dependências

**Arquivo:** [`src/api/dependencies.py`](../../src/api/dependencies.py)

```python
async def get_submission_repo() -> SubmissionRepository:
    db = await get_database()
    return SubmissionRepository(db)

async def get_book_repo() -> BookRepository:
    db = await get_database()
    return BookRepository(db)

# ... outros repositórios
```

**Injeção nos Endpoints:**

```python
@router.get("/tasks")
async def list_tasks(
    repo: SubmissionRepository = Depends(get_submission_repo),
):
    return await repo.list_all()
```

### 2.3 Camada de Repositórios

**Arquivo:** [`src/db/repositories.py`](../../src/db/repositories.py)

**Repositórios Disponíveis:**

| Repositório | Coleção | Operações |
|-------------|---------|-----------|
| `SubmissionRepository` | submissions | CRUD, list, stats, duplicate check |
| `BookRepository` | books | create_or_update, get_by_submission |
| `SummaryRepository` | summaries | create, get_by_book |
| `KnowledgeBaseRepository` | knowledge_base | create_or_update, get_by_book |
| `ArticleRepository` | articles | CRUD, drafts, WordPress link |
| `CredentialRepository` | credentials | CRUD, get_active |
| `PromptRepository` | prompts | CRUD, get_by_purpose, get_by_name |
| `ContentSchemaRepository` | content_schemas | CRUD |
| `PipelineConfigRepository` | pipeline_configs | CRUD, get_by_pipeline_id |

**Padrão de Repositório:**

```python
class SubmissionRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["submissions"]
    
    async def create(self, **kwargs) -> str:
        # Retorna ID do documento criado
        
    async def get_by_id(self, id: str) -> Optional[Dict]:
        # Retorna documento ou None
        
    async def list_all(self, skip, limit, filters) -> Tuple[List, int]:
        # Retorna lista e total
        
    async def update_status(self, id, status, extra_fields) -> bool:
        # Atualiza status e campos adicionais
```

### 2.4 Workers Celery

**Arquivo Principal:** [`src/workers/worker.py`](../../src/workers/worker.py)

```python
app = Celery(
    "pigmeu",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Configurações
app.conf.update(
    task_serializer="json",
    task_time_limit=30 * 60,  # 30 minutos
    task_track_started=True,
)
```

**Módulos de Tasks:**

| Módulo | Tasks |
|--------|-------|
| `scraper_tasks` | `scrape_amazon_task`, `process_additional_links_task`, `generate_context_task` |
| `article_tasks` | `generate_article_task` |
| `publishing_tasks` | `publish_article_task` |
| `link_tasks` | Processamento de links |

**Task de Entrada:**

```python
@app.task(name="start_pipeline")
def start_pipeline(submission_id: str, amazon_url: str, pipeline_id: str):
    """Ponto de entrada para iniciar o pipeline."""
    from src.workers.scraper_tasks import start_scraping_pipeline
    start_scraping_pipeline(submission_id, amazon_url, pipeline_id)
```

### 2.5 Scrapers

**Amazon Scraper:** [`src/scrapers/amazon.py`](../../src/scrapers/amazon.py)

```python
class AmazonScraper:
    async def initialize(self):
        # Inicializa Playwright
        
    async def scrape(self, url: str) -> Dict[str, Any]:
        # Extrai 13 campos de metadados
        
    async def cleanup(self):
        # Fecha browser
```

**Goodreads Scraper:** [`src/scrapers/goodreads.py`](../../src/scrapers/goodreads.py)

**Web Scraper Genérico:** [`src/scrapers/web_scraper.py`](../../src/scrapers/web_scraper.py)

### 2.6 Cliente LLM

**Arquivo:** [`src/workers/llm_client.py`](../../src/workers/llm_client.py)

```python
class LLMClient:
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: str,
        temperature: float,
        max_tokens: int,
        provider: Optional[str],
        api_key: Optional[str],
    ) -> str:
        # Gera resposta via LLM
```

**Provedores Suportados:**

- OpenAI (GPT-4, GPT-3.5)
- Groq (Llama 3.3 70B)
- Mistral (Mistral Large)
- Claude

---

## 3. Fluxos de Dados

### 3.1 Fluxo de Submissão

```
┌─────────┐    POST /submit    ┌─────────┐    create()    ┌─────────┐
│ Cliente │ ─────────────────► │  API    │ ─────────────► │ MongoDB │
└─────────┘                    └─────────┘                └─────────┘
                                    │
                                    │ start_pipeline.delay()
                                    ▼
                              ┌─────────┐
                              │  Redis  │
                              │ (Queue) │
                              └─────────┘
                                    │
                                    │ dequeue
                                    ▼
                              ┌─────────┐
                              │ Worker  │
                              │ Celery  │
                              └─────────┘
```

### 3.2 Fluxo de Scraping

```
┌─────────┐    scrape()    ┌─────────────┐    HTTP    ┌─────────┐
│ Worker  │ ─────────────► │   Playwright│ ─────────► │ Amazon  │
│ Celery  │                │   Browser   │            │  Web    │
└─────────┘                └─────────────┘            └─────────┘
     │                           │
     │ extract_data()            │ HTML
     ▼                           ▼
┌─────────────┐           ┌─────────────┐
│ BeautifulSoup│           │   Content   │
│  Parser     │ ◄───────── │   Raw       │
└─────────────┘           └─────────────┘
     │
     │ save
     ▼
┌─────────┐
│ MongoDB │
│  books  │
└─────────┘
```

### 3.3 Fluxo de Geração de Artigo

```
┌─────────────┐    get()    ┌─────────────┐
│  knowledge  │ ◄────────── │   Worker    │
│    _base    │             │   Celery    │
└─────────────┘             └─────────────┘
                                  │
                                  │ build_prompt()
                                  ▼
                            ┌─────────────┐
                            │    LLM      │
                            │   Client    │
                            └─────────────┘
                                  │
                                  │ generate()
                                  ▼
                            ┌─────────────┐
                            │   OpenAI/   │
                            │   Groq/     │
                            │   Mistral   │
                            └─────────────┘
                                  │
                                  │ markdown
                                  ▼
                            ┌─────────────┐
                            │   MongoDB   │
                            │  articles   │
                            └─────────────┘
```

---

## 4. Comunicação entre Componentes

### 4.1 API ↔ MongoDB

- **Driver:** Motor (async MongoDB driver)
- **Conexão:** Pool de conexões gerenciado
- **Operações:** CRUD assíncronas

### 4.2 API ↔ Redis

- **Uso:** Broker para Celery
- **Operações:** Enqueue tasks, check status

### 4.3 Workers ↔ MongoDB

- **Driver:** Motor (async)
- **Padrão:** Repository pattern reutilizado

### 4.4 Workers ↔ LLM APIs

- **Protocolo:** HTTP/REST
- **Autenticação:** API Keys
- **Timeout:** Configurável por provedor

### 4.5 Workers ↔ WordPress

- **Protocolo:** REST API
- **Autenticação:** Application Password
- **Operações:** Posts, Media, Categories

---

## 5. Tratamento de Erros

### 5.1 Níveis de Tratamento

| Nível | Estratégia |
|-------|------------|
| API | HTTPException com códigos apropriados |
| Repository | Retorna None ou levanta exceção |
| Worker | Log + retry + marcação de erro |
| Scraper | Retry com backoff |

### 5.2 Retry Strategy

```python
# Configuração de retry no scraper
config = RequestConfig(
    max_retries=3,
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    base_delay_seconds=2.0,
    max_delay_seconds=60.0,
)
```

### 5.3 Logging

```python
# Configuração de logging
setup_logger()
logger = logging.getLogger(__name__)

# Níveis
logger.info("Processing started")
logger.warning("Rate limit approaching")
logger.error("Failed to scrape", exc_info=True)
```

---

## 6. Segurança

### 6.1 Credenciais

- Armazenadas criptografadas no MongoDB
- API Keys nunca expostas em logs
- Suporte a múltiplas credenciais por serviço

### 6.2 Validação de Entrada

- Pydantic schemas para validação
- Sanitização de URLs
- Verificação de tipos

### 6.3 Rate Limiting

- Proteção contra sobrecarga de APIs externas
- Configurável por scraper

---

## 7. Escalabilidade

### 7.1 Horizontal

- Workers Celery podem ser escalados independentemente
- API stateless (pode ter múltiplas instâncias)
- MongoDB suporta sharding

### 7.2 Vertical

- Aumentar recursos dos containers
- Ajustar concorrência dos workers

### 7.3 Configuração de Concorrência

```bash
# Docker Compose
command: celery -A src.workers.worker worker --concurrency=4

# Ou via variável de ambiente
CELERY_WORKER_CONCURRENCY=4
```

---

## 8. Monitoramento

### 8.1 Health Checks

```bash
# API
curl http://localhost:8000/health

# Redis
redis-cli ping

# MongoDB
mongosh --eval "db.adminCommand('ping')"
```

### 8.2 Logs

- Localização: `logs/` directory
- Formato: JSON estruturado
- Rotação: Configurável

### 8.3 Métricas Disponíveis

- Total de tarefas por status
- Taxa de sucesso
- Tempo de processamento
- Erros por tipo

---

## 9. Decisões Arquiteturais

### 9.1 Por que MongoDB?

- Schema flexível para dados de livros variados
- Documentos aninhados para dados relacionados
- Boa performance para leituras

### 9.2 Por que Celery?

- Processamento assíncrono robusto
- Retry automático
- Monitoramento via Flower (opcional)

### 9.3 Por que Playwright?

- Renderização JavaScript
- Mais robusto que Selenium
- API moderna e async

### 9.4 Por que FastAPI?

- Performance assíncrona
- Documentação automática (OpenAPI)
- Validação integrada via Pydantic

---

## 10. Trade-offs

| Decisão | Vantagem | Desvantagem |
|---------|----------|-------------|
| MongoDB | Flexibilidade de schema | Menos consistência forte |
| Celery | Robustez | Complexidade operacional |
| Playwright | Renderização JS | Mais recursos necessários |
| Async | Performance | Complexidade de código |

---

## Próximos Passos

- [Modelo de Dados](./03-modelo-de-dados.md)
- [API REST](./04-api-rest.md)
- [Workers e Pipelines](./05-workers-pipelines.md)
