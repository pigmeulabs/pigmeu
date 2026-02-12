# Especificação dos Módulos CRUD

**Projeto:** PIGMEU  
**Versão:** 1.0  
**Data:** 2026-02-12

--- 

## 1. Escopo

Este documento define as especificações e o detalhamento dos módulos:
- CRUD de Prompts
- CRUD de Credenciais
- CRUD de Tasks (submissions)

---

## 2. Módulo: CRUD de Prompts

### 2.1 Objetivo
Gerenciar os prompts utilizados pelo pipeline de geração de conteúdo (contexto, tópicos, artigo, sumarização).

### 2.2 Entidade (`prompts`)
Campos mínimos:
- `_id` (ObjectId)
- `name` (string)
- `purpose` (string)
- `short_description` (string)
- `system_prompt` (text)
- `user_prompt` (text)
- `model_id` (string)
- `temperature` (float)
- `max_tokens` (int)
- `version` (int)
- `active` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)

### 2.3 Regras de Negócio
1. `name` deve ser obrigatório.
2. `system_prompt` deve ser obrigatório.
3. `user_prompt` deve ser obrigatório.
4. Apenas prompts ativos devem ser candidatos padrão no pipeline.
5. Exclusão deve preservar rastreabilidade (remoção lógica recomendada quando necessário).

### 2.4 Operações CRUD

#### Create
- **Endpoint:** `POST /prompts`
- **Entrada mínima:**
  - `name`
  - `purpose`
  - `system_prompt`
  - `user_prompt`
- **Saída:** `prompt_id`, objeto criado.

#### Read (lista)
- **Endpoint:** `GET /prompts`
- **Suporte:** paginação, filtro por `active`, filtro por `purpose`, busca textual por nome.
- **Saída:** lista paginada + total.

#### Read (detalhe)
- **Endpoint:** `GET /prompts/{id}`
- **Saída:** objeto completo do prompt.

#### Update
- **Endpoint:** `PATCH /prompts/{id}`
- **Campos editáveis:**
  - `name`, `purpose`, `short_description`
  - `system_prompt`, `user_prompt`
  - `model_id`, `temperature`, `max_tokens`
  - `active`
- **Saída:** objeto atualizado.

#### Delete
- **Endpoint:** `DELETE /prompts/{id}`
- **Regra:** não excluir fisicamente prompt em uso ativo por policy de segurança operacional; retornar erro ou aplicar exclusão lógica.

### 2.5 Interface (UI)
A tela deve permitir:
- Botão `Create Prompt`.
- Listagem em cards com `name`, `short_description`, status (`active/inactive`) e preview de prompts.
- Ações por item: `Edit`, `Delete`, `Activate/Deactivate`, expandir/colapsar detalhes.
- Modal Add/Edit com campos:
  - `Prompt name`
  - `Short description`
  - `System Prompt`
  - `User Prompt`
  - `Save`

---

## 3. Módulo: CRUD de Credenciais

### 3.1 Objetivo
Gerenciar credenciais de serviços externos (LLM, WordPress e demais integrações).

### 3.2 Entidade (`credentials`)
Campos mínimos:
- `_id` (ObjectId)
- `service` (string)
- `name` (string)
- `secret` (string criptografada)
- `username_email` (string)
- `active` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)
- `last_used_at` (datetime)

### 3.3 Regras de Negócio
1. `service` deve ser obrigatório.
2. `name` deve ser obrigatório.
3. `secret` (API Key/token/senha) deve ser obrigatório.
4. Segredo não pode ser retornado em texto puro nas respostas.
5. Segredo não pode ser logado.
6. Deve existir controle de ativação/inativação por credencial.
7. `last_used_at` deve ser atualizado quando a credencial for utilizada pelo pipeline.

### 3.4 Operações CRUD

#### Create
- **Endpoint:** `POST /credentials`
- **Entrada mínima:**
  - `service`
  - `name`
  - `secret`
- **Entrada opcional:**
  - `username_email`
- **Saída:** `credential_id`, metadados da credencial (sem segredo em claro).

#### Read (lista)
- **Endpoint:** `GET /credentials`
- **Suporte:** paginação, filtro por `service`, filtro por `active`, busca por nome.
- **Saída:** lista paginada com metadados (sem segredo).

#### Read (detalhe)
- **Endpoint:** `GET /credentials/{id}`
- **Saída:** metadados completos (sem segredo em claro).

#### Update
- **Endpoint:** `PATCH /credentials/{id}`
- **Campos editáveis:**
  - `name`
  - `username_email`
  - `secret` (rotação)
  - `active`
