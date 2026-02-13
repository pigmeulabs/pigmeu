# SSR — Especificação de Requisitos de Software

**Projeto:** PIGMEU  
**Versão:** 2.0 (consolidada)  
**Data:** 2026-02-12  
**Status:** Reconstruído a partir de históricos, resumos técnicos e mockups

---

## 1. Introdução

### 1.1 Propósito
Definir os requisitos completos do sistema PIGMEU para automação de produção editorial de artigos review de livros, incluindo ingestão, scraping, geração de contexto, geração/validação de artigo SEO, operação via dashboard e publicação opcional no WordPress.

### 1.2 Escopo
O sistema cobre:
- Cadastro de tarefas de review de livros.
- Pipeline assíncrono de scraping e geração de conteúdo.
- Gestão de prompts e credenciais.
- Monitoramento, reprocessamento e métricas.
- Publicação de artigo em WordPress.

### 1.3 Stakeholders
- Operador/Editor: cria tarefas, acompanha pipeline, revisa e publica.
- Administrador técnico: gerencia credenciais, prompts, configurações e infraestrutura.
- Integrações/Agentes: acionam fluxo via API.

### 1.4 Definições
- **Submission**: tarefa de processamento de um livro.
- **KB (Knowledge Base)**: contexto estruturado gerado para o livro.
- **LLM**: modelo de linguagem para geração textual.
- **Idempotência**: reprocessar sem criar duplicação indevida.

---

## 2. Visão Geral do Produto

### 2.1 Objetivo do Negócio
Gerar artigos estruturados e SEO-otimizados sobre livros a partir de fontes externas, com governança editorial e publicação em CMS.

### 2.2 Fluxo Macro
1. Cadastro da tarefa de review.
2. Scraping Amazon.
3. Enriquecimento Goodreads.
4. Geração de contexto (KB).
5. Extração de tópicos.
6. Geração do artigo.
7. Validação estrutural/editorial.
8. Revisão e aprovação (quando exigido).
9. Publicação WordPress (opcional).
10. Monitoramento no dashboard.

### 2.3 Arquitetura e Stack
- API: FastAPI.
- Workers: Celery.
- Banco: MongoDB.
- Broker: Redis.
- Integrações: OpenAI (ou provedor LLM compatível), WordPress REST API, fontes web (Amazon/Goodreads).
- Infra: Docker Compose (`pigmeu-api`, `pigmeu-worker`, `pigmeu-redis`).

---

## 3. Requisitos Funcionais

### 3.1 Cadastro de Tarefa (Book Review)

**RF-001** O sistema deve permitir criar tarefa de review via interface e API (`POST /submit`).

**RF-002** O cadastro deve exigir os campos:
- `title` (Book Title)
- `author_name` (Author name)
- `amazon_url` (Amazon Link)

**RF-003** O cadastro deve aceitar campos opcionais:
- `goodreads_url`
- `author_site`
- `other_links` (Additional Content Link, múltiplos)
- `textual_information` (informação textual livre)

**RF-004** O sistema deve validar formato de URL para campos de link.

**RF-005** O sistema deve validar duplicidade por `amazon_url` antes de criar nova submission.

**RF-006** O cadastro deve suportar:
- `run_immediately` (execução imediata)
- `schedule_execution` (execução agendada)

**RF-007** Quando `run_immediately=false`, `schedule_execution` deve ser obrigatório.

**RF-008** O cadastro deve suportar metadados editoriais:
- `main_category`
- `article_status`
- `user_approval_required`

**RF-009** Ao criar a submission, o sistema deve retornar `submission_id` e status inicial `pending_scrape`.

### 3.2 Pipeline de Scraping e Enriquecimento

**RF-010** O pipeline deve iniciar scraping Amazon após criação da tarefa (modo automático) ou por acionamento manual.

**RF-011** O scraping Amazon deve persistir metadados em `books` vinculados à submission.

**RF-011A** O scraping Amazon deve extrair e persistir os seguintes campos em `books.extracted`:

Observação: a lista de referência possui 16 campos (há duplicidade de numeração no item 8 da origem).

1. `title` (Título do livro)
- CSS: `#productTitle`
- XPath: `//*[@id="productTitle"]`
- JSPath: `document.querySelector("#productTitle")?.textContent.trim()`

