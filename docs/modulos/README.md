# Modulos do Sistema

Atualizado em: 2026-02-13

Este documento indexa os modulos tecnicos ativos. Cada modulo possui documento proprio com responsabilidades, fluxos, dados manipulados, endpoints/tasks envolvidos e limitacoes conhecidas.

## 1. Mapa de modulos

- Ingestao de Submissoes
  - Documento: `docs/modulos/ingestao.md`
  - Foco: entrada de comandos de trabalho e disparo inicial de pipeline.
- Gestao de Tasks
  - Documento: `docs/modulos/tasks.md`
  - Foco: acompanhamento, controle de fluxo, retry e operacao de lifecycle.
- Settings e Configuracoes
  - Documento: `docs/modulos/settings.md`
  - Foco: credenciais, prompts, schemas e pipelines configuraveis.
- Gestao de Artigos
  - Documento: `docs/modulos/articles.md`
  - Foco: atualizacao manual de artigo e metadados editoriais.
- Dashboard Frontend
  - Documento: `docs/modulos/frontend-dashboard.md`
  - Foco: UI operacional unica para tasks e configuracoes.
- Scrapers e Integracoes Externas
  - Documento: `docs/modulos/scrapers.md`
  - Foco: coleta de dados externos e adaptadores de integracao.
- Persistencia e Repositorios
  - Documento: `docs/modulos/persistencia.md`
  - Foco: conexao, migracoes, repositories e regras de consistencia.

## 2. Dependencias entre modulos

- `ingestao` depende de `settings` (bootstrap/pipeline valido) e `persistencia`.
- `tasks` depende de `persistencia`, `workers`, `scrapers` e `articles`.
- `settings` depende de `persistencia` e integra com WordPress (categorias).
- `articles` depende de `persistencia`.
- `frontend-dashboard` depende de todos os endpoints expostos pelos modulos acima.
- `scrapers` suporta principalmente `workers` e, indiretamente, `tasks`.
- `persistencia` e modulo base transversal para API e workers.

## 3. Fluxo consolidado entre modulos

1. `ingestao` recebe submissao e cria task.
2. `tasks`/workers executam pipeline e persistem artefatos.
3. `frontend-dashboard` mostra progresso e permite controle manual.
4. `settings` ajusta comportamento operacional do pipeline em runtime.
5. `articles` permite ajuste fino do conteudo final.
6. `tasks` aciona publicacao via worker.

