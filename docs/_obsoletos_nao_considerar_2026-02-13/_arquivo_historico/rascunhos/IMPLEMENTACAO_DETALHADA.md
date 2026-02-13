# 🛠️ GUIA TÉCNICO DETALHADO - IMPLEMENTAÇÃO CRÍTICA

## 1. Estructura de Artigo Conforme Spec

### Hierarquia Esperada

```markdown
# Book Title — Review (H1, ≤60 caracteres)

## Introduction to Book Topic (H2, ≥150 palavras)
Paragrafo 1. 50-100 palavras, 3-6 frases...
Paragrafo 2. 50-100 palavras, 3-6 frases...

## Context and Motivation (H2, ≥150 palavras)
...

## Impact and Applicability (H2, ≥150 palavras)
...

## [Topic 1 - Extracted] (H2, ≥200 palavras)
### [Subtopic 1.1] (H3)
Content...

### [Subtopic 1.2] (H3)
Content...

### [Subtopic 1.3] (H3)
Content...

## [Topic 2 - Extracted] (H2, ≥200 palavras)
...

## [Topic 3 - Extracted] (H2, ≥200 palavras)
...

## Book Details (H2, ≥100 palavras)
- **Author:** Name
- **ISBN:** ...
- **Publisher:** ...
- **Publication Date:** ...

## About the Author (H2, ≥100 palavras)
...

## Download & Links (H2, ≥50 palavras)
...

## Related Subjects (H2, ≥80 palavras)
...
```

**Totais:**
- **H1:** 1 (título, ≤60 chars)
- **H2:** 8 (3 temáticos + 5 fixos)
- **H3:** Apenas na seção temática, máximo 4 por H2
- **Palavra Total:** 800-1333
- **Parágrafos:** 50-100 palavras cada

---

### Schema em MongoDB

**Collection: `articles`**
```javascript
{
  "_id": ObjectId,
  "book_id": ObjectId,           // Referência a books collection
  "submission_id": ObjectId,     // Referência a submissions
  "title": "String (≤60 chars)",
  "content": "String (markedown full)",
  "word_count": Number,
  "structure": {
    "h1": "String",
    "sections": [
      {
        "title": "String (H2)",
        "word_count": Number,
        "min_required": Number,   // 150, 200, etc.
        "content": "String",
        "h3_subsections": [
          {
            "title": "String (H3)",
            "word_count": Number,
            "content": "String"
          }
        ]
      }
    ]
  },
  "topics_used": [
    {
      "name": "String",
      "description": "String",
      "subtopics": ["String"]
    }
  ],
  "metadata": {
    "seo_keywords": ["String"],
    "meta_description": "String (≤160 chars)",
    "reading_time_minutes": Number
  },
  "status": "draft|published",
  "wordpress_post_id": Number,
  "wordpress_url": "String",
  "published_at": ISODate,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

---

### Validação Logic (Python)

```python
from dataclasses import dataclass

@dataclass
class ArticleValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]