2. `original_title` (Título original do livro)
- CSS: `#detailBullets_feature_div li span.a-text-bold:contains("Título original") + span`
- XPath: `//*[@id="detailBullets_feature_div"]//li[.//span[@class="a-text-bold" and contains(normalize-space(.),"Título original")]]//span[@class="a-text-bold"]/following-sibling::span[1]`
- JSPath: `Array.from(document.querySelectorAll("#detailBullets_feature_div li")).find(li => li.innerText.includes("Título original"))?.querySelector("span.a-text-bold + span")?.textContent.trim()`

3. `authors` (Autor(es) do livro)
- CSS: `#bylineInfo span.author a.a-link-normal`
- XPath: `//*[@id="bylineInfo"]//span[contains(@class,"author")]//a`
- JSPath: `Array.from(document.querySelectorAll("#bylineInfo span.author a.a-link-normal")).map(a => a.textContent.trim())`

4. `language` (Idioma do livro)
- CSS: `#detailBullets_feature_div li span.a-text-bold:contains("Idioma") + span`
- XPath: `//*[@id="detailBullets_feature_div"]//li[.//span[@class="a-text-bold" and contains(normalize-space(.),"Idioma")]]//span[@class="a-text-bold"]/following-sibling::span[1]`
- JSPath: `Array.from(document.querySelectorAll("#detailBullets_feature_div li")).find(li => li.innerText.includes("Idioma"))?.querySelector("span.a-text-bold + span")?.textContent.trim()`

5. `original_language` (Idioma original do livro)
- CSS: `#detailBullets_feature_div li span.a-text-bold:contains("Idioma original") + span`
- XPath: `//*[@id="detailBullets_feature_div"]//li[.//span[@class="a-text-bold" and contains(normalize-space(.),"Idioma original")]]//span[@class="a-text-bold"]/following-sibling::span[1]`
- JSPath: `Array.from(document.querySelectorAll("#detailBullets_feature_div li")).find(li => li.innerText.includes("Idioma original"))?.querySelector("span.a-text-bold + span")?.textContent.trim()`

6. `edition` (Edição do livro)
- CSS: `#detailBullets_feature_div li span.a-text-bold:contains("Edição") + span`
- XPath: `//*[@id="detailBullets_feature_div"]//li[.//span[@class="a-text-bold" and contains(normalize-space(.),"Edição")]]//span[@class="a-text-bold"]/following-sibling::span[1]`
- JSPath: `Array.from(document.querySelectorAll("#detailBullets_feature_div li")).find(li => li.innerText.includes("Edição"))?.querySelector("span.a-text-bold + span")?.textContent.trim()`

7. `average_rating` (Avaliação média em estrelas)
- CSS: `#acrPopover`
- XPath: `//*[@id="acrPopover"]`
- JSPath: `document.querySelector("#acrPopover")?.getAttribute("title")?.match(/[\d,\.]+/)?.[0]?.replace(",", ".")`

8. `pages` (Número de páginas)
- CSS: `#detailBullets_feature_div li span.a-text-bold:contains("Número de páginas") + span`
- XPath: `//*[@id="detailBullets_feature_div"]//li[.//span[@class="a-text-bold" and contains(normalize-space(.),"Número de páginas")]]//span[@class="a-text-bold"]/following-sibling::span[1]`
- JSPath: `Array.from(document.querySelectorAll("#detailBullets_feature_div li")).find(li => li.innerText.includes("Número de páginas"))?.querySelector("span.a-text-bold + span")?.textContent.trim()`

9. `publisher` (Editora)
- CSS: `#detailBullets_feature_div li span.a-text-bold:contains("Editora") + span`
- XPath: `//*[@id="detailBullets_feature_div"]//li[.//span[@class="a-text-bold" and contains(normalize-space(.),"Editora")]]//span[@class="a-text-bold"]/following-sibling::span[1]`
- JSPath: `Array.from(document.querySelectorAll("#detailBullets_feature_div li")).find(li => li.innerText.includes("Editora"))?.querySelector("span.a-text-bold + span")?.textContent.trim()`

