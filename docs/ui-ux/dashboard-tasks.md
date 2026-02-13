# UI-UX: Dashboard e Lista de Tasks

Atualizado em: 2026-02-13
Tela: secao `#tasks-section` em `src/static/index.html`

## 1. Objetivo da tela

Oferecer visao operacional resumida de todas as submissões com:

- indicadores de saude do backlog;
- filtros rapidos;
- acesso ao detalhe da task;
- acao rapida de exclusao e visualizacao de artigo final.

## 2. Estrutura visual

- Cabecalho da secao:
  - titulo `My Tasks`
  - botao `Refresh`
- Bloco de filtros:
  - busca por titulo/autor
  - select de status
- Faixa de metricas (`stats-strip`):
  - Total
  - Published
  - Ready for Review
  - Failed
  - Success Rate
- Grade de cards (`tasks-grid`)
- Paginacao:
  - Previous
  - info de janela (ex.: `Showing 1-10 of 42`)
  - Next

## 3. Dados e endpoints utilizados

- metricas: `GET /stats`
- listagem: `GET /tasks?skip=&limit=&status=&search=`

Parametros de listagem controlados pela tela:

- `skip` (paginacao)
- `limit` (fixo em 10 no frontend)
- `status`
- `search`

## 4. Comportamento dos cards

Cada card mostra:

- titulo da task
- autor
- URL Amazon truncada
- status com cor contextual
- `updated_at`
- acoes:
  - ver artigo final (habilita apenas quando artigo/status indicam disponibilidade)
  - deletar task

Interacoes:

- clique no card abre Task Details;
- clique no botao de visualizar artigo abre Task Details com foco no viewer final;
- clique em deletar pede confirmacao e executa `DELETE /tasks/{id}`.

## 5. Feedback e estados

- Loading de metricas e tasks antes da resposta API.
- Empty state quando nao existem tasks.
- Mensagem de erro em caso de falha de request.
- desabilitacao contextual de botoes de paginacao:
  - `Previous` desabilitado no inicio;
  - `Next` desabilitado quando fim da lista e alcancado.

## 6. Regras de UX implementadas

- busca com debounce de 300ms para reduzir chamadas excessivas;
- refresh manual reseta pagina para inicio;
- mudanca de filtro de status tambem reseta pagina;
- status humanizado para leitura rapida (`pending_scrape` -> `Pending Scrape`, etc.).

## 7. Dependencias de navegacao

- ao abrir task, a navegacao marca `Tasks` como item ativo mesmo na secao de detalhes.
- a transicao para details preserva o contexto de pagina atual no dashboard.
