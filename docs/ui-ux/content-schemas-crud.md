# UI-UX: CRUD de Content Schemas

Atualizado em: 2026-02-13
Tela: secao `#content-schemas-section` + painel editor `#content-schema-editor-panel`

## 1. Objetivo da tela

Permitir definicao e manutencao da estrutura editorial usada pelo gerador de artigo.

## 2. Lista de content schemas

Cada card exibe:

- nome
- descricao
- target type
- limites de palavras (min/max)
- quantidade de itens TOC
- contagem de links internos/externos
- status ativo/inativo

Acoes por card:

- editar
- ativar/desativar
- excluir

## 3. Painel editor (create/edit)

Diferente de credentials/prompts, esta tela usa painel interno em vez de modal central.

Campos globais:

- `Schema Name *`
- `Usage Type` (atualmente `book_review`)
- `Description`
- `Min Total Words`
- `Max Total Words`
- `Internal Links Count`
- `External Links Count`
- `Active`

## 4. Editor de TOC template

A tela permite construir uma lista ordenada de itens TOC.

Cada item possui:

- `Level` (`H2`/`H3`)
- `Title/Sub-title Template`
- `Content Type` (`dynamic`/`specific`)
- `Specific Content Hint`
- `Min/Max Paragraphs`
- `Min/Max Words`
- `Database Fields` (source_fields, separado por virgula)
- `Prompt` (opcional, via select de prompts)

Operacoes:

- adicionar item
- remover item
- reindexacao visual automatica (`Item 1`, `Item 2`, ...)

## 5. Validacoes de frontend

- exige pelo menos um item TOC.
- exige `title_template` em cada item.
- valida inteiros nao-negativos.
- valida regras:
  - `max_paragraphs >= min_paragraphs`
  - `max_words >= min_words`
  - `max_total_words >= min_total_words`

## 6. Endpoints usados

- listagem: `GET /settings/content-schemas`
- criar: `POST /settings/content-schemas`
- editar/toggle: `PATCH /settings/content-schemas/{id}`
- excluir: `DELETE /settings/content-schemas/{id}`
- prompt options: `GET /settings/prompts`

## 7. Integracoes com runtime

- submissao pode selecionar `content_schema_id` no Book Review.
- worker de artigo aplica esse schema para:
  - orientar geracao de secoes;
  - validar estrutura final e regras de links/palavras/paragrafos.
- pipeline pode continuar funcional mesmo sem schema selecionado (fallback).

## 8. UX e feedback

- painel editor abre com scroll para foco imediato.
- mensagens de erro/sucesso em `content-schema-form-result` e `content-schema-result`.
- se prompts nao carregarem, usuario ainda consegue salvar schema e associar prompts depois.
