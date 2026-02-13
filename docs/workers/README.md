# Workers

Atualizado em: 2026-02-13

Este documento indexa os workers/tarefas assicronas do sistema. Cada arquivo detalha responsabilidades, entradas, efeitos em dados e regras de execucao.

## 1. Documentos

- Bootstrap Celery e entrada de pipeline
  - `docs/workers/worker-bootstrap.md`
- Pipeline de scraping e contexto
  - `docs/workers/scraper-tasks.md`
- Geracao de artigo
  - `docs/workers/article-tasks.md`
- Publicacao WordPress
  - `docs/workers/publishing-tasks.md`
- Descoberta/sumarizacao de links (worker auxiliar)
  - `docs/workers/link-tasks.md`

## 2. Cadeia principal de execucao

1. `start_pipeline` (entrypoint Celery)
2. `scrape_amazon_task`
3. `process_additional_links_task`
4. `consolidate_bibliographic_task`
5. `internet_research_task`
6. `generate_context_task`
7. `generate_article_task`
8. `publish_article_task` (quando acionado manualmente por endpoint)

## 3. Caracteristicas transversais

- runtime assicrono baseado em Celery + Redis.
- uso extensivo de repositories MongoDB para persistencia incremental.
- atualizacao de status/corrente de etapa em `submissions` para visibilidade na UI.
- suporte a delays configuraveis por step em `pipeline_configs`.

## 4. Observacao de escopo

- `find_and_summarize_links` (link worker) esta implementado e registrado, mas nao integra o encadeamento principal iniciado por `/submit` no estado atual.
