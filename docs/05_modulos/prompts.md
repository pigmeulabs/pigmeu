# Módulo Prompts

## Responsabilidade

Armazenar e versionar instruções de LLM usadas no pipeline, com configuração técnica aderente à UI de wireframes.

## Entidade

- Coleção: `prompts`
- Campos principais:
  - `name`
  - `short_description`
  - `purpose`
  - `provider`
  - `credential_id`
  - `model_id`
  - `temperature`
  - `max_tokens`
  - `system_prompt`
  - `user_prompt`
  - `active`, `version`

## Endpoints

- `GET /settings/prompts`
- `GET /settings/prompts/{prompt_id}`
- `POST /settings/prompts`
- `PATCH /settings/prompts/{prompt_id}`
- `DELETE /settings/prompts/{prompt_id}`

Endpoints auxiliares para a UI:
- `GET /settings/providers`
- `GET /settings/providers/{provider}/models`
- `GET /settings/credentials?service={provider}&active=true`

## Interface (wireframes)

### Listagem
- Cards com `name`, `short_description` e status `active`.
- Ações por card: `active/inactive`, `edit`, `delete`, `expand/collapse`.
- Em modo expandido, exibir `system_prompt` e `user_prompt` completos.
- Botão primário: `Create Prompt`.

### Modal
- Identificação:
  - `Prompt name` (obrigatório)
  - `Short description` (obrigatório)
- Configuração técnica:
  - `Provider` (obrigatório)
  - `Credential` (obrigatório, dependente de `Provider`)
  - `Model` (obrigatório, dependente de `Provider`)
  - `Temperature` (obrigatório)
  - `Max Tokens` (obrigatório)
- Conteúdo:
  - `System Prompt` (obrigatório)
  - `User Prompt` (obrigatório)

## Uso no pipeline

- Contexto: busca por `purpose=context` ou nome padrão.
- Tópicos: prompt de extração de tópicos.
- Artigo: prompt de geração de artigo.
- Links externos: prompt de sumarização.

## Scripts relacionados

- `scripts/seed_prompts.py`: carga inicial de prompts.
- `scripts/check_prompts.py`: verificação de estado.