class ArticleValidator:
    
    @staticmethod
    def validate_h1(title: str) -> tuple[bool, str]:
        """Validate H1 title."""
        if len(title) > 60:
            return False, f"H1 title too long: {len(title)} > 60"
        if len(title) < 20:
            return False, "H1 title too short"
        return True, ""
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text (simple split)."""
        return len(text.split())
    
    @staticmethod
    def validate_section(section_dict: dict) -> tuple[bool, list[str]]:
        """
        Validate a single H2 section.
        section_dict = {"title": str, "content": str, "h3s": [...]}
        """
        errors = []
        
        # Check word count
        word_count = ArticleValidator.count_words(section_dict['content'])
        min_words = section_dict.get('min_words', 100)
        if word_count < min_words:
            errors.append(f"Section '{section_dict['title']}' too short: {word_count} < {min_words}")
        
        # Check H3 count if has H3s
        h3s = section_dict.get('h3_subsections', [])
        if h3s and len(h3s) > 4:
            errors.append(f"Section '{section_dict['title']}' has too many H3s: {len(h3s)} > 4")
        
        # Validate each H3
        for h3 in h3s:
            h3_words = ArticleValidator.count_words(h3['content'])
            if h3_words < 80:
                errors.append(f"H3 '{h3['title']}' too short: {h3_words} < 80")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_article(article: dict) -> ArticleValidationResult:
        """Full article validation."""
        errors = []
        warnings = []
        
        # Validate H1
        valid, err = ArticleValidator.validate_h1(article['title'])
        if not valid:
            errors.append(err)
        
        # Get sections
        structure = article.get('structure', {})
        sections = structure.get('sections', [])
        
        # Validate section count
        if len(sections) != 8:
            errors.append(f"Expected 8 H2 sections, got {len(sections)}")
        
        # Validate each section
        total_words = 0
        h2_with_h3_count = 0
        
        for section in sections:
            valid, section_errors = ArticleValidator.validate_section(section)
            errors.extend(section_errors)
            
            section_words = ArticleValidator.count_words(section['content'])
            total_words += section_words
            
            if section.get('h3_subsections'):
                h2_with_h3_count += 1
        
        # Validate H2 with H3 count
        if h2_with_h3_count > 1:
            warnings.append(f"More than 1 H2 has H3s: {h2_with_h3_count}")
        
        # Validate total word count
        if total_words < 800:
            errors.append(f"Total word count too low: {total_words} < 800")
        if total_words > 1333:
            errors.append(f"Total word count too high: {total_words} > 1333")
        
        # Overall validation
        is_valid = len(errors) == 0
        
        return ArticleValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
```

**Uso:**
```python
result = ArticleValidator.validate_article(article_dict)
if not result.is_valid:
    logger.error(f"Article validation failed: {result.errors}")
    # Regenerate article com melhor prompt
```

---

## 2. Link Finder & Summarizer

### API de Busca (Google Custom Search ou SerpAPI)

**Requisita:**
- API Key para Google Custom Search ou SerpAPI
- Query: `"{Title}" OR "{Title} by {Author}" review OR summary`
- Limitar a 3 resultados mais relevantes

**Response esperado:**
```python
[
  {
    "url": "https://example.com/article-about-book",
    "title": "Article Title",
    "snippet": "Short preview...",
    "domain": "example.com"
  }
]
```

### Scraping & Content Extraction

```python
# src/scrapers/link_scraper.py

class LinkScraper:
    """Extract main content from web pages."""
    
    async def fetch_and_extract(url: str) -> str:
        """
        Fetch URL and extract main text content.
        Returns: Plain text (paragraphs concatenated)
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                html = await resp.text()
        
        # Use BeautifulSoup para extrair main content
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script/style
        for script in soup(['script', 'style']):
            script.decompose()
        
        # Get main content (article, main, or largest text block)
        # Remover nav, footer, ads
        
        # Get all paragraphs
        text = " ".join([p.get_text() for p in soup.find_all('p')])
        
        return text[:3000]  # Limitar a 3000 chars para prompts
```

### Summarization using LLM

**Prompt:** "Link Summarizer" (seeded no BD)

```python
@shared_task(bind=True)
async def summarize_link_task(self, url: str, page_content: str, book_title: str):
    """
    Summarize a single link's content.
    Store in summaries collection.
    """
    db = await get_db()
    prompt_repo = PromptRepository(db)
    
    # Get "Link Summarizer" prompt
    prompt = await prompt_repo.get_by_name("Link Summarizer")
    
    # Prepare user prompt
    user_prompt = prompt['user_prompt'].replace(
        "{{title}}", book_title
    ).replace(
        "{{content}}", page_content[:2000]  # Truncate if too long
    )
    
    # Call LLM
    response = openai.ChatCompletion.create(
        model=prompt['model_id'],
        messages=[
            {"role": "system", "content": prompt['system_prompt']},
            {"role": "user", "content": user_prompt},
        ],
        temperature=prompt['temperature'],
        max_tokens=prompt['max_tokens'],
    )
    
    summary_text = response.choices[0].message['content']
    
    # Parse response (should include topics)
    # Extract: main_idea, key_points, topics
    
    # Persist
    summary_repo = SummaryRepository(db)
    await summary_repo.create(
        book_id=book_id,
        source_url=url,
        summary_text=summary_text,
        topics=[...],  # Extracted from summary
        credibility="high/medium/low"
    )
