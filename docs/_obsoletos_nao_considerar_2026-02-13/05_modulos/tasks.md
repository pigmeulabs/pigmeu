# Módulo Tasks

## Responsabilidade

Gerenciar ciclo de vida da submission e operações do pipeline, incluindo a interface de criação de task em Book Review.

## Endpoints

- `GET /tasks`
- `GET /tasks/{submission_id}`
- `PATCH /tasks/{submission_id}`
- `POST /tasks/{submission_id}/generate_context`
- `POST /tasks/{submission_id}/generate_article`
- `POST /tasks/{submission_id}/retry`
- `POST /tasks/{submission_id}/draft_article`
- `POST /tasks/{submission_id}/publish_article`
- `GET /tasks/stats`
- `POST /submit`

## Interface de Nova Task (wireframe)

### Bloco principal
- `Book Title` (obrigatório)
- `Author name` (obrigatório)
- `Amazon Link` (obrigatório)
- `Additional Content Link` (dinâmico, opcional)
- `Textual information` (opcional)

### Painel de opções
- `Run immediately`
- `Schedule execution` (obrigatório se `run_immediately=false`)
- `Main Category`
- `Article Status`
- `User approval required`

## Repositórios envolvidos

- `SubmissionRepository`
- `BookRepository`
- `KnowledgeBaseRepository`
- `ArticleRepository`

## Integração com workers

- Entrada: `start_pipeline` (Celery)
- Contexto: `generate_context_task`
- Artigo: `generate_article_task`
- Publicação: `publish_article_task`

## Metadados extraídos da Amazon

Campos esperados em `books.extracted` no step de scraping Amazon:

- `title`
- `original_title`
- `authors`
- `language`
- `original_language`
- `edition`
- `average_rating`
- `pages`
- `publisher`
- `publication_date`
- `asin`
- `isbn_10`
- `isbn_13`
- `price`
- `ebook_price`
- `cover_image_url`
- `amazon_url`

Referência detalhada de extração (CSS/XPath/JSPath por campo):
- `docs/_arquivo_historico/legado/requirements/SSR.md` (seção `RF-011A`)

## Regras relevantes

- Retry limpa erros e volta status para `pending_scrape`.
- Publicação com aprovação exigida só aceita status `approved` ou `ready_for_review`.
- Draft exige `content` não vazio.
- `amazon_url` duplicada deve ser rejeitada no create.
