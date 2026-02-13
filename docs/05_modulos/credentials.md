# Módulo Credentials

## Responsabilidade

Gerenciar credenciais de integrações externas (LLM/WordPress) com foco em listagem por card e cadastro/edição via modal.

## Entidade

- Coleção: `credentials`
- Campos-chave: `service`, `name`, `key`, `username_email`, `active`, `created_at`, `last_used_at`

## Endpoints

- `GET /settings/credentials`
- `GET /settings/credentials/{cred_id}`
- `POST /settings/credentials`
- `PATCH /settings/credentials/{cred_id}`
- `DELETE /settings/credentials/{cred_id}`

## Interface (wireframes)

### Listagem
- Cards com `name`, `service`, `created_at`, `last_used_at`.
- Ações por card: `active/inactive`, `edit`, `delete`.
- Botão primário: `Create Credential`.

### Modal
- Campos:
  - `Service` (obrigatório)
  - `Credential Name` (obrigatório)
  - `API Key` (obrigatório)
  - `Username/email` (condicional)
- Comportamento:
  - Campos devem adaptar conforme `Service`.
  - Modal fecha apenas em sucesso.

## Comportamento

- A chave é mascarada nas respostas (`****` ou prefixo/sufixo).
- O worker de publicação atualiza `last_used_at` ao usar credencial WordPress ativa.
- Filtros disponíveis: `service` e `active`.

## Serviços suportados

- `openai`
- `groq`
- `mistral`
- `claude`
- `wordpress`
- `amazon_pa_api`