10. `publication_date` (Data de publicação)
- CSS: `#detailBullets_feature_div li span.a-text-bold:contains("Data da publicação") + span`
- XPath: `//*[@id="detailBullets_feature_div"]//li[.//span[@class="a-text-bold" and contains(normalize-space(.),"Data da publicação")]]//span[@class="a-text-bold"]/following-sibling::span[1]`
- JSPath: `Array.from(document.querySelectorAll("#detailBullets_feature_div li")).find(li => li.innerText.includes("Data da publicação"))?.querySelector("span.a-text-bold + span")?.textContent.trim()`

11. `asin` (ASIN)
- CSS: `#detailBullets_feature_div li span.a-text-bold:contains("ASIN") + span`
- XPath: `//*[@id="detailBullets_feature_div"]//li[.//span[@class="a-text-bold" and contains(normalize-space(.),"ASIN")]]//span[@class="a-text-bold"]/following-sibling::span[1]`
- JSPath: `Array.from(document.querySelectorAll("#detailBullets_feature_div li")).find(li => li.innerText.includes("ASIN"))?.querySelector("span.a-text-bold + span")?.textContent.trim()`

12. `isbn_10` (ISBN-10)
- CSS: `#detailBullets_feature_div li span.a-text-bold:contains("ISBN-10") + span`
- XPath: `//*[@id="detailBullets_feature_div"]//li[.//span[@class="a-text-bold" and contains(normalize-space(.),"ISBN-10")]]//span[@class="a-text-bold"]/following-sibling::span[1]`
- JSPath: `Array.from(document.querySelectorAll("#detailBullets_feature_div li")).find(li => li.innerText.includes("ISBN-10"))?.querySelector("span.a-text-bold + span")?.textContent.trim()`

13. `isbn_13` (ISBN-13)
- CSS: `#detailBullets_feature_div li span.a-text-bold:contains("ISBN-13") + span`
- XPath: `//*[@id="detailBullets_feature_div"]//li[.//span[@class="a-text-bold" and contains(normalize-space(.),"ISBN-13")]]//span[@class="a-text-bold"]/following-sibling::span[1]`
- JSPath: `Array.from(document.querySelectorAll("#detailBullets_feature_div li")).find(li => li.innerText.includes("ISBN-13"))?.querySelector("span.a-text-bold + span")?.textContent.trim()`

14. `price` (Preço do livro)
- CSS: `#corePriceDisplay_desktop_feature_div span.priceToPay`
- XPath: `//*[@id="corePriceDisplay_desktop_feature_div"]//span[contains(@class,"a-price")]`
- JSPath: `(function(){ const w=document.querySelector('#corePriceDisplay_desktop_feature_div span.priceToPay span.a-price-whole')?.textContent||''; const f=document.querySelector('#corePriceDisplay_desktop_feature_div span.priceToPay span.a-price-fraction')?.textContent||''; return (w+ '.' +f).replace(/[^\d\.]/g,''); })()`

15. `ebook_price` (Preço do ebook)
- CSS: `#tmm-grid-swatch-KINDLE span.slot-price span[aria-label]`
- XPath: `//*[@id="tmm-grid-swatch-KINDLE"]//span[contains(@class,"slot-price")]//span[@aria-label]`
- JSPath: `document.querySelector('#tmm-grid-swatch-KINDLE span.slot-price span[aria-label]')?.getAttribute('aria-label')?.match(/[\d,\.]+/)?.[0]?.replace(",", ".")`

16. `cover_image_url` (Link da imagem da capa)
- CSS: `#landingImage`
- XPath: `//*[@id="landingImage"]`
- JSPath: `document.querySelector("#landingImage")?.getAttribute("data-old-hires") || document.querySelector("#landingImage")?.src`

**RF-012** Em falha no scraping Amazon, a submission deve transitar para `scraping_failed` com diagnóstico.

**RF-013** O pipeline deve executar enriquecimento Goodreads após Amazon.

**RF-014** Falha no Goodreads não deve bloquear as etapas seguintes de geração.

### 3.3 Geração de Contexto e Tópicos

**RF-015** O sistema deve gerar KB em Markdown na collection `knowledge_base`.

**RF-016** O sistema deve selecionar prompt por finalidade (`purpose=context`) na collection `prompts`.

