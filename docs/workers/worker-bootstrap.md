# Worker: Bootstrap Celery

Atualizado em: 2026-02-13
Implementacao: `src/workers/worker.py`

## 1. Responsabilidade

Inicializar o app Celery, registrar modulos de task e expor entrypoints base do pipeline assicrono.

## 2. Configuracao Celery

Parametros relevantes:

- broker/backend: `REDIS_URL`
- serializer: JSON
- `task_track_started=true`
- `task_time_limit=30 min`
- `task_ignore_result=true`
- timezone: UTC

## 3. Registro de modulos de task

Importa no startup para garantir registro de `shared_task`:

- `src.workers.scraper_tasks`
- `src.workers.article_tasks`
- `src.workers.publishing_tasks`
- `src.workers.link_tasks`

## 4. Tasks expostas diretamente

## 4.1 `ping`

- uso: health simples de worker.
- retorno: `pong`.

## 4.2 `start_pipeline`

Entrada:

- `submission_id`
- `amazon_url`
- `pipeline_id` (default `book_review_v2`)

Comportamento:

- chama `start_scraping_pipeline` em `scraper_tasks`.
- retorna status resumido (`started` ou `error`).

## 5. Papel no fluxo

- e o ponto de entrada padrao para iniciar processamento apos `POST /submit` com execucao imediata.
- desacopla endpoint HTTP da cadeia de scraping/contexto/artigo.

## 6. Dependencias

- `src/config.py` para `redis_url`
- tasks dos modulos workers importados
