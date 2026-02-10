# System Architecture

## Overview

Pigmeu Copilot is a multi-stage pipeline system for automated technical book review generation. The system processes book submissions through several stages, each adding value and context before final article generation.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER / WEB UI                             │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI REST API                              │
│  ┌──────────────┬──────────────┬──────────────┬───────────────┐  │
│  │  Submission  │   Tasks      │   Config     │   Articles    │  │
│  │  Endpoints   │   Endpoints  │  Endpoints   │   Endpoints   │  │
│  └──────────────┴──────────────┴──────────────┴───────────────┘  │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ├──────────────────────┬──────────────────────┐
       │                      │                      │
       ▼                      ▼                      ▼
  ┌───────┐             ┌──────────┐          ┌──────────┐
  │MongoDB│             │  Redis   │          │ Celery   │
  │ Atlas │             │ Queue    │          │ Broker   │
  └───────┘             └──────────┘          └──────────┘
       │                      │
       │                      └──────────────┬────────────┐
       │                                     │            │
       │                      ┌──────────────▼──┐    ┌────▼──────┐
       │                      │  Worker 1        │    │ Worker 2  │
       │                      │  (Scraper)       │    │ (Context) │
       │                      └──────────────────┘    └────┬──────┘
       │                                                   │
       │          ┌────────────────────────────────┬──────▼────┐
       │          │                                │            │
       ▼          ▼                                ▼            ▼
    ┌────────┐  ┌───────────┐      ┌──────────┐  ┌──────────────┐
    │Amazon  │  │ Goodreads │      │ OpenAI   │  │ Article      │
    │Scraper │  │ Scraper   │      │ LLM      │  │ Generator    │
    └────────┘  └───────────┘      └──────────┘  └──────────────┘
       │              │                  │              │
       └──────┬───────┴──────┬──────────┴──────────────┘
              │              │
              ▼              ▼
         ┌─────────────────────────┐
         │  Final Article Output   │
         │  - Markdown formatted   │
         │  - SEO optimized        │
         │  - Ready for WordPress  │
         └─────────────────────────┘
