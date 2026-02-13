# Arquitetura

Atualizado em: 2026-02-13

## 1. Objetivo arquitetural

O sistema PIGMEU implementa um fluxo de geracao de conteudo orientado a pipeline, com foco em:

- ingestao de submissao de review de livro;
- enriquecimento de dados por scraping e LLM;
- geracao de contexto editorial e artigo final em markdown;
- revisao operacional via UI;
- publicacao em WordPress.

A arquitetura foi desenhada para separar:

- operacoes HTTP de baixa latencia (API/UI);
- processamento longo e falhavel (workers Celery);
- persistencia incremental de artefatos (MongoDB);
- configuracao de comportamento por dados (pipelines, prompts, credenciais, schemas).

## 2. Visao macro

### 2.1 Componentes principais

- API e servidor UI: FastAPI (`src/app.py`)
  - expõe REST para operacao.
  - serve SPA estatica em `/ui`.
  - executa migracoes de banco no startup.
- Worker assicrono: Celery (`src/workers/worker.py`)
  - executa tarefas de scraping, contexto, artigo e publicacao.
  - usa Redis como broker/backend.
- Persistencia: MongoDB (`src/db/*`)
  - colecoes por agregado (`submissions`, `books`, `summaries`, etc.).
  - padrao repository para acesso e update.
- Frontend operacional: HTML/CSS/JS vanilla (`src/static/*`)
  - dashboard de tasks.
  - CRUDs de configuracao.
  - controles operacionais de pipeline.
- Integracoes externas:
  - Amazon (Playwright + parsing HTML);
  - DuckDuckGo/links web (httpx + parsing HTML);
  - provedores LLM OpenAI-compatible (Groq, Mistral);
  - WordPress REST API.

### 2.2 Diagrama de fluxo (alto nivel)

1. Usuario cria submissao via `/submit`.
2. API grava `submissions` e, se `run_immediately=true`, enfileira `start_pipeline`.
3. Worker executa cadeia de scraping/contexto/artigo:
   - amazon -> links -> consolidacao -> pesquisa web -> contexto -> artigo.
4. UI acompanha status e permite retry por etapa, edicao e publicacao.
5. Publicacao cria post no WordPress e atualiza artigo/submissao.

## 3. Camadas e responsabilidades

### 3.1 Camada de API (`src/api/*`)

Responsavel por:

- validacao de entrada (Pydantic + regras de endpoint);
- leitura/escrita de dados via repositories;
- enfileiramento de tarefas Celery;
- agregacao de detalhes para visualizacao operacional;
- CRUD de configuracoes (credentials/prompts/content schemas/pipelines).

Caracteristicas:

- sem autenticacao/autorizacao implementada;
- responses JSON com ObjectId serializado para string;
- endpoints de health e stats para observabilidade basica.

### 3.2 Camada de processamento assicrono (`src/workers/*`)

Responsavel por:

- execucao de scraping com retries;
- orchestracao de etapas com delays configuraveis por pipeline;
- geracao de contexto e artigo com LLM;
- publicacao em WordPress;
- atualizacao de status/corrente de etapa em `submissions`.

Caracteristicas:

- Celery com `task_track_started=true`, `task_ignore_result=true`;
- uso de `asyncio.run()`/event loop dedicado em tarefas que chamam codigo async;
- politica de retry com backoff na base `ScraperTask`.

### 3.3 Camada de dados (`src/db/*`)

Responsavel por:

- conexao Motor com tratamento de troca de event loop (importante para Celery);
- criacao de colecoes e indices no startup (`run_migrations`);
- CRUD especializado por agregado de dominio.

Caracteristicas:

- modelagem orientada a documento;
- atualizacao incremental de artefatos por etapa;
- indices de busca, ordenacao e unicidade (ex.: `amazon_url` unico em `submissions`).

### 3.4 Camada de apresentacao (`src/static/*`)

Responsavel por:

- operacao de tasks (listar, detalhar, retry, editar, deletar, gerar artigo, publicar);
- operacao de configuracoes (credentials, prompts, content schemas, pipelines);
- exibicao de progresso por etapa com timeline;
- controle de estados de tela e feedback de erro/sucesso.

Caracteristicas:

- SPA sem framework;
- consumo direto dos endpoints REST;
- alguns itens de menu sao placeholders (Analytics, Articles, Social Media, SEO Tools, Settings, Logout).

## 4. Pipeline operacional implementado

### 4.1 Pipeline principal: `book_review_v2`

Etapas e executor:

1. `amazon_scrape`
   - executor: `scrape_amazon_task`
   - efeito: cria/atualiza `books.extracted` com metadados Amazon.
2. `additional_links_scrape`
   - executor: `process_additional_links_task`
   - efeito: processa `other_links`, grava `summaries` e candidatos bibliograficos.
3. `summarize_additional_links`
   - executor: mesma task anterior, fase de resumo.
4. `consolidate_book_data`
   - executor: `consolidate_bibliographic_task`
   - efeito: consolida dados Amazon + links em `consolidated_bibliographic`.
5. `internet_research`
   - executor: `internet_research_task`
   - efeito: pesquisa web adicional e grava `web_research`.
