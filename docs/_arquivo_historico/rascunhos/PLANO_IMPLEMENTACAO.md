# 🚀 PLANO DE IMPLEMENTAÇÃO - PRÓXIMAS FEATURES

## Fase 1: MVP Completo (Critical) - **~6 horas**

### 1.1 Seed de Prompts Iniciais ✅ (Pronto)
**Arquivo:** `scripts/seed_prompts.py`
**Status:** Implementado (script criado)
**Próximo Passo:** Executar em dev
```bash
python scripts/seed_prompts.py
```

### 1.2 Estrutura de Artigo Conforme Spec (PRIORITY)
**Arquivo a Modificar:** `src/workers/scraper_tasks.py` / novo module `ArticleStructurer`
**Tempo Estimado:** 4 horas

**Requisitos:**
- [ ] Criar `ArticleStructurer` class para validar/estruturar artigos
- [ ] Implementar extração de 3 tópicos principais do livro
- [ ] Gerar artigo com 8 seções H2 exatas (3 temáticas + 5 fixas)
- [ ] Uma seção H2 deve ter 2-4 H3 subsections
- [ ] Validar word count: 800-1333 total
- [ ] Validar parágrafos: 50-100 palavras (3-6 frases)

**Fluxo:**
```
1. extract_topics(book_data) → {"topics": [{"name", "description", "subtopics"}]}
   - Usar prompt "Topic Extractor for Books"
   - Parse JSON response
   
2. structure_article(content, topics, book_data) → article_dict
   - Dividir conteúdo gerado em 8 seções
   - Validar estrutura e word count
   - Se falhar, regenerar com prompt melhorado
   
3. validate_article(article_dict) → bool
   - H1 existe e ≤60 caracteres
   - 8 H2s presentes
   - 1 H2 tem 2-4 H3s
   - Total 800-1333 palavras
   - Parágrafos tem 50-100 palavras
```

**Implementação Detalhada:**

```python
# src/workers/article_structurer.py (NOVO)

class ArticleStructurer:
    """Responsible for structuring and validating articles per spec."""
    
    @staticmethod
    async def extract_topics(book_data: dict, prompt_repo, llm_client) -> list[dict]:
        """Extract 3 main topics using LLM."""
        # Usar prompt "Topic Extractor for Books"
        # Return: [{"name": str, "description": str, "subtopics": [str]}]
        
    @staticmethod
    def structure_article(markdown_content: str, topics: list) -> dict:
        """Parse and structure markdown into required sections."""
        # Parse H1, H2s, H3s
        # Validate hierarchy
        # Return: {"h1": str, "sections": [{"h2": str, "content": str, "h3s": [...]}]}
        
    @staticmethod
    def validate_article(article: dict) -> tuple[bool, list[str]]:
        """Validate article against spec. Return (is_valid, errors)."""
        # Check word count
        # Check H1 length
        # Check section count and structure
        # Return errors if any
        
    @staticmethod
    async def regenerate_article(submission_id, kb_data, topics):
        """If validation fails, regenerate with better prompt."""
```

---

### 1.3 Busca e Sumarização de Links Externos (PRIORITY)
**Arquivo a Criar:** `src/scrapers/link_finder.py`, `src/workers/link_tasks.py`
**Tempo Estimado:** 4-5 horas

**Requisitos:**
- [ ] Busca automática de 3 links sobre o livro via Google/Bing
- [ ] Scrape de cada página
- [ ] Sumarização em markdown usando LLM
- [ ] Persistência em `summaries` collection

**Implementação:**

```python
# src/scrapers/link_finder.py (NOVO)

class LinkFinder:
    """Find relevant external links about books."""
    
    async def search_book_links(title: str, author: str, count: int = 3) -> list[dict]:
        """
        Search for book links.
        Returns: [{"url": str, "title": str, "snippet": str}]
        """
        # Usar SerpAPI ou similar para buscar
        # Filtrar por relevância
        
    async def fetch_and_parse(url: str) -> str:
        """Fetch URL and extract main content text."""
        
    async def summarize_page(content: str, title: str, prompt_repo, llm) -> dict:
        """Summarize page using Link Summarizer prompt."""
        # Return: {"summary": str, "topics": [str], "credibility": str}


# src/workers/link_tasks.py (NOVO)

@shared_task(base=ScraperTask, bind=True)
async def find_and_summarize_links(self, submission_id: str, book_title: str, author: str):
    """Celery task: Find 3 links about book and summarize each."""
    # 1. LinkFinder.search_book_links(...)
    # 2. Para cada link:
    #    - fetch_and_parse()
    #    - summarize_page() com LLM
    #    - persist em summaries collection
    # 3. Create/update KnowledgeBase com todos os resumos
```

---

### 1.4 Integração WordPess Publishing (PRIORITY)
**Arquivo a Criar:** `src/scrapers/wordpress_client.py`, `src/api/publishing.py`, nova task
**Tempo Estimado:** 3 horas

