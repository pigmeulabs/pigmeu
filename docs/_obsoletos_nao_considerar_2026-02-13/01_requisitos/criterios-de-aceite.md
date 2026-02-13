# Critérios de Aceite

## CA-01 Criar task
- Dado payload válido, `POST /submit` retorna `201` com `id` e status inicial.
- Dado `amazon_url` já existente, retorna `400` com mensagem de duplicidade.

## CA-02 Nova Task (validações de UI)
- A UI deve bloquear envio sem `Book Title`, `Author name` e `Amazon Link`.
- A UI deve validar formato de URL para `amazon_url` e `other_links`.
- Com `run_immediately=false`, a UI deve exigir `schedule_execution`.

## CA-03 Listagem e filtro de tasks
- `GET /tasks` deve respeitar `skip`, `limit`, `status` e `search`.
- UI deve refletir filtros sem recarregar a página.

## CA-04 Pipeline contexto/artigo
- Disparo de `generate_context` e `generate_article` retorna `202`.
- Task deve refletir transições de estado em até 1 ciclo de processamento do worker.

## CA-05 Draft e edição
- `POST /tasks/{id}/draft_article` deve salvar conteúdo não vazio.
- `PATCH /articles/{id}` deve atualizar título/conteúdo e retornar artigo atualizado.

## CA-06 Publicação WordPress
- `POST /tasks/{id}/publish_article` deve enfileirar publicação e retornar `202`.
- Após execução com credenciais válidas, artigo deve conter `wordpress_post_id` e `wordpress_url`.

## CA-07 Credenciais (listagem)
- API deve mascarar `key` ao listar/buscar credenciais.
- Alteração de `active` deve refletir em listagem sem inconsistência.
- Ação de `delete` deve exigir confirmação na UI.

## CA-08 Credenciais (modal)
- Modal deve abrir em modo criação via `Create Credential` e em modo edição via `Edit`.
- Modal deve validar obrigatórios (`Service`, `Credential Name`, `API Key`).
- Campos condicionais por serviço devem ser exibidos conforme regra de negócio.

## CA-09 Prompts (listagem)
- Deve permitir CRUD completo e filtro por `active/purpose/search`.
- Cada card deve permitir `expand/collapse` para visualização completa de `System Prompt` e `User Prompt`.
- Ação de `delete` deve exigir confirmação na UI.

## CA-10 Prompts (modal)
- Modal deve validar obrigatórios de identificação, configuração técnica e conteúdo.
- Deve validar dependência `Provider -> Credential` e `Provider -> Model`.
- `Prompt name` duplicado deve ser rejeitado.

## CA-11 Estados de interface
- Listagens e submits devem exibir `loading` durante requisição.
- Sem dados, deve exibir `empty state`.
- Falhas de API devem exibir mensagem de erro clara.

## CA-12 Qualidade mínima
- `pytest -q` deve passar.
- `python -m compileall -q src tests scripts` deve passar.
