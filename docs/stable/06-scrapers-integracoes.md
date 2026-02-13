# Scrapers e Integrações

**Versão:** 0.1.0  
**Última Atualização:** 2026-02-14

---

## 1. Visão Geral

O sistema possui módulos de scraping para extrair dados de múltiplas fontes, além de integrações com serviços externos como LLMs e WordPress.

### 1.1 Módulos de Scraping

| Módulo | Fonte | Dados Extraídos |
|--------|-------|-----------------|
| `amazon.py` | Amazon | Metadados do livro |
| `goodreads.py` | Goodreads | Ratings, reviews, gêneros |
| `web_scraper.py` | Genérico | Conteúdo de páginas web |
| `link_finder.py` | Web | Descoberta de links relacionados |
| `extractors.py` | - | Utilitários de extração |
| `proxy_manager.py` | - | Gerenciamento de proxies |

### 1.2 Integrações Externas

| Integração | Tipo | Uso |
|------------|------|-----|
| OpenAI | LLM API | Geração de artigos |
| Groq | LLM API | Contexto, resumos |
| Mistral | LLM API | Extração de dados |
| WordPress | REST API | Publicação de artigos |

---

## 2. Amazon Scraper

**Arquivo:** [`src/scrapers/amazon.py`](../../src/scrapers/amazon.py)

### 2.1 Visão Geral

O Amazon Scraper utiliza **Playwright** para renderização JavaScript e **BeautifulSoup** para parsing HTML.

```python
class AmazonScraper:
    """Scraper for Amazon.com book product pages."""
    
    SELECTORS = {
        "title": "#productTitle",
        "authors": "#bylineInfo span.author a.a-link-normal",
        "rating_popover": "#acrPopover",
        "price_container": "#corePriceDisplay_desktop_feature_div",
        "cover_image": "#landingImage",
        # ...
    }
    
    ASIN_PATTERN = re.compile(r'/dp/([A-Z0-9]{10})')
```

### 2.2 Dados Extraídos

| Campo | Seletor/Fonte | Descrição |
|-------|---------------|-----------|
| `title` | `#productTitle` | Título do livro |
| `authors` | `#bylineInfo .author a` | Lista de autores |
| `asin` | URL parsing | Amazon Standard ID |
| `isbn_10` | Detail bullets | ISBN-10 |
| `isbn_13` | Detail bullets | ISBN-13 |
| `price_book` | Price container | Preço do livro físico |
| `price_ebook` | Kindle swatch | Preço do ebook |
| `rating` | `#acrPopover` | Rating (0-5) |
| `rating_count` | `#acrCustomerReviewText` | Número de avaliações |
| `pages` | Detail bullets | Número de páginas |
| `language` | Detail bullets | Idioma |
| `publisher` | Detail bullets | Editora |
| `publication_date` | Detail bullets | Data de publicação |
| `cover_image_url` | `#landingImage` | URL da capa |
| `description` | Product description | Descrição do livro |

### 2.3 Uso

```python
from src.scrapers.amazon import AmazonScraper

async def scrape_book(url: str):
    scraper = AmazonScraper(
        rate_limiter=RateLimiter(requests_per_second=0.5),
        proxy_rotator=ProxyRotator(),
        user_agent_rotator=UserAgentRotator(),
    )
    
    await scraper.initialize()
    try:
        data = await scraper.scrape(url)
        return data
    finally:
        await scraper.cleanup()
```

### 2.4 Rate Limiting

```python
rate_limiter = RateLimiter(
    requests_per_second=0.5,  # 1 request a cada 2 segundos
    requests_per_hour=100.0,   # Máximo 100 requests/hora
)
```

### 2.5 Retry com Backoff

```python
config = RequestConfig(
    max_retries=3,
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    base_delay_seconds=2.0,
    max_delay_seconds=60.0,
    retry_on_status_codes=[429, 500, 502, 503, 504],
)
```