```

### Schema em MongoDB

**Collection: `summaries`**
```javascript
{
  "_id": ObjectId,
  "book_id": ObjectId,
  "source_url": "String (URL)",
  "source_domain": "String",
  "summary_text": "String (markdown content, 150-300 words)",
  "topics": ["String"],                    // Keywords/Topics extracted
  "key_points": ["String"],                // Main insights
  "credibility": "high|medium|low",        // Source quality
  "created_at": ISODate
}
```

---

## 3. WordPress Publishing

### Architecture de Publicação

```
┌─────────────────────┐
│ Article in MongoDB  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│ publish_article_task (Task) │
└──────────┬──────────────────┘
           │
    ┌──────┴───────┐
    ▼              ▼
[Validate]   [Format for WP]
    │              │
    └──────┬───────┘
           ▼
┌──────────────────────────────────┐
│ POST /wp-json/wp/v2/posts (WP)  │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────┐
│ POST_ID + URL        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────┐
│ Update article.wordpress_post_id │
│       article.published_at       │
└──────────────────────────────────┘
```

### WordPress REST API Integration

```python
# src/scrapers/wordpress_client.py

class WordPressClient:
    """Client for WordPress REST API."""
    
    def __init__(self, wordpress_url: str, access_token: str):
        """
        wordpress_url: e.g., https://myblog.com
        access_token: OAuth2 token or basic auth
        """
        self.base_url = wordpress_url.rstrip('/')
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )
    
    async def create_post(self, post_data: dict) -> dict:
        """
        Create a new post in WordPress.
        
        post_data = {
            "title": "String",
            "content": "String (HTML or markdown)",
            "excerpt": "String (140 chars)",
            "categories": [int],              # Category IDs
            "tags": [int],                    # Tag IDs  
            "status": "publish|draft|pending",
            "featured_media": int,             # Featured image ID
            "meta": {                          # SEO metadata
                "_yoast_wpseo_metadesc": "...",
                "_yoast_wpseo_focuskw": "..."
            }
        }
        """
        async with self.session.post(
            f"{self.api_url}/posts",
            json=post_data
        ) as resp:
            if resp.status != 201:
                raise Exception(f"WP API error: {resp.status}")
            return await resp.json()
    
    async def close(self):
        """Close session."""
        await self.session.close()

# Usage in task:
wp_client = WordPressClient(
    wordpress_url="https://myblog.com",
    access_token=wp_credential['key']
)

post_data = {
    "title": article['title'],
    "content": convert_markdown_to_html(article['content']),
    "excerpt": article['metadata']['meta_description'],
    "categories": [1],  # Default category
    "tags": [tag_ids_for_topics],
    "status": "publish",
    "meta": {
        "_yoast_wpseo_metadesc": article['metadata']['meta_description'],
        "_yoast_wpseo_focuskw": article['metadata']['seo_keywords'][0]
    }
}

result = await wp_client.create_post(post_data)
post_id = result['id']
post_url = result['link']
```

### Endpoint API

```python
# src/api/publishing.py

from fastapi import APIRouter, HTTPException
from src.workers.publishing_tasks import publish_article_task

router = APIRouter(prefix="/tasks", tags=["publishing"])

