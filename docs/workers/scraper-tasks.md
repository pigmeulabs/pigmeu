# Worker: Scraper Tasks (Pipeline de coleta e contexto)

Atualizado em: 2026-02-13
Implementacao: `src/workers/scraper_tasks.py`

## 1. Responsabilidade

Executar o bloco inicial do pipeline:

- scraping Amazon;
- processamento de links adicionais;
- consolidacao bibliografica;
- pesquisa web;
- geracao de contexto (knowledge base).

## 2. Tasks publicas

- `scrape_amazon_task`
- `process_additional_links_task`
- `consolidate_bibliographic_task`
- `internet_research_task`
- `generate_context_task`
- `check_scraping_status`
- `start_scraping_pipeline` (helper para iniciar cadeia)

## 3. Base de execucao e resiliencia

- tasks principais usam `ScraperTask` com:
  - retry automatico
  - backoff exponencial
  - jitter
- resolucao de delay por step:
  - `_get_step_delay_seconds(step_id, pipeline_id)`
  - leitura de `pipeline_configs.steps[].delay_seconds`
- enfileiramento com delay:
  - `_enqueue_task(task, delay_seconds, **kwargs)`

## 4. Prompts auxiliares embutidos

Este worker contem templates default para garantir fluxo minimo quando prompts nao existem no banco:

- `LINK_BIBLIO_PROMPT` (extracao bibliografica por link)
- `LINK_SUMMARY_PROMPT` (resumo de link)
- `WEB_RESEARCH_PROMPT` (sintese de pesquisa web)

Regra:

- `_ensure_prompt` cria prompt apenas se nao houver prompt com mesmo nome;
- prompts existentes de usuario nao sao sobrescritos automaticamente.

## 5. Cadeia detalhada de execucao

## 5.1 `scrape_amazon_task`

Entrada:

- `submission_id`
- `amazon_url`
- `pipeline_id`

Fluxo:

1. carrega submissao e resolve `pipeline_id` efetivo.
2. atualiza status para `scraping_amazon` e `current_step=amazon_scrape`.
3. executa `AmazonScraper.scrape(amazon_url)`.
4. se falhar sem dados minimos (sem titulo):
   - status `scraping_failed`
   - registra erro explicito.
5. se sucesso:
   - grava `books.extracted`;
   - status `pending_context`, `current_step=additional_links_processing`;
   - enfileira `process_additional_links_task` (com delay configurado).

## 5.2 `process_additional_links_task`

Entrada:

- `submission_id`

Fluxo:

1. carrega submissao e book.
2. status `pending_context`, `current_step=additional_links_processing`.
3. garante prompts de extracao bibliografica e resumo.
4. resolve credenciais LLM:
   - preferencia por nome default (`Mistral A`, `GROC A`)
   - fallback para credencial ativa por servico.
5. percorre `other_links` deduplicados.
6. para cada link:
   - fetch/parse de conteudo (`LinkFinder.fetch_and_parse`)
   - extracao bibliografica (Mistral)
   - resumo (Groq)
   - grava `summary` com metadados extras.
7. atualiza `books.extracted` com:
   - candidatos bibliograficos
   - total/processado
   - timestamp de processamento
8. status `pending_context`, `current_step=bibliographic_consolidation`.
9. enfileira `consolidate_bibliographic_task`.

Caso sem links adicionais:

- avanca direto para consolidacao com contadores zerados.

## 5.3 `consolidate_bibliographic_task`

Fluxo:

1. status `pending_context`, `current_step=bibliographic_consolidation`.
2. coleta candidatos de `summaries.bibliographic_data`.
3. normaliza dados Amazon e dados de links.
4. consolida campos sem duplicidade/colisao.
5. grava em `books.extracted.consolidated_bibliographic` + contadores.
6. status `pending_context`, `current_step=internet_research`.
7. enfileira `internet_research_task`.

## 5.4 `internet_research_task`

Fluxo:

1. status `pending_context`, `current_step=internet_research`.
2. garante prompt de pesquisa web.
3. resolve credencial Groq.
4. busca links externos relacionados (`search_book_links`).
5. coleta snippets/excerpts das fontes.
6. executa sintese LLM (ou fallback heuristico).
7. grava bloco `web_research` em `books.extracted`.
8. status `context_generation`, `current_step=context_generation`.
9. enfileira `generate_context_task`.

## 5.5 `generate_context_task`

Fluxo:

1. status `context_generation`, `current_step=context_generation`.
2. coleta:
   - dados extraidos do book
   - consolidacao bibliografica
   - web research
   - summaries
   - notas do usuario
3. busca prompt de contexto (`purpose=context` ou fallback por nome).
4. tenta gerar markdown via LLM.
5. fallback: monta markdown estruturado localmente.
6. calcula `topics_index` deduplicado.
7. upsert em `knowledge_base`.
8. status `context_generated`, depois `pending_article`.
9. enfileira `generate_article_task` com delay configurado de `article_generation`.

## 5.6 `check_scraping_status`

Retorna snapshot simplificado:

- `submission_status`
- `current_step`
- `updated_at`

## 6. Efeitos persistentes por etapa

- `submissions`: status/current_step/errors/contadores.
- `books`: metadados Amazon, consolidacao e web research.
- `summaries`: resumo e dados auxiliares por link.
- `knowledge_base`: markdown consolidado + topicos.

## 7. Integracoes e dependencias

- scrapers:
  - `AmazonScraper`
  - `LinkFinder`
- LLM:
  - `LLMClient`
  - `build_user_prompt_with_output_format`
- repositories:
  - submission/book/summary/kb/prompt/credential/pipeline

## 8. Pontos de atencao

- sucesso de scraping depende de disponibilidade e layout dos sites externos.
- ausencia de credencial LLM ativa aciona caminhos de fallback com qualidade reduzida.
- estado de pipeline precisa ser mantido consistente; por isso cada etapa atualiza status explicitamente.
