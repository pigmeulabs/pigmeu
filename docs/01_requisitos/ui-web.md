# UI Web

## Visão geral

A UI é uma SPA simples servida por FastAPI em `/ui`, com assets em `/ui/static`.

## Seções da interface

### 1. Tasks Dashboard
- Lista de tasks em cards.
- Busca por título/autor.
- Filtro por status.
- Paginação.
- Faixa de métricas (total, publicados, revisão, falhas, taxa de sucesso).
- Modal de detalhe com:
  - progresso da task,
  - ações de pipeline,
  - editor de artigo markdown + preview,
  - salvamento de draft,
  - publicação WordPress.

### 2. Nova Task
- Formulário com campos obrigatórios e opcionais.
- Links adicionais dinâmicos.
- Opção `Run immediately` com habilitação/desabilitação de `schedule_execution`.

### 3. Configurações
- CRUD de credenciais com ativação/inativação.
- CRUD de prompts com ativação/inativação.

## Integração UI x API

- Tasks: `/tasks`, `/tasks/{id}`, `/tasks/{id}/...`
- Submit: `/submit`
- Stats: `/stats`
- Credenciais: `/settings/credentials`
- Prompts: `/settings/prompts`
- Artigos: `/articles/{id}`

## Limitações atuais

- Sem autenticação de usuário.
- Sem autorização por perfil.
- Sem upload de mídia para WordPress pela UI.
