# Módulo Prompts

## Responsabilidade

Armazenar e versionar instruções de LLM usadas no pipeline.

## Entidade

- Coleção: `prompts`
- Campos principais:
  - `name`
  - `purpose`
  - `short_description`
  - `system_prompt`
  - `user_prompt`
  - `model_id`, `temperature`, `max_tokens`
  - `active`, `version`

## Endpoints

- `GET /settings/prompts`
- `GET /settings/prompts/{prompt_id}`
- `POST /settings/prompts`
- `PATCH /settings/prompts/{prompt_id}`
- `DELETE /settings/prompts/{prompt_id}`

## Uso no pipeline

- Contexto: busca por `purpose=context` ou nome padrão.
- Tópicos: prompt `Topic Extractor for Books`.
- Artigo: prompt `SEO-Optimized Article Writer`.
- Links externos: `purpose=summarization`/`link_summarization` ou nome `Link Summarizer`.

## Scripts relacionados

- `scripts/seed_prompts.py`: carga inicial de prompts.
- `scripts/check_prompts.py`: verificação de estado.
