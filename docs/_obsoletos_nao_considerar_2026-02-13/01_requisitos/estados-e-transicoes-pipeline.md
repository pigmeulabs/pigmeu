# Estados e Transições do Pipeline

## Estados de submission

- `pending_scrape`
- `scraping_amazon`
- `scraping_goodreads`
- `scraped`
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

## Fluxo principal

1. `pending_scrape` (criação da submission)
2. `scraping_amazon`
3. `scraping_goodreads`
4. `context_generation`
5. `context_generated`
6. `pending_article`
7. `article_generated`
8. `ready_for_review`
9. `published`

## Transições por ação/evento

- `POST /submit` com `run_immediately=true`:
  - cria submission em `pending_scrape`
  - enfileira `start_pipeline`

- Worker `scrape_amazon_task`:
  - `pending_scrape -> scraping_amazon -> scraping_goodreads`

- Worker `scrape_goodreads_task`:
  - mantém `scraping_goodreads`
  - ao final: `-> context_generation`
  - em paralelo, pode enfileirar `find_and_summarize_links`

- `POST /tasks/{id}/generate_context` ou worker:
  - `-> context_generation -> context_generated`

- `POST /tasks/{id}/generate_article` ou worker:
  - `-> pending_article -> article_generated`
  - se `user_approval_required=false`: `article_generated -> ready_for_review`

- `POST /tasks/{id}/publish_article`:
  - valida pré-condições
  - enfileira publicação
  - worker atualiza para `published`

- `POST /tasks/{id}/retry`:
  - força `-> pending_scrape` e reenfileira pipeline.

## Regras de aprovação/publicação

- Se `user_approval_required=true`, endpoint de publicação exige status `approved` ou `ready_for_review`.
- Não existe endpoint dedicado para `approve`; a mudança pode ser feita por atualização manual do status.

## Observação sobre agendamento

- `schedule_execution` é persistido quando `run_immediately=false`.
- Não há scheduler nativo implementado para disparo automático na data/hora.