6. `context_generation`
   - executor: `generate_context_task`
   - efeito: gera `knowledge_base.markdown_content`.
7. `article_generation`
   - executor: `generate_article_task`
   - efeito: gera artigo em `articles` + validacao.
8. `ready_for_review`
   - etapa de workflow sinalizada por status da submissao.

### 4.2 Pipeline secundario: `links_content_v1`

- existe como template e pode ser configurado em `pipeline_configs`.
- o encadeamento automatico de workers hoje continua acoplado ao fluxo principal de scraping/contexto/artigo.
- portanto, `links_content_v1` esta presente como configuracao, mas nao tem cadeia dedicada completa no runtime atual.

## 5. Estados de submissao e progresso

Estados modelados em `SubmissionStatus`:

- `pending_scrape`
- `scraping_amazon`
- `scraping_goodreads` (enum existe; fluxo principal nao aciona)
- `scraped`
- `pending_context`
- `context_generation`
- `context_generated`
- `pending_article`
- `article_generated`
- `ready_for_review`
- `approved`
- `published`
- `scraping_failed`
- `failed`

Regra geral de transicao:

- cada etapa atualiza `status` + `current_step` + timestamps/campos auxiliares;
- falhas em scraping/artigo podem levar a `scraping_failed` ou `failed`;
- retry por etapa remove artefatos posteriores e recoloca status coerente.

## 6. Configuracao orientada a dados

A arquitetura usa configuracoes persistidas para reduzir necessidade de deploy:

- `pipeline_configs`
  - permite configurar por step: `delay_seconds`, `credential_id`, `prompt_id`.
- `prompts`
  - parametriza prompts de contexto/artigo e etapas auxiliares.
- `credentials`
  - concentra chaves de provedores LLM e WordPress.
- `content_schemas`
  - define estrutura editorial (TOC, limites, links).

Bootstrap automatico em runtime (settings API):

- garante pipelines default (`book_review_v2`, `links_content_v1`);
- garante content schema default;
- garante credenciais default de bootstrap.

## 7. Resiliencia e fallbacks

### 7.1 Fallbacks de scraping/LLM

- Amazon scraping:
  - se nao obtiver dados minimos (ex.: titulo), marca falha de scraping.
- links adicionais:
  - se LLM indisponivel, resumo cai para extrato textual heuristico.
- pesquisa web:
  - se LLM indisponivel, gera markdown fallback com topicos inferidos.
- contexto/artigo:
  - se prompt/LLM falharem, geracao tenta caminhos alternativos/template.

### 7.2 Retry operacional

- retry completo: recomeça do inicio (`start_pipeline`).
- retry por etapa: limpa dados de etapas posteriores (summaries, kb, artigos, drafts e campos extraidos especificos) e re-enfileira a etapa alvo.

## 8. Observabilidade

- Endpoints:
  - `/health`, `/tasks/health`, `/submit/health`
  - `/stats` e `/tasks/stats`
- Logs:
  - API: ciclo de vida, falhas de validacao/enqueue.
  - Workers: falhas de scraping/LLM/publicacao e eventos de transicao.

Limitacoes atuais de observabilidade:

- sem tracing distribuido;
- sem metricas de fila por task no proprio produto (apenas via logs/infra externa).

## 9. Seguranca e compliance (estado atual)

- Sem auth na API/UI.
- Credenciais salvas no banco com flag `encrypted`, mas sem camada de criptografia aplicada no repository.
- Bootstrap inclui credenciais default hardcoded em codigo (`src/api/settings.py`), o que exige endurecimento para ambiente produtivo.
- Chamada ao WordPress usa Basic Auth e pode cair para configuracao de `.env`.

## 10. Decisoes arquiteturais vigentes

- FastAPI + SPA no mesmo servico
  - simplifica deploy e reduz superficie operacional.
- Celery + Redis
  - desacopla request HTTP de operacoes longas e falhaveis.
- MongoDB orientado a documentos
  - favorece evolucao rapida de schema e armazenamento de artefatos heterogeneos por etapa.
- Pipeline configuravel no banco
  - permite tuning operacional por step sem alterar codigo.
- Geracao com content schema
  - adiciona validacao estrutural e controle editorial mais forte.

## 11. Limitacoes estruturais conhecidas

- `schedule_execution` e persistido mas nao ha scheduler nativo para disparo futuro.
- Fluxo Goodreads existe em codigo de scraper/enum, mas nao compoe o pipeline automatico principal.
- Alguns modulos de menu da UI estao apenas como placeholders.
- Sem multitenancy e sem controle de usuarios/permissoes.

## 12. Referencias de codigo

- App/Lifecycle: `src/app.py`
- API routes: `src/api/*.py`
- Worker bootstrap: `src/workers/worker.py`
- Worker pipeline: `src/workers/scraper_tasks.py`, `src/workers/article_tasks.py`, `src/workers/publishing_tasks.py`
- Estruturacao e validacao do artigo: `src/workers/article_structurer.py`
- Dados/repositorios: `src/db/connection.py`, `src/db/migrations.py`, `src/db/repositories.py`
- Frontend: `src/static/index.html`, `src/static/app.js`, `src/static/styles.css`
