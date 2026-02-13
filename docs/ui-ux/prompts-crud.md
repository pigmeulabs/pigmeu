# UI-UX: CRUD de Prompts

Atualizado em: 2026-02-13
Tela: secao `#prompts-section` + modal `#prompt-modal`
Wireframes base:

- `docs/ui-ux/wireframes/crud-prompts.png`
- `docs/ui-ux/wireframes/crud-prompts-modal.png`

## 1. Objetivo da tela

Gerenciar prompts que direcionam comportamento das etapas de IA no pipeline.

## 2. Lista de prompts

## 2.1 Estrutura do card (wireframe A)

Exibe:

- nome
- descricao curta/purpose
- categoria
- provider/model
- trecho do system prompt
- status ativo/inativo

## 2.2 Acoes de card (wireframe B)

- editar
- ativar/desativar
- excluir

## 2.3 Acao global (wireframe D)

- `Create Prompt` abre modal de criacao.

## 2.4 Filtros da lista

- categoria
- provider
- busca por nome (debounce)

## 3. Modal Add/Edit Prompt

Campos implementados por grupos (alinhado ao wireframe modal):

## 3.1 Identificacao do prompt (wireframe A)

- `Prompt Name *`
- `Purpose`
- `Category`
- `Short Description`

## 3.2 Configuracao tecnica de modelo (wireframe B)

- `Provider`
- `Model`
- `Temperature`
- `Max Tokens`

## 3.3 Conteudo do prompt (wireframe C)

- `System Prompt *`
- `User Prompt *`
- `Expected Output Format`
- `Active`

## 4. Validacoes de frontend

- obrigatorios:
  - `name`
  - `purpose`
  - `category`
  - `provider`
  - `system_prompt`
  - `user_prompt`
- normalizacao:
  - provider em lowercase;
  - defaults de category/provider/model quando necessario.

## 5. Endpoints usados

- categorias: `GET /settings/prompt-categories`
- listagem: `GET /settings/prompts` (com query de filtro)
- criar: `POST /settings/prompts`
- editar/toggle: `PATCH /settings/prompts/{id}`
- excluir: `DELETE /settings/prompts/{id}`

## 6. Integracoes com outras telas

- prompts aparecem como opcoes em:
  - editor de content schema (por item TOC)
  - configuracao de steps de pipeline
- alteracoes de prompt impactam runtime de workers sem redeploy.

## 7. Mapeamento wireframe -> implementacao

- expand/recolher card (wireframe C da listagem): implementacao atual usa card resumido clicavel para abrir modal, mantendo listagem compacta.
- grupo de acoes do prompt (wireframe B): mantido via botoes edit/toggle/delete.
- modal com identificacao + config tecnica + conteudo: implementado integralmente.

## 8. Diferencas frente ao wireframe

- implementacao adiciona filtros dinamicos por categoria/provider.
- UI usa icones de acao com suporte de acessibilidade sem alterar a semantica do fluxo.
