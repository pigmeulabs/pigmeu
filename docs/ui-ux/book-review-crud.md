# UI-UX: Book Review (Create/Edit)

Atualizado em: 2026-02-13
Tela: secao `#submit-section` em `src/static/index.html`
Wireframe base: `docs/ui-ux/wireframes/crud-task-book-review.png`

## 1. Objetivo da tela

Criar e editar tarefas de geracao de conteudo de book review, incluindo dados editoriais e opcoes de execucao.

## 2. Estrutura visual (wireframe)

## 2.1 Painel principal de dados (wireframe A)

Campos implementados:

- `Book Title *`
- `Author Name *`
- `Amazon Link *`
- `Additional Content Link` (lista dinamica com adicionar/remover)
- `Textual Information` (texto livre para contexto)

## 2.2 Painel de opcoes de execucao/editorial (wireframe B)

Campos implementados:

- `Run immediately` (checkbox)
- `Schedule Execution` (`datetime-local`)
- `WordPress Credential` (fonte para categorias)
- `Main Category`
- `Content Schema`
- `Article Status`
- `User approval required`

Acoes:

- `Create Task` (modo criacao)
- `Save task changes` (modo edicao)
- `Cancel Edit` (somente em modo edicao)

## 3. Fluxos suportados

## 3.1 Criacao

- submit chama `POST /submit`;
- em sucesso, form e resetado;
- dashboard e metricas sao atualizados.

## 3.2 Edicao

- tela pode ser aberta em modo edicao a partir de Task Details;
- submit chama `PATCH /tasks/{id}` com bloco `submission`;
- ao salvar, tela retorna ao modo criacao.

## 4. Validacoes de frontend

- obrigatorios: `title`, `author_name`, `amazon_url`;
- `amazon_url` deve iniciar com `http://` ou `https://`;
- links adicionais, quando preenchidos, tambem devem ser URL valida;
- se `run_immediately=false`, `schedule_execution` torna-se obrigatorio;
- no modo edicao, campos herdados de submissao base sao preservados quando nao editaveis diretamente (ex.: `goodreads_url`, `author_site`).

## 5. Integracoes dinamicas da tela

## 5.1 Credencial WordPress -> categorias

- carrega credenciais via `GET /settings/credentials?service=wordpress&active=true`;
- seleciona credencial default com preferencia por URL padrao;
- carrega categorias via `GET /settings/wordpress/categories?credential_id=...`.

## 5.2 Content schema

- carrega opcoes ativas via `GET /settings/content-schemas?active=true&target_type=book_review`;
- mantém selecao pendente ao alternar entre modos.

## 5.3 Persistencia local

- credencial WordPress selecionada e persistida em `localStorage` para reutilizacao.

## 6. Diferencas frente ao wireframe

Mantido:

- divisao em dois paineis (dados da tarefa + opcoes de execucao).
- foco em criacao rapida de nova task.

Extendido:

- selecao de credencial WordPress e carregamento de categorias em tempo real;
- selecao de content schema;
- modo de edicao completo reutilizando a mesma tela;
- lista dinamica de links adicionais com controle de visibilidade de botao remover.
