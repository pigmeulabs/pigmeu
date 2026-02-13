# Modulo: Dashboard Frontend

Atualizado em: 2026-02-13
Implementacao principal: `src/static/index.html`, `src/static/app.js`, `src/static/styles.css`

## 1. Responsabilidade

Oferecer interface operacional unica para monitorar e controlar o sistema sem acessar banco, shell ou ferramentas externas.

## 2. Estrutura da interface

## 2.1 Navegacao lateral

Itens principais:

- `Tasks` (ativo por default)
- `Content Copilot > Book Review`
- `Settings > Credentials`
- `Settings > Content Schemas`
- `Settings > Prompts`
- `Settings > Pipelines`

Itens atualmente placeholder:

- Analytics
- Articles
- Social Media
- SEO Tools
- Settings (geral)
- Logout

## 2.2 Secoes funcionais implementadas

- Dashboard de tasks
- Task details
- Formulario Book Review (create/edit)
- Credentials CRUD (modal)
- Prompts CRUD (modal)
- Content Schemas CRUD (painel editor)
- Pipelines configuracao por step

## 3. Integracao API por area

- Dashboard/tasks:
  - `/stats`
  - `/tasks`
  - `/tasks/{id}`
  - `/tasks/{id}/retry_step`
  - `/tasks/{id}/generate_article`
  - `/tasks/{id}` (PATCH/DELETE)
- Book Review:
  - `/submit`
  - `/tasks/{id}` (PATCH em modo edicao)
  - `/settings/credentials?service=wordpress&active=true`
  - `/settings/wordpress/categories`
  - `/settings/content-schemas?active=true&target_type=book_review`
- Credentials:
  - `/settings/credentials*`
- Prompts:
  - `/settings/prompts*`
  - `/settings/prompt-categories`
- Content Schemas:
  - `/settings/content-schemas*`
  - `/settings/prompts` (opcoes de prompt por item TOC)
- Pipelines:
  - `/settings/pipelines`
  - `/settings/pipelines/{pipeline_id}`
  - `/settings/pipelines/{pipeline_id}/steps/{step_id}`
- Health UI:
  - `/health`

## 4. Comportamentos de UX implementados

- sidebar colapsavel com persistencia em `localStorage`.
- busca com debounce (tasks e prompts).
- paginação de tasks (`skip/limit`).
- feedback visual padronizado (`form-result success/error`).
- cards clicaveis com acessibilidade de teclado (`Enter`/`Space`).
- botoes com icones e labels acessiveis (`aria-label`, `title`, `sr-only`).
- timeline de task dinamica baseada em `pipeline.steps` quando disponivel.

## 5. Task details: comportamento operacional

- calcula estado por etapa (`to_do`, `current`, `processed`, `failed`) usando:
  - status da submissao
  - `current_step`
  - artefatos existentes (`book`, `summaries`, `kb`, `article`).
- permite por etapa:
  - `Retry`
  - `View Content` (JSON ou markdown)
- permite acoes globais:
  - gerar artigo (se contexto pronto e sem artigo)
  - ver artigo final
  - editar task
  - excluir task

## 6. CRUD e validacoes de frontend

## 6.1 Book Review

- valida campos obrigatorios e formato URL.
- exige agendamento quando `run_immediately=false`.
- suporta links adicionais dinamicos (+/-).
- suporta modo edicao reaproveitando o formulario de criacao.

## 6.2 Credentials

- exige `service`, `name`, `key` na criacao.
- exige `url` para credencial WordPress.
- toggle ativo/inativo por PATCH.

## 6.3 Prompts

- exige `name`, `purpose`, `category`, `provider`, `system_prompt`, `user_prompt`.
- filtros por categoria/provedor/nome.
- categorias e provedores dinamicos conforme dados retornados.

## 6.4 Content Schemas

- exige nome e pelo menos um item TOC.
- valida inteiros nao-negativos.
- valida relacoes `min <= max` em palavras/paragrafos e total global.
- permite vincular prompt por item TOC.

## 6.5 Pipelines

- carrega cards e detalhe por clique.
- por step permite salvar:
  - `delay_seconds`
  - `credential_id` (se AI)
  - `prompt_id` (se AI)
- valida `delay_seconds` no cliente antes de enviar.

## 7. Estado visual e estilo

- design baseado em cards/paineis com sidebar fixa.
- estilos responsivos para desktop/tablet/mobile.
- bloco de timeline e estado por badge de etapa.
- arquivo CSS contem tokens e secoes organizadas por dominio visual.

## 8. Divergencias wireframe x implementacao

- wireframes cobrem principalmente Book Review, Task Details, Credentials e Prompts.
- implementacao atual estende com:
  - content schemas CRUD completo;
  - configuracao detalhada de pipelines;
  - actions icon-only e controles de acessibilidade;
  - placeholders de modulos ainda nao implementados.

## 9. Limitacoes atuais

- nao ha autenticacao/controle de sessao.
- nao ha roteamento SPA profundo por URL (navegacao por secao in-memory).
- modulos de menu fora do escopo continuam em estado "coming soon".