```

## Data Flow

### Stage 1: Ingest
- User submits book info (title, author, URLs)
- System creates submission document
- Status: `pending_scrape`

### Stage 2: Scraping
- Worker scrapes Amazon (metadata, pricing, ratings)
- Worker scrapes secondary sources (Goodreads, author site)
- Extracted metadata persisted to `books` collection
- Status: `scraped` → `pending_context`

### Stage 3: Context Generation
- AI agent reads all summary sources
- Summarizes each source (3-5 summaries)
- Identifies key topics and themes
- Generates single knowledge base document (markdown)
- Status: `context_generated` → `pending_article`

### Stage 4: Article Generation
- AI agent receives knowledge base
- Generates structured article:
  - 8 total H2 sections (3 thematic + 5 fixed)
  - 1 H2 with 2-4 H3 subsections
  - 800-1,333 total words
  - SEO-optimized title (≤60 chars)
- Validates structure and word counts
- Status: `article_generated` → `ready_for_review`

### Stage 5: Review & Publishing
- User reviews article in UI
- User can manually edit content
- Once approved, publish to WordPress via API
- Status: `approved` → `published`

## Component Details

### FastAPI API (`src/app.py`)
- REST endpoints for all operations
- Request validation (Pydantic)
- Response serialization
- Automatic Swagger documentation
- Health checks

### Database (`src/db/`)
- **connection.py**: Async Motor client (MongoDB)
- **migrations.py**: Collection and index creation
- Collections:
  - `submissions`: Raw user input
  - `books`: Extracted metadata
  - `summaries`: Per-source summaries
  - `knowledge_base`: Aggregated context
  - `articles`: Final review articles
  - `articles_drafts`: User edits
  - `credentials`: Encrypted API keys
  - `prompts`: Configurable LLM prompts

### Task Queue (`src/workers/`)
- Celery tasks for background work
- Redis broker for task queueing
- Worker concurrency: 2-4 workers
- Task retries and error handling

### AI Agents (`src/agents/`)
- **context_agent**: Summarize and extract topics
- **knowledge_builder**: Aggregate summaries into KB
- **article_agent**: Generate structured articles
- LLM integration (OpenAI, Claude, etc.)

### Scrapers (`src/scrapers/`)
- **amazon.py**: Product metadata extraction
- **goodreads.py**: Reviews and ratings
- Playwright for JavaScript rendering
- BeautifulSoup for HTML parsing
- Proxy rotation and rate limiting

### Models (`src/models/`)
- **schemas.py**: Pydantic input/output models
- **enums.py**: Status enums, service types

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API | FastAPI | REST interface |
| Database | MongoDB Atlas | Document storage |
| Queue | Redis | Task queue broker |
| Worker | Celery | Background job processing |
| Scraping | Playwright | Browser automation |
| Parsing | BeautifulSoup | HTML/XML parsing |
| LLM | OpenAI GPT-4 | AI content generation |
| Container | Docker | Development & deployment |
| Language | Python 3.10+ | Core implementation |

## Database Schema

### submissions
```javascript
{
  _id: ObjectId,
  title: String,
  author_name: String,
  amazon_url: String,
  goodreads_url: String,
  author_site: String,
  other_links: [String],
  status: String, // pending_scrape, scraped, etc.
  created_at: Date,
  updated_at: Date
}
```

### books
```javascript
{
  _id: ObjectId,
  submission_id: ObjectId,
  extracted: {
    title_original: String,
    authors: [String],
    theme: String,
    lang_original: String,
    lang_edition: String,
    edition: String,
    pub_date: String,
    publisher: String,
    isbn: String,
    pages: Number,
    price_physical: Number,
    price_ebook: Number,
    amazon_rating: Number
  },
  last_updated: Date
}
```

### summaries
```javascript
{
  _id: ObjectId,
  book_id: ObjectId,
  source_url: String,
  summary_text: String,
  topics: [String],
  created_at: Date
}
```

### articles
```javascript
{
  _id: ObjectId,
  book_id: ObjectId,
  title: String,
  content: String, // Markdown
  word_count: Number,
  status: String,
  created_at: Date
}
```

## Deployment Architecture (Future)

```
┌─────────────────────────────────────────────────┐
│         Kubernetes Cluster                      │
│  ┌──────────────────────────────────────────┐   │
│  │  Ingress / Load Balancer                 │   │
│  └───────────────┬──────────────────────────┘   │
│                  │                              │
│  ┌──────────────▼──────────────┐               │
│  │  FastAPI Pods (replicas=3)  │               │
│  └─────────────────────────────┘               │
│                                                │
│  ┌──────────────┬──────────────┐              │
│  │ Celery Worker│ Celery Worker│              │
│  │ (replicas=5) │ (replicas=5) │              │
│  └──────────────┴──────────────┘              │
│                                                │
└────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
    ┌────────┐    ┌─────────┐    ┌──────────┐
    │ MongoDB│    │ Redis   │    │ Postgres │
    │ Atlas  │    │ Cloud   │    │ (optional)
    └────────┘    └─────────┘    └──────────┘

External:
- SendGrid (email notifications)
- Sentry (error tracking)
- DataDog (monitoring)
```

## Error Handling & Retries

- **Scraper failures**: Exponential backoff (1s, 2s, 4s, 8s...)
- **LLM timeouts**: Retry up to 3 times with longer timeouts
- **Database errors**: Automatic connection recovery
- **Dead letter queue**: Failed tasks logged for manual review

## Performance Considerations

- **Concurrency**: 2-4 Celery workers (adjustable)
- **Timeouts**: 30-minute hard limit per task
- **Caching**: Redis for temporary data (TTL 24h)
- **Batch processing**: Scrape multiple books in parallel
- **Rate limiting**: 1 request per 100ms to external APIs

## Security

- MongoDB: TLS encryption, IP whitelist
- API: CORS, request validation
- Credentials: Encrypted storage with rotation
- Environment: Secret management via .env
- Logging: Sensitive data redaction

## Monitoring

- **Logs**: Structured JSON logging to file
- **Metrics**: Prometheus-compatible endpoints (future)
- **Alerts**: Failed tasks, long-running tasks (future)
- **Tracing**: Distributed tracing (future)

## Scalability

- Horizontal scaling: Add more Celery workers
- Database: MongoDB Atlas auto-scaling
- Queue: Redis Cluster for high throughput
- API: Kubernetes HPA based on CPU/memory

See [SETUP.md](SETUP.md) for local development instructions.