---

## 3. Goodreads Scraper

**Arquivo:** [`src/scrapers/goodreads.py`](../../src/scrapers/goodreads.py)

### 3.1 Dados Extraídos

| Campo | Descrição |
|-------|-----------|
| `title` | Título do livro |
| `authors` | Lista de autores |
| `rating` | Rating médio (0-5) |
| `rating_count` | Número de avaliações |
| `reviews_count` | Número de reviews |
| `genres` | Lista de gêneros |
| `description` | Descrição do livro |
| `pages` | Número de páginas |
| `isbn` | ISBN |
| `asin` | ASIN (se disponível) |

### 3.2 Uso

```python
from src.scrapers.goodreads import GoodreadsScraper

async def scrape_goodreads(url: str):
    scraper = GoodreadsScraper()
    await scraper.initialize()
    try:
        data = await scraper.scrape(url)
        return data
    finally:
        await scraper.cleanup()
```

---

## 4. Web Scraper Genérico

**Arquivo:** [`src/scrapers/web_scraper.py`](../../src/scrapers/web_scraper.py)

### 4.1 Funcionalidades

- Scraping de páginas web genéricas
- Extração de texto principal
- Limpeza de HTML
- Suporte a JavaScript rendering

### 4.2 Uso

```python
from src.scrapers.web_scraper import WebScraper

async def scrape_page(url: str):
    scraper = WebScraper()
    await scraper.initialize()
    try:
        content = await scraper.scrape(url)
        return {
            "url": url,
            "title": content.get("title"),
            "text": content.get("text"),
            "links": content.get("links", []),
        }
    finally:
        await scraper.cleanup()
```

---

## 5. Link Finder

**Arquivo:** [`src/scrapers/link_finder.py`](../../src/scrapers/link_finder.py)

### 5.1 Funcionalidades

- Descoberta de links relacionados
- Busca por nome do autor
- Busca por título do livro
- Filtragem de links relevantes

### 5.2 Uso

```python
from src.scrapers.link_finder import LinkFinder

async def find_related_links(book_title: str, author_name: str):
    finder = LinkFinder()
    links = await finder.find_links(
        query=f"{book_title} {author_name} book review"
    )
    return links
```

---

## 6. Extratores

**Arquivo:** [`src/scrapers/extractors.py`](../../src/scrapers/extractors.py)

### 6.1 Funções de Extração

| Função | Uso |
|--------|-----|
| `extract_text()` | Extrai texto limpo |
| `extract_price()` | Extrai valor numérico de preço |
| `extract_isbn()` | Extrai e valida ISBN |
| `extract_rating()` | Extrai rating (0-5) |
| `extract_authors()` | Extrai lista de autores |
| `extract_date()` | Extrai e normaliza data |
| `extract_language()` | Extrai idioma |
| `clean_text()` | Limpa texto removendo caracteres especiais |
| `parse_html()` | Faz parsing de HTML com BeautifulSoup |

### 6.2 Exemplos

```python
from src.scrapers.extractors import (
    extract_text,
    extract_price,
    extract_isbn,
    extract_rating,
)

# Extrair preço
price = extract_price("R$ 89,90")  # Retorna: 89.90

# Extrair ISBN
isbn = extract_isbn("ISBN-13: 978-1449373327")  # Retorna: "9781449373327"

# Extrair rating
rating = extract_rating("4.5 out of 5 stars")  # Retorna: 4.5
```

---

## 7. Proxy Manager

**Arquivo:** [`src/scrapers/proxy_manager.py`](../../src/scrapers/proxy_manager.py)

### 7.1 Componentes

#### RateLimiter

```python
class RateLimiter:
    def __init__(
        self,
        requests_per_second: float = 1.0,
        requests_per_hour: float = 1000.0,
    ):
        ...
    
    async def wait(self):
        """Aguarda até que seja seguro fazer a próxima request."""
```

