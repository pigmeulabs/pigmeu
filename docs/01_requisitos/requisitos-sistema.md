# Requisitos do Sistema

## Requisitos funcionais

### RF-01 Cadastro de task
- O sistema deve permitir criar submissions com `title`, `author_name` e `amazon_url` obrigatórios.
- Deve impedir duplicidade por `amazon_url`.
- Deve suportar campos opcionais: Goodreads, links extras, informações textuais, categoria, status editorial e aprovação.

### RF-02 Pipeline de processamento
- Deve executar scraping Amazon e Goodreads.
- Deve criar/atualizar registro em `books`.
- Deve gerar contexto em `knowledge_base`.
- Deve gerar artigo com validação de estrutura e persistência em `articles`.

### RF-03 Enriquecimento externo
- Deve buscar até 3 links externos relevantes.
- Deve resumir conteúdo e salvar em `summaries`.
- Deve incorporar resumos externos na `knowledge_base`.

### RF-04 Operação de tasks
- Deve listar tasks com paginação, filtro por status e busca textual.
- Deve permitir ações: `generate_context`, `generate_article`, `retry`, `draft_article`, `publish_article`.
- Deve permitir atualização parcial da submission e metadados extraídos.

### RF-05 CRUD de credenciais
- Deve permitir criar, listar, atualizar e excluir credenciais.
- Deve mascarar segredo (`key`) nas respostas de API.
- Deve suportar controle `active` e atualização de `last_used_at`.

### RF-06 CRUD de prompts
- Deve permitir criar, listar, atualizar e excluir prompts.
- Deve suportar filtro por `active`, `purpose` e busca por nome.
- Deve permitir alternar prompt ativo para uso no pipeline.

### RF-07 Edição de artigo
- Deve permitir atualizar conteúdo e título de artigo.
- Deve permitir salvar draft separado do artigo publicado/gerado.

### RF-08 Publicação WordPress
- Deve publicar artigo via REST API do WordPress.
- Deve salvar `wordpress_post_id` e `wordpress_url` no artigo.
- Deve atualizar status da submission para `published` quando aplicável.

## Requisitos não funcionais

### RNF-01 Robustez operacional
- Tasks de scraping devem ter retry automático (backoff/jitter).
- Falha de Goodreads não deve impedir continuidade.

### RNF-02 Performance básica
- Listagens devem usar índices e paginação.
- Processamento assíncrono via fila Redis/Celery.

### RNF-03 Segurança mínima
- Segredos não devem ser retornados em texto puro.
- Dados sensíveis não devem ser expostos em logs de aplicação.

### RNF-04 Observabilidade
- API e workers devem registrar eventos críticos e falhas.
- Endpoints de health devem estar disponíveis.

### RNF-05 Testabilidade
- Projeto deve possuir testes automatizados de unidade/integração.
- Suite atual executa com `pytest` e valida contratos principais.
