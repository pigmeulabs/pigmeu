# Contexto para Agentes

Atualizado em: 2026-02-13

## 1. Objetivo

Fornecer contexto tecnico objetivo para agentes/automações operarem no repositorio sem ambiguidade sobre arquitetura, fluxos e pontos criticos.

## 2. Mapa rapido do codigo

- App/API:
  - `src/app.py`
  - `src/api/*.py`
- Modelos e validacoes:
  - `src/models/enums.py`
  - `src/models/schemas.py`
- Dados:
  - `src/db/connection.py`
  - `src/db/migrations.py`
  - `src/db/repositories.py`
- Workers:
  - `src/workers/worker.py`
  - `src/workers/scraper_tasks.py`
  - `src/workers/article_tasks.py`
  - `src/workers/publishing_tasks.py`
  - `src/workers/link_tasks.py`
  - `src/workers/article_structurer.py`
- Scrapers/integracoes:
  - `src/scrapers/*`
- Frontend:
  - `src/static/index.html`
  - `src/static/app.js`
  - `src/static/styles.css`

## 3. Fluxo operacional principal

1. `POST /submit` cria submissao.
2. `start_pipeline` inicia cadeia de scraping.
3. worker executa etapas ate gerar contexto e artigo.
4. task fica em `ready_for_review` (ou `article_generated` quando requer aprovacao).
5. `POST /tasks/{id}/publish_article` enfileira publicacao.

## 4. Estados de submissao relevantes

- `pending_scrape`
- `scraping_amazon`
- `pending_context`
- `context_generation`
- `context_generated`
- `pending_article`
- `article_generated`
- `ready_for_review`
- `approved`
- `published`
- `scraping_failed`
- `failed`

## 5. Regras de negocio criticas

- `run_immediately=false` exige `schedule_execution`.
- `amazon_url` duplicada e bloqueada.
- publish pode ser bloqueado por `user_approval_required`.
- retry por etapa apaga artefatos posteriores.

## 6. Pontos criticos para automacao

- sem auth: qualquer endpoint pode ser acionado no ambiente ativo.
- defaults de settings podem ser bootstrapados automaticamente ao chamar pipelines/submit.
- conexao Mongo e sensivel ao event loop; usar APIs/repositories padrao do projeto.
- `schedule_execution` e apenas persistido (sem scheduler nativo).

## 7. Wireframes e referencia de UX

- wireframes historicos ativos em `docs/ui-ux/wireframes/`.
- comportamento final deve ser validado contra implementacao real em `src/static/app.js`.

## 8. Resultado esperado de alteracoes

Ao alterar qualquer fluxo, garantir alinhamento simultaneo entre:

- endpoints/API
- workers/status transitions
- persistencia/repositories
- frontend (acoes e feedback)
- documentacao correspondente em `docs/`
