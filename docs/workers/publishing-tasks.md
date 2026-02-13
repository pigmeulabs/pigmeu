# Worker: Publishing Tasks (Publicacao WordPress)

Atualizado em: 2026-02-13
Implementacao: `src/workers/publishing_tasks.py`

## 1. Responsabilidade

Publicar artigo no WordPress, persistir metadados de publicacao e atualizar status da submissao.

## 2. Task principal

- `publish_article_task(article_id, submission_id=None, draft=False)`

## 3. Fluxo detalhado

1. carrega artigo por ID.
2. resolve credenciais WordPress:
   - prioridade para credencial ativa no banco (`service=wordpress`)
   - fallback para variaveis de ambiente (`WORDPRESS_*`)
3. valida presenca de URL, usuario e senha.
4. resolve submissao associada (argumento ou `article.submission_id`).
5. monta taxonomias:
   - categoria principal a partir de `submission.main_category`;
   - tags por `article_status`, autor e topicos do artigo.
6. converte markdown para HTML (`markdown_to_html`).
7. gera meta description (`build_meta_description`).
8. usa `WordPressClient` para:
   - resolver/criar categorias e tags;
   - criar post (`publish` ou `draft`).
9. atualiza artigo com:
   - `wordpress_post_id`
   - `wordpress_url`
   - `published_at`
   - `status=published`
   - categorias, tags e meta description.
10. atualiza submissao para `published` e salva `published_url`.
11. atualiza `last_used_at` da credencial WordPress usada.

## 4. Conversao de conteudo

`markdown_to_html` cobre:

- `#`, `##`, `###`
- listas `-`
- paragrafos
- negrito markdown `**texto**`

## 5. Regras e falhas

- sem credencial WordPress valida, retorna erro sem publicar.
- falhas de rede/API WordPress resultam em retorno de erro e log detalhado.
- task nao exige workflow adicional de aprovacao; essa validacao ocorre no endpoint `/tasks/{id}/publish_article`.

## 6. Dependencias

- repositories:
  - `ArticleRepository`
  - `CredentialRepository`
  - `SubmissionRepository`
- integracao externa:
  - `src/scrapers/wordpress_client.py`
- settings:
  - fallback de credenciais por `src/config.py`

## 7. Resultado esperado

- artigo publicado no WordPress com URL publica;
- dados de publicacao rastreaveis no Mongo;
- submissao encerrada em estado `published`.
