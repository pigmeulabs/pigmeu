# UI-UX: Detalhe da Task e Acoes de Fluxo

Atualizado em: 2026-02-13
Tela: secao `#task-details-section` em `src/static/index.html`
Wireframe base: `docs/ui-ux/wireframes/taskdetails.png`

## 1. Objetivo da tela

Permitir controle fino da execucao da task, com visibilidade de progresso por etapa e acoes operacionais diretamente no fluxo.

## 2. Estrutura da tela

## 2.1 Cabecalho da task (wireframe A)

Exibe:

- nome do pipeline/task (titulo principal)
- acoes globais:
  - gerar artigo (quando permitido)
  - ver artigo final
  - editar task
  - deletar task

## 2.2 Metadados de execucao (wireframe B)

Exibe:

- livro
- autor
- data de criacao
- ultimo update

## 2.3 Progresso visual do pipeline (wireframe C)

Componente timeline mostra cada etapa com estado:

- `to_do`
- `current`
- `processed`
- `failed`

A definicao de etapas vem de:

- `task.pipeline.steps` quando existe;
- fallback para fluxo padrao (`amazon_scrape` -> `ready_for_review`) quando pipeline detalhado nao esta disponivel.

## 2.4 Lista de etapas (wireframe D)

Para cada etapa a UI mostra:

- nome da etapa
- badge de estado
- botao `Retry`
- botao `View Content`

## 2.5 Acoes por etapa (wireframe E)

- `Retry`
  - chama `POST /tasks/{id}/retry_step` com `stage` correspondente;
  - exibe confirmacao explicando descarte de etapas posteriores;
  - aplica atualizacao otimista na timeline antes do refresh definitivo.
- `View Content`
  - abre painel de visualizacao com conteudo relacionado a etapa:
    - JSON (metadados/summaries/research)
    - markdown renderizado (contexto/artigo)

## 3. Mapeamento de conteudo por etapa

A funcao `getStepContent()` faz o binding:

- `amazon_scrape` -> `book.extracted`
- `additional_links_scrape` -> links configurados + totais processados + candidatos bibliograficos
- `summarize_additional_links` -> `summaries`
- `consolidate_book_data` -> `extracted.consolidated_bibliographic`
- `internet_research` -> `extracted.web_research`
- `context_generation` -> `knowledge_base.markdown_content`
- `article_generation` / `ready_for_review` -> `draft.content` ou `article.content`

## 4. Acoes globais e regras

## 4.1 Gerar artigo manualmente

Botao aparece apenas quando:

- contexto existe (`knowledge_base.markdown_content`);
- nao existe artigo/draft ja gerado;
- task nao esta em `pending_article`/`article_generation`.

Acao:

- chama `POST /tasks/{id}/generate_article`.

## 4.2 Ver artigo final

- renderiza markdown final em viewer dedicado;
- prioriza `article.content`, com fallback para `draft.content`.

## 4.3 Editar task

- abre fluxo de edicao reaproveitando formulario Book Review na secao de submit.

## 4.4 Deletar task

- confirmacao obrigatoria;
- chama `DELETE /tasks/{id}`;
- retorna para dashboard e atualiza metricas/listagem.

## 5. Feedback e resiliencia de UX

- mensagens transientes de sucesso/erro no bloco `task-action-result`.
- re-fetch automatico apos comandos assicronos para sincronizar estado real.
- fallback visual quando conteudo da etapa ainda nao existe.

## 6. Diferencas frente ao wireframe

Mantido:

- cabecalho, metadados, progresso linear e acoes por etapa.

Extendido na implementacao:

- renderizador de conteudo por etapa (JSON/markdown);
- retry com update otimista da timeline;
- acoes globais extras (editar/deletar/gerar artigo manual);
- alinhamento com pipeline dinamico configurado em `settings/pipelines`.
