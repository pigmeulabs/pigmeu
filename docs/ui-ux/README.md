# UI-UX

Atualizado em: 2026-02-13
Implementacao principal: `src/static/index.html`, `src/static/app.js`, `src/static/styles.css`

## 1. Objetivo

Consolidar a documentacao de interface operacional do sistema, relacionando:

- wireframes historicos;
- comportamento real implementado em frontend;
- contratos de API utilizados por cada tela.

## 2. Documentos por modulo de interface

- Dashboard e Lista de Tasks
  - `docs/ui-ux/dashboard-tasks.md`
- Detalhe da Task e Acoes de Fluxo
  - `docs/ui-ux/task-details.md`
- Book Review CRUD (create/edit de submissao)
  - `docs/ui-ux/book-review-crud.md`
- Credentials CRUD
  - `docs/ui-ux/credentials-crud.md`
- Prompts CRUD
  - `docs/ui-ux/prompts-crud.md`
- Content Schemas CRUD
  - `docs/ui-ux/content-schemas-crud.md`
- Pipelines Config
  - `docs/ui-ux/pipelines-config.md`

## 3. Wireframes historicos incorporados

Diretorio: `docs/ui-ux/wireframes/`

- `crud-task-book-review.png`
- `taskdetails.png`
- `crud-credenciais.png`
- `crud-credenciais-modal.png`
- `crud-prompts.png`
- `crud-prompts-modal.png`
- `wireframes.drawio`

## 4. Correspondencia geral wireframe -> implementacao

- Book Review:
  - formulario principal + painel de opcoes mantidos;
  - adicionados campos de schema e fonte de categoria WordPress.
- Task Details:
  - cabecalho, metadados e linha de progresso mantidos;
  - adicionadas acoes de retry/view por etapa com conteudo dinamico.
- Credentials:
  - listagem de cards/acoes e modal de cadastro implementados;
  - inclui alternancia ativo/inativo e refresh de categorias WordPress.
- Prompts:
  - listagem com acoes e modal de edicao implementados;
  - inclui filtros por categoria/provedor e configuracao de output format.

## 5. Escopo atual da UI

Implementado:

- tasks, task details, book review, credentials, prompts, content schemas, pipelines.

Placeholder (sem fluxo funcional completo):

- analytics, articles, social media, seo tools, settings geral, logout.

## 6. Caracteristicas transversais de UX

- feedback de estado (`loading`, sucesso, erro) em todas as areas principais;
- acoes destrutivas com confirmacao;
- acessibilidade basica com `aria-label`, focus e navegacao por teclado em cards;
- persistencia de preferencias locais (sidebar colapsada, credencial WordPress preferida);
- renderizacao responsiva para diferentes larguras de viewport.
