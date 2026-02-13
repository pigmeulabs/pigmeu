# Modulo: Settings e Configuracoes

Atualizado em: 2026-02-13
Implementacao principal: `src/api/settings.py`

## 1. Responsabilidade

Centraliza toda configuracao operacional do runtime:

- credenciais externas
- prompts de IA
- content schemas editoriais
- configuracao de pipelines e etapas
- consulta de categorias WordPress

## 2. Subdominios e endpoints

## 2.1 Credentials

- `GET /settings/credentials`
- `GET /settings/credentials/{id}`
- `POST /settings/credentials`
- `PATCH /settings/credentials/{id}`
- `DELETE /settings/credentials/{id}`

Funcionalidades:

- CRUD completo;
- filtro por `service` e `active`;
- mascaramento de `key` em respostas;
- controle de `last_used_at` para auditoria de uso.

## 2.2 WordPress categories

- `GET /settings/wordpress/categories`

Funcionalidades:

- seleciona credencial WordPress ativa (especifica ou default);
- varre categorias via REST API com paginacao;
- fallback de tentativa sem auth quando endpoint rejeita auth para leitura publica;
- devolve lista normalizada `{id, name, slug}`.

## 2.3 Prompts

- `GET /settings/prompts`
- `GET /settings/prompts/{id}`
- `POST /settings/prompts`
- `PATCH /settings/prompts/{id}`
- `DELETE /settings/prompts/{id}`
- `GET /settings/prompt-categories`

Funcionalidades:

- CRUD completo;
- filtros por categoria/provedor/purpose/nome;
- normalizacao de provider/category;
- inferencia de provider por `model_id` quando provider nao informado;
- consolidacao dinamica de categorias para UI.

## 2.4 Content Schemas

- `GET /settings/content-schemas`
- `GET /settings/content-schemas/{id}`
- `POST /settings/content-schemas`
- `PATCH /settings/content-schemas/{id}`
- `DELETE /settings/content-schemas/{id}`

Funcionalidades:

- CRUD completo de estrutura editorial;
- suporte a TOC por itens H2/H3;
- validacao de limites globais e por item;
- ativacao/desativacao de schemas.

## 2.5 Pipelines

- `GET /settings/pipelines`
- `GET /settings/pipelines/{pipeline_id}`
- `PATCH /settings/pipelines/{pipeline_id}/steps/{step_id}`

Funcionalidades:

- lista pipelines em modo card;
- detalha etapas com opcoes de AI e opcoes disponiveis de prompt/credential;
- permite alterar, por step:
  - `delay_seconds`
  - `credential_id`
  - `prompt_id`

Validacoes criticas:

- step sem AI nao aceita `credential_id`/`prompt_id`;
- `delay_seconds` inteiro entre `0` e `86400`;
- IDs de prompt/credential precisam existir.

## 3. Bootstrap automatico de defaults

Helpers internos garantem baseline ao acessar pipelines/submissoes:

- `_ensure_default_pipelines`
  - cria `book_review_v2` e `links_content_v1` se ausentes.
- `_ensure_default_credentials`
  - cria/normaliza credenciais default.
- `_ensure_default_content_schema`
  - cria schema editorial default completo.

Observacao operacional:

- defaults incluem valores de credenciais bootstrap em codigo; em ambiente produtivo e esperado substituir via configuracao segura.

## 4. Estruturas chave

## 4.1 Pipeline step AI

Cada step AI pode conter:

- `provider`
- `model_id`
- `credential_id`
- `prompt_id`
- `default_credential_name`
- `default_prompt_purpose`

## 4.2 Content schema TOC item

Campos relevantes:

- `level` (`h2`/`h3`)
- `title_template`
- `content_mode`
- `specific_content_hint`
- `min/max_paragraphs`
- `min/max_words`
- `source_fields`
- `prompt_id`
- `position`

## 5. Integracao com outros modulos

- `ingestao`
  - depende deste modulo para bootstrap de pipeline/schema/credenciais antes de criar submissao.
- `workers`
  - dependem de prompts, credenciais e pipeline step config para executar LLM.
- `frontend-dashboard`
  - usa este modulo para todos os CRUDs de configuracao e para montar opcoes dinamicas de formulario.

## 6. Falhas tratadas

- `404` para recurso inexistente (credential/prompt/schema/pipeline/step).
- `422` para payload invalido ou regra violada.
- `502` para erro remoto WordPress categories.
- `500` para falha interna.

## 7. Relevancia arquitetural

Este modulo transforma configuracao em dados versionados e editaveis, permitindo ajustar comportamento de pipeline em runtime sem alterar codigo-fonte.