#### ProxyRotator

```python
class ProxyRotator:
    def __init__(self, proxies: List[str] = None):
        ...
    
    def get_random(self) -> Optional[str]:
        """Retorna um proxy aleatório da lista."""
    
    def mark_failed(self, proxy: str):
        """Marca um proxy como falho."""
```

#### UserAgentRotator

```python
class UserAgentRotator:
    def __init__(self, user_agents: List[str] = None):
        ...
    
    def get_random(self) -> str:
        """Retorna um User-Agent aleatório."""
```

#### BackoffStrategy

```python
class BackoffStrategy(Enum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    CONSTANT = "constant"
```

#### RequestConfig

```python
@dataclass
class RequestConfig:
    max_retries: int = 3
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    timeout_seconds: float = 30.0
    retry_on_status_codes: List[int] = field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )
```

---

## 8. Cliente LLM

**Arquivo:** [`src/workers/llm_client.py`](../../src/workers/llm_client.py)

### 8.1 Visão Geral

O cliente LLM fornece uma interface unificada para múltiplos provedores de IA.

### 8.2 Provedores Suportados

| Provedor | Modelos | SDK |
|----------|---------|-----|
| OpenAI | gpt-4, gpt-3.5-turbo | openai |
| Groq | llama-3.3-70b-versatile | groq |
| Mistral | mistral-large-latest | mistralai |
| Claude | claude-3-opus, claude-3-sonnet | anthropic |

### 8.3 Uso

```python
from src.workers.llm_client import LLMClient

client = LLMClient()

response = await client.generate(
    system_prompt="Você é um assistente especializado em livros.",
    user_prompt="Resuma o livro: {{title}}",
    model_id="gpt-4",
    temperature=0.7,
    max_tokens=2000,
    provider="openai",
    api_key="sk-...",
)
```

### 8.4 Fallback

```python
response = await client.generate(
    ...,
    allow_fallback=True,  # Permite fallback para outros provedores
)
```

Quando `allow_fallback=True`, o cliente tenta:
1. Provedor primário
2. Groq (se primário falhar)
3. Mistral (se Groq falhar)

---

## 9. Cliente WordPress

**Arquivo:** [`src/scrapers/wordpress_client.py`](../../src/scrapers/wordpress_client.py)

### 9.1 Funcionalidades

- Criação de posts
- Upload de mídia
- Gerenciamento de categorias e tags
- Autenticação via Application Password

### 9.2 Uso

```python
from src.scrapers.wordpress_client import WordPressClient

client = WordPressClient(
    url="https://seu-site.com",
    username="admin",
    password="application_password",
)

# Criar post
post = await client.create_post(
    title="Título do Artigo",
    content="Conteúdo em HTML ou Markdown",
    status="draft",  # ou "publish"
    categories=[15],
    tags=[42, 43],
    featured_image="/path/to/image.jpg",
)

print(post["link"])  # URL do post
```

### 9.3 Operações Disponíveis

| Método | Descrição |
|--------|-----------|
| `create_post()` | Cria um novo post |
| `update_post()` | Atualiza um post existente |
| `upload_media()` | Faz upload de mídia |
| `get_categories()` | Lista categorias |
| `get_tags()` | Lista tags |
| `create_category()` | Cria categoria |
| `create_tag()` | Cria tag |

---

## 10. Prompts de IA

### 10.1 Estrutura de um Prompt

```python
{
    "name": "Book Review - Article Writer",
    "purpose": "article",
    "category": "Book Review",
    "provider": "openai",
    "model_id": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2500,
    "system_prompt": "Você é um escritor especializado...",
    "user_prompt": "Escreva um artigo sobre: {{title}}\n\nContexto: {{context}}",
    "expected_output_format": "Markdown",
}
```

### 10.2 Templates de Variáveis

Variáveis disponíveis nos prompts:

| Variável | Descrição |
|----------|-----------|
| `{{title}}` | Título do livro |
| `{{author}}` | Nome do autor |
| `{{context}}` | Contexto da knowledge base |
| `{{data}}` | Dados extraídos do livro |
| `{{url}}` | URL da fonte |
| `{{content}}` | Conteúdo da página |

### 10.3 Prompts Padrão

| Purpose | Nome | Uso |
|---------|------|-----|
| `context` | Context Generator | Gera base de conhecimento |
| `article` | SEO-Optimized Article Writer | Gera artigo final |
| `book_review_link_bibliography_extract` | Link Bibliographic Extractor | Extrai dados de links |
| `book_review_link_summary` | Link Summary | Resume links |
| `book_review_web_research` | Web Research | Pesquisa web |
| `topic_extraction` | Topic Extractor | Extrai tópicos |

---

## 11. Fluxo de Integração

### 11.1 Fluxo Completo de Scraping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUXO DE SCRAPING                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. AMAZON                                                                   │
│  ┌─────────────┐                                                            │
│  │ URL Amazon  │ ──► Playwright ──► BeautifulSoup ──► Dados Extraídos       │
│  └─────────────┘                                                            │
│                                                                              │
│  2. GOODREADS (se URL fornecida)                                            │
│  ┌─────────────┐                                                            │
│  │URL Goodreads│ ──► Playwright ──► BeautifulSoup ──► Dados Extraídos       │
│  └─────────────┘                                                            │
│                                                                              │
│  3. LINKS ADICIONAIS                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                    │
│  │ Author Site │ ──► │ Other Links │ ──► │ Web Scraper │ ──► Conteúdo       │
│  └─────────────┘     └─────────────┘     └─────────────┘                    │
│                                                                      │       │
│                                                                      ▼       │
│  4. PROCESSAMENTO IA                                                  │       │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ LLM Client ──► Extrair dados bibliográficos ──► Resumos        │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│  5. CONSOLIDAÇÃO                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ Merge de dados ──► Deduplicação ──► Base de Conhecimento       │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Fluxo de Publicação WordPress

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE PUBLICAÇÃO                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. PREPARAÇÃO                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ Artigo Aprovado ──► Carregar Credenciais WordPress             │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│  2. UPLOAD DE MÍDIA                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ Imagem de Capa ──► Download ──► Upload WordPress ──► Media ID  │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│  3. CRIAÇÃO DO POST                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ Título + Conteúdo + Categorias + Tags + Featured Image          │       │
│  │                          │                                       │       │
│  │                          ▼                                       │       │
│  │              WordPress REST API                                  │       │
│  │                          │                                       │       │
│  │                          ▼                                       │       │
│  │              Post ID + URL                                       │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│  4. ATUALIZAÇÃO                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ Article.wordpress_post_id ──► Article.wordpress_url             │       │
│  │ Submission.status ──► "published"                                │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Tratamento de Erros

### 12.1 Erros de Scraping

| Erro | Tratamento |
|------|------------|
| Timeout | Retry com backoff |
| 429 Too Many Requests | Aguardar e retry |
| 403 Forbidden | Trocar proxy/user-agent |
| CAPTCHA | Marcar como falha |
| Página não encontrada | Log e continuar |

### 12.2 Erros de LLM

| Erro | Tratamento |
|------|------------|
| Rate limit | Fallback para outro provedor |
| Contexto muito longo | Truncar contexto |
| Resposta inválida | Retry com prompt mais claro |
| Timeout | Retry com timeout maior |

### 12.3 Erros de WordPress

| Erro | Tratamento |
|------|------------|
| Autenticação falhou | Verificar credenciais |
| Post já existe | Atualizar em vez de criar |
| Upload de mídia falhou | Publicar sem imagem |

---

## Próximos Passos

- [Frontend Dashboard](./07-frontend-dashboard.md)
- [Infraestrutura e Deploy](./08-infraestrutura-deploy.md)