**RF-017** O sistema deve usar credencial LLM ativa da collection `credentials` quando disponível.

**RF-018** Na ausência/falha de credencial LLM, o sistema deve gerar contexto por fallback local.

**RF-019** O sistema deve extrair tópicos dinâmicos (ex.: 3 tópicos) para orientar o artigo.

### 3.4 Geração e Validação de Artigo

**RF-020** O sistema deve gerar artigo SEO a partir de `title`, `author_name`, `knowledge_base` e tópicos.

**RF-021** O sistema deve selecionar prompt por finalidade (`purpose=article`) na collection `prompts`.

**RF-022** O artigo gerado deve ser persistido em `articles`.

**RF-023** O sistema deve validar estrutura editorial do artigo:
- 1 H1.
- H2/H3 conforme template editorial ativo.
- Faixa de palavras total.

**RF-024** O sistema deve gerar relatório de validação com métricas e violações.

**RF-025** Em validação aprovada, o sistema deve marcar `ready_for_review`.

**RF-026** Em validação reprovada, o sistema deve manter o artigo persistido e marcar inválido (status/flag).

**RF-027** O sistema deve suportar edição de rascunho antes da publicação (`draft_article`).

### 3.5 Publicação

**RF-028** O sistema deve converter Markdown para HTML no fluxo de publicação.

**RF-029** O sistema deve publicar no WordPress via API quando acionado.

**RF-030** Após publicar, o sistema deve persistir `wordpress_post_id` e `wordpress_url` no artigo.

**RF-031** O sistema deve impedir publicação quando regra de aprovação exigir revisão e ela não estiver concluída.

### 3.6 Operação de Tasks

**RF-032** O sistema deve listar submissions com paginação e filtro por status (`GET /tasks`).

**RF-033** O sistema deve retornar detalhe de submission com progresso e erros (`GET /tasks/{id}`).

**RF-034** O sistema deve permitir atualização controlada de campos (`PATCH /tasks/{id}`).

**RF-035** O sistema deve permitir disparo manual de geração de contexto e artigo por submission.

**RF-036** O sistema deve permitir retry de etapas com falha (`POST /tasks/{id}/retry`).

**RF-037** O sistema deve expor métricas agregadas (`GET /stats` ou equivalente).

### 3.7 Requisitos de Interface (Dashboard)

**RF-038** A navegação lateral deve conter:
- Analytics
- Tasks
- Content Copilot
- Book Review
- Articles
- Social media
- SEO Tools
- Settings
- Credentials
- Content Schemas
- Prompts
- Logout

**RF-039** A interface de nova tarefa de review deve conter:
- `Book Title*`
- `Author name*`
- `Amazon Link*`
- `Additional Content Link (optional)` com adição de múltiplos links
- `Textual information (optional)`
- Painel de opções com `Run immediately`, `Schedule execution`, `Main Category`, `Article Status`, `User approval required`
- Botão `Create Task`

**RF-040** A dashboard de tarefas deve suportar busca e filtros por status.

### 3.8 Requisitos de Interface (Credentials)

**RF-041** A tela de credenciais deve listar itens com:
- Nome da credencial
- Tipo/serviço
- Status ativo/inativo
- Data de criação
- Data do último uso

**RF-042** Cada credencial deve oferecer ações `Edit` e `Delete`.

**RF-043** A tela deve oferecer ação global `Create Credential`.

**RF-044** O modal de criação/edição de credencial deve conter:
- `Service`
- `Credential Name`
- `API Key` (obrigatório)
- `Username/email` (opcional conforme serviço)
- Ação `Save`

### 3.9 Requisitos de Interface (Prompts)

**RF-045** A tela de prompts deve listar cards com:
- Nome
- Descrição curta
- Status ativo/inativo
- Trechos de `system_prompt` e `user_prompt` em modo expandido

**RF-046** Cada prompt deve oferecer ações `Edit`, `Delete` e alternância de ativação.

**RF-047** A tela deve oferecer ação global `Create Prompt`.

**RF-048** O modal Add/Edit Prompt deve conter:
- `Prompt name`
- `Short description`
- `System Prompt`
- `User Prompt`
- Ação `Save`

### 3.10 Prompts de Seed