- **Saída:** objeto atualizado (sem segredo em claro).

#### Delete
- **Endpoint:** `DELETE /credentials/{id}`
- **Regra:** exclusão permitida se não houver bloqueio por dependência crítica ativa.

### 3.5 Interface (UI)
A tela deve permitir:
- Botão `Create Credential`.
- Listagem com:
  - `name`
  - `service`
  - `created_at`
  - `last_used_at`
  - status (`active/inactive`)
- Ações por item: `Edit`, `Delete`.
- Modal Add/Edit com campos:
  - `Service`
  - `Credential Name`
  - `API Key`
  - `Username/email`
  - `Save`

---

## 4. Módulo: CRUD de Tasks

### 4.1 Objetivo
Gerenciar tarefas de geração de artigo review de livro e seu ciclo de vida operacional.

### 4.2 Entidade (`submissions`)
Campos mínimos:
- `_id` (ObjectId)
- `title` (string)
- `author_name` (string)
- `amazon_url` (string)
- `goodreads_url` (string)
- `author_site` (string)
- `other_links` (array<string>)
- `textual_information` (text)
- `run_immediately` (boolean)
- `schedule_execution` (datetime)
- `main_category` (string)
- `article_status` (string)
- `user_approval_required` (boolean)
- `status` (string)
- `current_step` (string)
- `attempts` (object)
- `errors` (array/object)
- `created_at` (datetime)
- `updated_at` (datetime)

### 4.3 Estados Mínimos do Pipeline
- `pending_scrape`
- `scraping_amazon`
- `scraping_goodreads`
- `context_generation`
- `context_generated`
- `pending_article`
- `article_generated`
- `ready_for_review`
- `approved`
- `published`
- `scraping_failed`

### 4.4 Regras de Negócio
1. `title`, `author_name` e `amazon_url` são obrigatórios no Create.
2. `amazon_url` deve ser validada e usada para prevenção de duplicidade.
3. Falha em Goodreads não bloqueia continuidade da geração.
4. Retry deve ser idempotente e registrar tentativas.
5. Se `user_approval_required=true`, publicação depende de aprovação.

### 4.5 Operações CRUD

#### Create
- **Endpoint:** `POST /submit`
- **Entrada obrigatória:**
  - `title`
  - `author_name`
  - `amazon_url`
- **Entrada opcional:**
  - `goodreads_url`, `author_site`, `other_links`, `textual_information`
  - `run_immediately`, `schedule_execution`
  - `main_category`, `article_status`, `user_approval_required`
- **Saída:** `submission_id`, status inicial.

#### Read (lista)
- **Endpoint:** `GET /tasks`
- **Suporte:** paginação, filtros por status e busca.
- **Saída:** lista de tasks + total.

#### Read (detalhe)
- **Endpoint:** `GET /tasks/{id}`
- **Saída:** dados da submission, progresso, erros e artefatos associados.

#### Update
- **Endpoint:** `PATCH /tasks/{id}`
- **Campos editáveis:**
  - Metadados de submissão permitidos
  - Ajustes editoriais antes de publicar
- **Saída:** objeto atualizado.

#### Delete
- **Endpoint:** `DELETE /tasks/{id}`
- **Regra:** exclusão deve ser lógica para manter trilha operacional (ex.: `deleted_at`/`archived=true`).

### 4.6 Operações Operacionais Complementares
- `POST /tasks/{id}/generate_context`
- `POST /tasks/{id}/generate_article`
- `POST /tasks/{id}/draft_article`
- `POST /tasks/{id}/publish_article`
- `POST /tasks/{id}/retry`
- `GET /stats`

### 4.7 Interface (UI)
A tela de nova task deve conter:
- `Book Title*`
- `Author name*`
- `Amazon Link*`
- `Additional Content Link (optional)` com múltiplos itens
- `Textual information (optional)`
- Painel de opções:
  - `Run immediately`
  - `Schedule execution`
  - `Main Category`
  - `Article Status`
  - `User approval required`
- Botão `Create Task`

A tela de listagem de tasks deve conter:
- Busca por texto.
- Filtro por status.
- Acesso ao detalhe.
- Ações operacionais (gerar/retry/publicar).

---

## 5. Requisitos Não Funcionais Comuns aos 3 Módulos

1. Logs estruturados com identificação da operação.
2. Controle de erros com mensagens operacionais claras.
3. Auditoria mínima de criação e atualização.
4. Paginação para listas.
5. Segurança de dados sensíveis (especialmente credenciais).
6. Compatibilidade com execução em API + workers (FastAPI/Celery).