@router.post("/{task_id}/publish_article")
async def publish_article_to_wordpress(
    task_id: str,
    blog_category: Optional[str] = "Book Reviews",
    draft_mode: bool = False,
    article_repo: ArticleRepository = Depends(get_article_repo),
    submission_repo: SubmissionRepository = Depends(get_submission_repo),
):
    """
    Publish article to WordPress.
    
    Args:
        task_id: Submission ID
        blog_category: WordPress category (optional, default: "Book Reviews")
        draft_mode: If True, create as draft instead of publish
    """
    try:
        # Get article
        submission = await submission_repo.get_by_id(ObjectId(task_id))
        if not submission:
            raise HTTPException(404, "Submission not found")
        
        # Get latest article for this submission
        articles = await article_repo.list_by_submission(str(submission['_id']), limit=1)
        if not articles:
            raise HTTPException(404, "No article found for this submission")
        
        article = articles[0]
        
        # Enqueue task
        celery_task = publish_article_task.delay(
            article_id=str(article['_id']),
            category=blog_category,
            draft=draft_mode
        )
        
        return {
            "status": "queued",
            "celery_task_id": celery_task.id,
            "article_id": str(article['_id'])
        }
    
    except Exception as e:
        logger.error(f"Error queueing publication: {e}")
        raise HTTPException(500, f"Error: {str(e)}")
```

---

## 4. Databases Schemas de Suporte

### Articles (Expandido)

```javascript
// NEW FIELDS to add to current articles collection:

{
  ...existing fields...,
  
  "structure": {                    // NEW: Article structure metadata
    "h1": "String",
    "h2_count": 8,
    "sections": [
      {
        "h2": "String",
        "content": "String",
        "word_count": Number,
        "h3_count": Number,
        "h3_subsections": [...],
        "validation_status": "valid|invalid"
      }
    ],
    "total_word_count": Number,
    "last_validated_at": ISODate
  },

  "metadata": {                      // NEW: SEO & Publication metadata
    "seo_keywords": ["String"],
    "meta_description": "String",
    "featured_image_url": "String",
    "reading_time_minutes": Number,
    "tone": "academic|casual|technical"
  },

  "publishing": {                    // NEW: Publication tracking
    "status": "draft|queued|published|failed",
    "wordpress_post_id": Number,
    "wordpress_url": "String",
    "wordpress_category": "String",
    "published_at": ISODate,
    "publish_error": "String"
  },

  "versions": [                       // NEW: Article versions
    {
      "version_num": Number,
      "created_at": ISODate,
      "summary": "String (what changed)"
    }
  ]
}
```

### Summaries (Schema Completo)

Ver seção 2 acima.

### Submissions (Add Fields)

```javascript
{
  ...existing...,
  
  "pipeline_progress": {             // NEW: Track completion
    "amazon_scrape": {
      "status": "pending|in_progress|completed|failed",
      "completed_at": ISODate,
      "error": "String"
    },
    "goodreads_scrape": { ... },
    "author_scrape": { ... },
    "link_finding": { ... },
    "context_generation": { ... },
    "topic_extraction": { ... },
    "article_generation": { ... },
    "wordpress_publishing": { ... }
  },
  
  "estimated_completion": ISODate    // NEW: ETA based on pipeline
}
```

---

## Updates em Migrations

```python
# src/db/migrations.py - ADD estes índices:

# Para súmários
await db["summaries"].create_index([("book_id", ASCENDING), ("created_at", DESCENDING)])
await db["summaries"].create_index([("topics", ASCENDING)])

# Para articles (expandido)
await db["articles"].create_index([("wordpress_post_id", ASCENDING)], sparse=True)
await db["articles"].create_index([("metadata.seo_keywords", ASCENDING)])
await db["articles"].create_index([("publishing.status", ASCENDING)])

# Para submissions (agora com pipeline progress)
await db["submissions"].create_index([("pipeline_progress", ASCENDING)])
```