**Requisitos:**
- [ ] `POST /tasks/{id}/publish_article` endpoint
- [ ] `publish_article_task` Celery task
- [ ] Autenticação WordPress REST API
- [ ] Criar post com artigo (título, conteúdo, categorias, tags)
- [ ] SEO metadata (meta description, prioridade)
- [ ] Retornar link do artigo publicado
- [ ] UI: Botão "Publish to WordPress"

**Implementação:**

```python
# src/repositories.py (EXISTING - ADD METHOD)

class ArticleRepository:
    async def update_with_wordpress_link(self, article_id: str, wp_post_id: str, wp_url: str):
        """Store WordPress publication info."""
        await self.collection.update_one(
            {"_id": ObjectId(article_id)},
            {"$set": {
                "wordpress_post_id": wp_post_id,
                "wordpress_url": wp_url,
                "published_at": datetime.utcnow(),
                "status": "published"
            }}
        )

# src/api/publishing.py (NOVO)

@router.post("/tasks/{task_id}/publish_article")
async def publish_article(task_id: str, credentials: CredentialRepository = ...):
    """Enqueue article publication to WordPress."""
    # 1. Get article from DB
    # 2. Get WordPress credentials
    # 3. Validate article
    # 4. Enqueue publish_article_task
    # Return: {"status": "queued", "task_id": celery_task_id}

# src/workers/publishing_tasks.py (NOVO)

@shared_task(bind=True)
async def publish_article_task(self, article_id: str):
    """Publish article to WordPress."""
    # 1. Get article from DB
    # 2. Get WordPress credentials and URL
    # 3. Prepare post data (title, content, category, tags)
    # 4. POST /wp-json/wp/v2/posts
    # 5. Extract post ID and URL
    # 6. Update article with WordPress metadata
    # 7. Update submission status to "published"
```

---

## Fase 2: Polish & Features (High Priority) - **~6 horas**

### 2.1 Extração Dinâmica de Tópicos
**Status:** Parcialmente feito (prompt existe, não está integrado no pipeline)
**Tempo:** 1.5 horas

**Integrar em:** `generate_article_task`
```python
# Após scraping, antes de gerar artigo:
topics = await ArticleStructurer.extract_topics(book_data)
# Passar topics para prompt de geração de artigo
```

### 2.2 Filtro e Busca na Dashboard
**Status:** HTML pronto, JS não wired
**Tempo:** 1 hora

**No `app.js`:**
```javascript
// Add listeners para #filter-status e #search-tasks
document.getElementById('filter-status').addEventListener('change', async (e) => {
  const status = e.target.value;
  skip = 0;
  await fetchTasks(status);
});

document.getElementById('search-tasks').addEventListener('input', debounce(async (e) => {
  const query = e.target.value;
  // Filtrar tasksGrid por título/autor (client-side ou API)
}, 300));
```

### 2.3 Modal de Edição de Artigo (Draft)
**Tempo:** 2 horas
**Arquivos:**
- [ ] `src/api/articles.py` — Novo endpoint `PATCH /articles/{id}`
- [ ] `ArticleRepository.update()` — Update conteúdo
- [ ] UI: Modal editor markdown com preview

### 2.4 Retry de Tarefas Falhadas
**Tempo:** 0.5 horas
**Endpoint:** `POST /tasks/{id}/retry`
```python
@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    """Re-enqueue failed task."""
    submission_repo.update_status(task_id, "pending_scrape")
    start_pipeline(task_id)
```

### 2.5 Métricas e Dashboard Stats
**Tempo:** 1.5 horas
**Endpoint:** `GET /stats`
```json
{
  "total_tasks": 10,
  "by_status": {"pending": 2, "processing": 1, "completed": 7, "failed": 0},
  "success_rate": 0.87,
  "avg_generation_time_seconds": 120
}
```

---

## Fase 3: Testes & Deployment (Opcional)
- [ ] Testes e2e: submit → generate context → article → publish
- [ ] Load testing
- [ ] Docker build e deploy

---

## 📋 Quick Start

### Executar Hoje:
```bash
# 1. Seed prompts
python scripts/seed_prompts.py

# 2. Testar endpoint de tasks
curl http://localhost:8000/tasks

# 3. Submeter livro teste
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{"title": "Designing Data", "author_name": "Kleppmann", "amazon_url": "https://amazon.com/..."}'
```

### Próximos PRs:
1. **PR #1:** Articles Structuring + Topic Extraction
2. **PR #2:** Link Finder + Summarizer Integration
3. **PR #3:** WordPress Publishing
4. **PR #4:** Dashboard Polish (filters, retry, drafts)

---

## 🎯 Definition of Done

Feature está pronta quando:
- ✅ Backend implementado e testado
- ✅ DB migrations/schema atualizado
- ✅ API endpoints working
- ✅ UI integrada e responsiva
- ✅ Error handling e logging
- ✅ Documentado em README/ARCHITECTURE

