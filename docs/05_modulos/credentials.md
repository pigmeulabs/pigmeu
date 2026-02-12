# Módulo Credentials

## Responsabilidade

Gerenciar credenciais de integrações externas (LLM/WordPress e outras previstas no enum).

## Entidade

- Coleção: `credentials`
- Campos-chave: `service`, `name`, `key`, `username_email`, `active`, `last_used_at`

## Endpoints

- `GET /settings/credentials`
- `GET /settings/credentials/{cred_id}`
- `POST /settings/credentials`
- `PATCH /settings/credentials/{cred_id}`
- `DELETE /settings/credentials/{cred_id}`

## Comportamento

- A chave é mascarada nas respostas (`****` ou prefixo/sufixo).
- O worker de publicação atualiza `last_used_at` ao usar credencial WordPress ativa.
- Filtros disponíveis: `service` e `active`.

## Serviços suportados (enum)

- `openai`
- `groq`
- `mistral`
- `claude`
- `wordpress`
- `amazon_pa_api`
