# CHANGELOG

## [0.1.1] - 2024-02-10

### Added - FASE 1: Ingest API
- **API Endpoints**:
  - `POST /submit` — Submit book for review (with duplicate detection)
  - `GET /tasks` — List all submissions with pagination/filtering
  - `GET /tasks/{id}` — Get detailed submission progress and extracted data
  - Health checks for all endpoints

- **Database Layer**:
  - `SubmissionRepository` — CRUD for submissions
  - `BookRepository` — CRUD for extracted metadata
  - `SummaryRepository` — CRUD for source summaries
  - `KnowledgeBaseRepository` — CRUD for aggregated context
  - `ArticleRepository` — CRUD for generated articles

- **Dependency Injection**:
  - FastAPI dependency injection for all repositories
  - Clean architecture separation

- **Data Validation**:
  - Pydantic schemas for all models
  - URL validation
  - Status enum validation

- **Error Handling**:
  - Comprehensive error responses (400, 404, 422, 500)
  - Duplicate submission detection
  - Graceful error logging

- **Documentation**:
  - Complete API documentation with examples
  - cURL, Python, JavaScript examples
  - Status transitions documented
  - Pagination guide

- **Testing**:
  - Integration tests for all endpoints
  - Validation tests
  - Error handling tests
  - Pagination tests

### Task Status
- [x] Repository layer (CRUD operations)
- [x] Dependency injection setup
- [x] POST `/submit` endpoint
- [x] GET `/tasks` and `/tasks/{id}` endpoints
- [x] Database integration
- [x] Integration tests
- [x] API documentation
- [x] Error handling

### FASE 2: Web Scraping (Completed)
- **New modules**:
  - `src/scrapers/proxy_manager.py` — Rate limiting, proxy & UA rotation, backoff strategies
  - `src/scrapers/extractors.py` — HTML extraction utilities (price, isbn, rating, authors, dates)
  - `src/scrapers/amazon.py` — Playwright-based Amazon scraper (metadata extraction)
  - `src/scrapers/goodreads.py` — Goodreads search + detail scraper
  - `src/scrapers/web_scraper.py` — Generic website scraper for author sites and pages
  - `src/workers/scraper_tasks.py` — Celery tasks orchestration (Amazon → Goodreads → author)
- **Highlights**:
  - Playwright integration for JS-rendered pages
  - Proxy rotation and rate limiting to reduce ban risk
  - Exponential backoff and retry strategies
  - Celery task chaining and status updates in `submissions` collection
  - Unit tests added: `tests/test_scrapers.py`

### Task Status
- [x] Amazon scraper implementation
- [x] Goodreads scraper
- [x] Playwright browser automation
- [x] Celery task trigger on submission

---

## [0.1.0] - 2024-02-10

### Added - FASE 0: Foundation
- Initial project structure and scaffolding
- MongoDB Atlas integration (cloud database)
- FastAPI application with health check endpoints
- Pydantic data models and validation schemas
- Celery worker configuration with Redis broker
- Docker and Docker Compose local development setup
- Database migrations script for collections and indexes
- Comprehensive documentation (SETUP, ARCHITECTURE)
- Environment configuration with `.env` support
- Logging setup and configuration
- Test framework with pytest integration
- 8 MongoDB collections with proper indexes:
  - submissions (task tracking)
  - books (extracted metadata)
  - summaries (source summaries)
  - knowledge_base (aggregated context)
  - articles (final articles)
  - articles_drafts (user edits)
  - credentials (encrypted API keys)
  - prompts (LLM prompt templates)

### Task Status
- [x] Project structure created
- [x] Database schema defined and migrations ready
- [x] API base setup with FastAPI
- [x] Worker setup with Celery/Redis
- [x] Docker containers configured
- [x] Documentation started

---

See [docs/SETUP.md](docs/SETUP.md) for setup instructions.
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design.
See [docs/API.md](docs/API.md) for API documentation.