**RF-049** O sistema deve suportar seed inicial de prompts via `scripts/seed_prompts.py`.

**RF-050** O seed deve cobrir, no mínimo, prompts para:
- Extração de metadados
- Geração de contexto
- Extração de tópicos
- Geração de artigo SEO
- Sumarização de links

---

## 4. Requisitos de Dados

### 4.1 Collections Obrigatórias

**RD-001** `submissions`
- Campos mínimos: `_id`, `title`, `author_name`, `amazon_url`, `goodreads_url`, `author_site`, `other_links`, `textual_information`, `main_category`, `article_status`, `user_approval_required`, `run_immediately`, `schedule_execution`, `status`, `current_step`, `attempts`, `errors`, `created_at`, `updated_at`.

**RD-002** `books`
- Campos mínimos: `submission_id`, `updated_at`, `goodreads_data` e metadados Amazon estruturados em `extracted` com:
  `title`, `original_title`, `authors`, `language`, `original_language`, `edition`, `average_rating`, `pages`, `publisher`, `publication_date`, `asin`, `isbn_10`, `isbn_13`, `price`, `ebook_price`, `cover_image_url`, `amazon_url`.

**RD-003** `knowledge_base`
- Campos mínimos: `submission_id/book_id`, `markdown_content`, `topics_index`, `created_at`, `updated_at`.

**RD-004** `articles`
- Campos mínimos: `submission_id/book_id`, `title`, `content_markdown`, `content_html`, `validation_report`, `status`, `wordpress_post_id`, `wordpress_url`, `created_at`, `updated_at`.

**RD-005** `prompts`
- Campos mínimos: `name`, `purpose`, `system_prompt`, `user_prompt`, `model_id`, `temperature`, `max_tokens`, `version`, `active`, `created_at`, `updated_at`.

**RD-006** `credentials`
- Campos mínimos: `service`, `name`, `secret`, `username_email`, `active`, `created_at`, `last_used_at`, `updated_at`.

**RD-007** `summaries` (quando módulo de links estiver habilitado)
- Campos mínimos: `submission_id/book_id`, `source_url`, `summary_markdown`, `created_at`.

### 4.2 Rastreabilidade entre Entidades

**RD-008** O sistema deve manter vínculo estável entre `submission`, `book`, `knowledge_base` e `article`.

**RD-009** O sistema deve armazenar tentativas por etapa para auditoria e retry.

---

## 5. Estados e Transições do Pipeline

### 5.1 Estados Mínimos
- `pending_scrape`
- `scraping_amazon`
- `scraping_goodreads`
- `context_generation`
- `context_generated`
- `pending_article`
- `article_generated`
- `ready_for_review`
- `approved` (quando revisão manual estiver habilitada)
- `published`
- `scraping_failed`

### 5.2 Regras de Transição

**RT-001** `pending_scrape -> scraping_amazon` ao iniciar pipeline.

**RT-002** `scraping_amazon -> scraping_goodreads` em sucesso.

**RT-003** `scraping_goodreads -> context_generation` mesmo com falha de enriquecimento.

**RT-004** `context_generation -> context_generated` após persistência da KB.

**RT-005** `context_generated -> pending_article -> article_generated` na geração de artigo.

**RT-006** `article_generated -> ready_for_review` após validação aprovada.

**RT-007** `ready_for_review -> approved -> published` quando revisão e publicação ocorrerem.

**RT-008** Qualquer falha crítica de scraping deve registrar diagnóstico e levar a `scraping_failed`.

---

## 6. Requisitos Não Funcionais

### 6.1 Confiabilidade

**RNF-001** Tasks assíncronas devem ter retry automático (mínimo 3 tentativas).

**RNF-002** Retry deve usar backoff exponencial com jitter.

**RNF-003** Goodreads e outras fontes não críticas não devem interromper o pipeline principal.

### 6.2 Consistência e Idempotência

**RNF-004** Reprocessamento não deve criar duplicação indevida de artefatos.

**RNF-005** Atualizações de estado devem manter consistência de sequência por submission.

### 6.3 Desempenho

**RNF-006** A API deve responder operações de listagem/detalhe em tempo compatível com uso operacional.

**RNF-007** O sistema deve suportar múltiplas submissions em paralelo via workers.

