# Worker: Article Tasks (Geracao de artigo)

Atualizado em: 2026-02-13
Implementacao: `src/workers/article_tasks.py`

## 1. Responsabilidade

Gerar artigo final em markdown a partir de contexto e dados consolidados, aplicar validacao estrutural e persistir resultado com metadados de configuracao usada.

## 2. Task principal

- `generate_article_task(submission_id, skip_config_delay=False)`

## 3. Resolucao de configuracao de geracao

A task usa `_resolve_article_generation_config` para compor configuracao final com precedencias:

1. config de step no pipeline (`article_generation`).
2. prompt explicitamente vinculado (`prompt_id`).
3. prompt default por `default_prompt_purpose`.
4. fallback para prompt ativo `purpose=article`.
5. fallback final por nome `SEO-Optimized Article Writer`.

Parametros resolvidos:

- `delay_seconds`
- `provider`
- `model_id`
- `temperature`
- `max_tokens`
- `prompt_id`
- `credential_id`
- `api_key`
- `allow_fallback`

Credencial:

- tenta `credential_id` do step;
- fallback por `default_credential_name`;
- fallback por credencial ativa do provider;
- atualiza `last_used_at` quando credencial e usada.

## 4. Fluxo de execucao detalhado

1. carrega submissao e book.
2. carrega KB e summaries do book.
3. resolve content schema:
   - usa `submission.content_schema_id` quando presente;
   - fallback para primeiro schema ativo `book_review`;
   - se fallback usado, grava `content_schema_id` na submissao.
4. resolve configuracao de step de artigo.
5. se `delay_seconds > 0` e `skip_config_delay=false`:
   - atualiza status `pending_article`;
   - reenfileira a propria task com countdown e `skip_config_delay=true`.
6. monta `context` agregando:
   - KB markdown
   - notas de usuario
   - summaries de links
   - bloco de web research
7. atualiza status para etapa de geracao.
8. instancia `ArticleStructurer` e chama `generate_valid_article(...)`.
9. valida artigo com `validate_article(..., strict=True, content_schema=...)`.
10. anexa no report:
    - schema aplicado
    - metadados de pipeline step usado.
11. persiste artigo em `articles`.
12. atualiza submissao para `article_generated`.
13. se `user_approval_required=false`, avança para `ready_for_review`.

## 5. Persistencia e status

Cria artigo com:

- `title`
- `content`
- `word_count`
- `status`:
  - `draft` quando `user_approval_required=true`
  - `in_review` caso contrario
- `validation_report`

Atualiza submissao:

- `status`
- `current_step`
- `article_id`

## 6. Tratamento de falha

- se geracao falhar, atualiza submissao para `failed` com `current_step=article_generation` e erro.
- task retorna payload de erro logavel para observabilidade.

## 7. Dependencias

- repositories:
  - submission/book/kb/summary/article/content_schema/prompt/credential/pipeline
- estruturador:
  - `src/workers/article_structurer.py`
- defaults AI:
  - `src/workers/ai_defaults.py`

## 8. Relevancia operacional

Este worker e o ponto de maior sensibilidade de qualidade do sistema, pois converte artefatos parciais (scraping/contexto) em artigo final validado e pronto para revisao/publicacao.
