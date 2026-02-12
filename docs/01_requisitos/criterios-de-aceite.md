# Critérios de Aceite

## CA-01 Criar task
- Dado payload válido, `POST /submit` retorna `201` com `id` e status inicial.
- Dado `amazon_url` já existente, retorna `400` com mensagem de duplicidade.

## CA-02 Listagem e filtro
- `GET /tasks` deve respeitar `skip`, `limit`, `status` e `search`.
- UI deve refletir filtros sem recarregar página.

## CA-03 Pipeline contexto/artigo
- Disparo de `generate_context` e `generate_article` retorna `202`.
- Task deve refletir transições de estado em até 1 ciclo de processamento do worker.

## CA-04 Draft e edição
- `POST /tasks/{id}/draft_article` deve salvar conteúdo não vazio.
- `PATCH /articles/{id}` deve atualizar título/conteúdo e retornar artigo atualizado.

## CA-05 Publicação WordPress
- `POST /tasks/{id}/publish_article` deve enfileirar publicação e retornar `202`.
- Após execução com credenciais válidas, artigo deve conter `wordpress_post_id` e `wordpress_url`.

## CA-06 Credenciais
- API deve mascarar chave ao listar/buscar credenciais.
- Alteração de status `active` deve refletir em listagem sem inconsistência.

## CA-07 Prompts
- Deve permitir CRUD completo e filtro por `active/purpose/search`.
- Pipeline deve conseguir selecionar prompt ativo por propósito.

## CA-08 Qualidade mínima
- `pytest -q` deve passar.
- `python -m compileall -q src tests scripts` deve passar.