### 6.4 Disponibilidade e Recuperação

**RNF-008** Reinício de API/workers não pode perder rastreabilidade de status.

**RNF-009** O sistema deve permitir retomada/retry de etapas após falha.

### 6.5 Segurança

**RNF-010** Segredos de credenciais não devem ser logados.

**RNF-011** Credenciais devem ser armazenadas de forma segura.

**RNF-012** Campos sensíveis (`API Key`, senhas/tokens) não devem ser reexibidos em texto puro na UI após salvar.

### 6.6 Observabilidade

**RNF-013** Logs devem incluir `submission_id`, etapa, timestamps e erros.

**RNF-014** O sistema deve registrar início/fim de cada etapa de pipeline.

**RNF-015** Métricas devem cobrir volume por status, sucesso/falha e tempo médio por etapa.

### 6.7 Portabilidade e Operação

**RNF-016** O sistema deve operar via Docker Compose com API, worker e Redis.

**RNF-017** Configuração por variáveis de ambiente deve suportar ambientes local e servidor.

---

## 7. Regras de Negócio

**RB-001** Um livro duplicado por `amazon_url` não deve criar nova submission sem confirmação explícita de reprocessamento.

**RB-002** Publicação deve respeitar regra de aprovação quando `user_approval_required=true`.

**RB-003** Prompts e credenciais ativos devem ser priorizados nas execuções.

**RB-004** O artigo deve seguir o template editorial vigente definido pelo prompt ativo.

**RB-005** O sistema deve manter histórico operacional mínimo de criação, uso e alteração de recursos críticos (submissions, prompts, credenciais).

---

## 8. Interfaces de API (consolidadas)

### 8.1 Submissões/Tarefas
- `POST /submit` — cria submission.
- `GET /tasks` — lista submissions (paginação e filtros).
- `GET /tasks/{id}` — detalhe e progresso.
- `PATCH /tasks/{id}` — atualização controlada.
- `POST /tasks/{id}/generate_context` — enfileira geração de contexto.
- `POST /tasks/{id}/generate_article` — enfileira geração de artigo.
- `POST /tasks/{id}/retry` — reprocessa etapa(s).

### 8.2 Operação e Métricas
- `GET /stats` (ou `/metrics`) — indicadores operacionais.
- `GET /health` — saúde da API.

### 8.3 Publicação
- `POST /tasks/{id}/publish_article` — publica no WordPress.
- `POST /tasks/{id}/draft_article` — salva/atualiza rascunho editorial.

### 8.4 Configuração
- Endpoints de gestão de `credentials` (listar/criar/editar/remover/ativar).
- Endpoints de gestão de `prompts` (listar/criar/editar/remover/ativar).

---

## 9. Critérios de Aceite de Alto Nível

**CA-001** É possível criar uma submission válida com campos obrigatórios e obter `submission_id`.

**CA-002** O pipeline executa scraping Amazon e tenta Goodreads com atualização de status.

**CA-003** O sistema gera KB e artigo com fallback quando LLM estiver indisponível.

**CA-004** O artigo possui validação estrutural e registro de relatório.

**CA-005** O dashboard permite listar, filtrar, detalhar e reprocessar tasks.

**CA-006** O módulo de credenciais permite criar, listar, editar, ativar/inativar e excluir sem expor segredo.

**CA-007** O módulo de prompts permite criar, listar, editar, ativar/inativar e excluir.

**CA-008** Com credencial WordPress válida, o artigo pode ser publicado e retorna `wordpress_post_id`/`wordpress_url`.

---

## 10. Premissas e Pontos de Validação

1. Alguns campos e estados podem variar conforme implementação final dos modelos do repositório.
2. A regra exata de estrutura do artigo (quantidade fixa de H2) deve seguir o template/prompt ativo em produção.
3. O controle de autenticação/autorização da dashboard e APIs administrativas deve ser confirmado na implementação final.
4. Os endpoints de configuração de prompts/credenciais devem ser confirmados no código final caso não estejam expostos ainda.

---

## 11. Dependências Externas

- MongoDB.
- Redis.
- API de LLM.
- WordPress REST API.
- Fontes web para scraping (Amazon/Goodreads e links externos).
