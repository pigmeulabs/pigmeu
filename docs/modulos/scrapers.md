# Modulo: Scrapers e Integracoes Externas

Atualizado em: 2026-02-13

## 1. Responsabilidade

Coletar dados de fontes externas e prover adaptadores de integracao para enriquecer o pipeline de conteudo.

## 2. Componentes

## 2.1 Amazon scraper (`src/scrapers/amazon.py`)

- usa Playwright + BeautifulSoup;
- valida se URL pertence a dominio Amazon (inclui dominios regionais);
- extrai metadados de livro por selectors e mapa de detalhes;
- inclui heuristicas de parse de numero, paginas, idioma, ISBN, preco e rating;
- possui retry com backoff e rate limiting.

Saida esperada:

- objeto `extracted` com campos bibliograficos usados pelo pipeline.

## 2.2 Link finder (`src/scrapers/link_finder.py`)

- busca links relacionados via DuckDuckGo HTML;
- faz fetch e parse de paginas externas;
- remove scripts/styles e compacta texto para contexto de LLM;
- possui sumarizacao auxiliar com fallback quando LLM falha.

Usado por:

- `process_additional_links_task`
- `internet_research_task`
- `find_and_summarize_links`

## 2.3 Generic web scraper (`src/scrapers/web_scraper.py`)

- scraper generico com Playwright;
- extrai metadados comuns (title/description/author/date/social links/email);
- detecta heuristica de "author website";
- extrai links de pagina.

Status no produto:

- modulo implementado e testavel, mas nao e etapa principal do encadeamento core atual.

## 2.4 Goodreads scraper (`src/scrapers/goodreads.py`)

- busca livros no Goodreads;
- extrai resultados e detalhes de pagina.

Status no produto:

- componente existente, mas nao integrado ao pipeline automatico principal.

## 2.5 WordPress client (`src/scrapers/wordpress_client.py`)

- cliente REST para categorias/tags/posts;
- resolve termo por nome e cria quando necessario;
- cria post com payload de conteudo + taxonomias + meta.

Usado por:

- `publish_article_task`.

## 2.6 Utilitarios de extracao (`src/scrapers/extractors.py`)

- normalizacao e extracao de texto;
- parse de preco/ISBN/rating/data/autores;
- helpers de parsing HTML e limpeza.

## 2.7 Controle de request (`src/scrapers/proxy_manager.py`)

- `RateLimiter`
- `ProxyRotator`
- `UserAgentRotator`
- `BackoffStrategy`
- `RequestConfig`

## 3. Dependencias externas

- Playwright (browser headless instalado)
- httpx
- BeautifulSoup
- endpoints externos (Amazon, DuckDuckGo, WordPress)

## 4. Requisitos operacionais

- ambiente deve ter browsers Playwright instalados para scrapers baseados em navegador;
- bloqueios anti-bot, mudancas de DOM e latencia externa impactam taxa de sucesso;
- integracoes remotas devem ser tratadas como falhavel por natureza.

## 5. Papel no pipeline

- fornece dados primarios e secundarios para formar `books.extracted`, `summaries` e contexto;
- sem esse modulo, o pipeline fica restrito a dados manuais e fallbacks heuristicas.

## 6. Limitacoes atuais

- scraping de fontes externas depende de estabilidade de layout remoto;
- nem todos os scrapers implementados fazem parte do fluxo principal encadeado;
- nao ha gerenciamento central de quotas por dominio alem das estrategias locais de rate limiting.
