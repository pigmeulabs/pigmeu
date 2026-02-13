# Modulo: Gestao de Tasks

Atualizado em: 2026-02-13
Implementacao principal: `src/api/tasks.py`

## 1. Responsabilidade

Modulo central de operacao do lifecycle de submissao. Ele oferece leitura operacional consolidada e comandos de controle do pipeline (geracao, retry, delete, publish, edicao).

## 2. Superficie funcional

## 2.1 Leitura e observabilidade

- `GET /tasks/health`
- `GET /tasks/stats`
- `GET /tasks`
- `GET /tasks/{submission_id}`

## 2.2 Comandos de controle

- `POST /tasks/{id}/generate_context`
- `POST /tasks/{id}/generate_article`
- `POST /tasks/{id}/retry`
- `POST /tasks/{id}/retry_step`
- `POST /tasks/{id}/draft_article`
- `POST /tasks/{id}/publish_article`

## 2.3 Gestao de dados

- `PATCH /tasks/{id}`
- `DELETE /tasks/{id}`

## 3. Dados agregados no detalhe de task

`GET /tasks/{id}` retorna um agregado operacional composto por:

- `submission`
- `book`
- `summaries`
- `knowledge_base`
- `article`
- `draft`
- `progress`
- `pipeline`

Esse agregado e o payload principal consumido pelo frontend para timeline, acoes por etapa e visualizacao de conteudo intermediario.

## 4. Retry por etapa: regra e limpeza

O modulo implementa retry fino com normalizacao de aliases de etapa e limpeza de artefatos posteriores.

## 4.1 Aliases aceitos (exemplos)

- `pending_scrape` -> `amazon_scrape`
- `pending_context` -> `context_generation`
- `pending_article` e `ready_for_review` -> `article_generation`

## 4.2 Limpeza por etapa

- `amazon_scrape`
  - remove `book`, `summaries`, `knowledge_base`, `articles`, `drafts`.
- `additional_links_scrape` / `summarize_additional_links`
  - remove `summaries`, `knowledge_base`, `articles`, `drafts`;
  - limpa campos de links/consolidacao/web_research em `books.extracted`.
- `consolidate_book_data`
  - remove `knowledge_base`, `articles`, `drafts`;
  - limpa consolidacao e web_research em `books.extracted`.
- `internet_research`
  - remove `knowledge_base`, `articles`, `drafts`;
  - limpa `web_research`.
- `context_generation`
  - remove `knowledge_base`, `articles`, `drafts`.
- `article_generation`
  - remove `articles`, `drafts`.

## 4.3 Re-enfileiramento

Cada etapa limpa e dispara sua task correspondente:

- `amazon_scrape` -> `scrape_amazon_task`
- `additional_links_scrape` / `summarize_additional_links` -> `process_additional_links_task`
- `consolidate_book_data` -> `consolidate_bibliographic_task`
- `internet_research` -> `internet_research_task`
- `context_generation` -> `generate_context_task`
- `article_generation` -> `generate_article_task`

## 5. Publicacao e governanca editorial

`POST /tasks/{id}/publish_article` valida pre-condicoes antes de enfileirar publicacao.

Regra critica:

- se `user_approval_required=true`, somente publica quando status da submissao estiver em `approved` ou `ready_for_review`.

## 6. Progresso de task

O modulo monta progresso simplificado com macro-etapas:

- `pending_scrape`
- `pending_context`
- `pending_article`
- `ready_for_review`

Tambem aplica alias de status para manter visualizacao coerente na UI.

## 7. Dependencias tecnicas

- repositories:
  - `SubmissionRepository`, `BookRepository`, `SummaryRepository`, `KnowledgeBaseRepository`, `ArticleRepository`, `PipelineConfigRepository`
- workers:
  - `start_pipeline`
  - tasks de `scraper_tasks`, `article_tasks`, `publishing_tasks`

## 8. Erros e protecoes relevantes

- `404` quando submissao/book/artigo inexistentes.
- `422` para stage invalida no retry_step ou payload invalido.
- `400` para tentativa de publish sem aprovacao quando exigido.
- `500` em falha de enqueue/processamento interno.

## 9. Papel no sistema

Este modulo e o hub operacional do produto. Ele conecta estados de dados, aciona workers e fornece a visao consolidada usada pelo dashboard para tomada de decisao em tempo real.
