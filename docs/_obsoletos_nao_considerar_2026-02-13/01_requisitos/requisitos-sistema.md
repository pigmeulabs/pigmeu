# Requisitos do Sistema

## Requisitos funcionais

### RF-01 Cadastro de task
- O sistema deve permitir criar submissions com `title`, `author_name` e `amazon_url` obrigatórios.
- Deve impedir duplicidade por `amazon_url`.
- Deve suportar campos opcionais: `other_links`, `textual_information`, `main_category`, `article_status`, `user_approval_required`.

### RF-02 Operação de tasks
- Deve listar tasks com paginação, filtro por status e busca textual.
- Deve permitir ações: `generate_context`, `generate_article`, `retry`, `draft_article`, `publish_article`.
- Deve permitir atualização parcial da submission e metadados extraídos.

### RF-03 Interface global da UI
- Deve usar layout com sidebar fixa e área de conteúdo principal.
- Deve exibir navegação completa definida nos wireframes (Analytics, Tasks, Book Review, Credentials, Prompts etc.).
- Deve exibir ação primária por tela no cabeçalho da seção.

### RF-04 Interface de Nova Task (Book Review)
- Deve separar visualmente formulário principal e painel de opções de execução.
- Deve validar obrigatórios (`Book Title`, `Author name`, `Amazon Link`).
- Deve validar URLs dos campos de link.
- Deve exigir `Schedule execution` quando `Run immediately=false`.
- Deve permitir adicionar/remover links adicionais dinamicamente.

### RF-05 Interface de Credenciais (listagem)
- Deve exibir cards com `name`, `service`, `created_at`, `last_used_at` e `active`.
- Deve oferecer ações rápidas por card: `active/inactive`, `edit`, `delete`.
- Deve abrir modal de criação via botão `Create Credential`.

### RF-06 Interface de Credenciais (modal)
- Deve conter `Service`, `Credential Name`, `API Key` e `Username/email` (condicional).
- Deve adaptar campos conforme serviço selecionado.
- Deve impedir salvar sem os campos obrigatórios.
- Deve fechar modal apenas em sucesso.

### RF-07 Interface de Prompts (listagem)
- Deve exibir cards com `name`, `short_description`, `active` e ações rápidas.
- Deve suportar `expand/collapse` por card para exibir `system_prompt` e `user_prompt` completos.
- Deve abrir modal de criação via botão `Create Prompt`.

### RF-08 Interface de Prompts (modal)
- Deve conter identificação do prompt: `Prompt name`, `Short description`.
- Deve conter configuração técnica: `Provider`, `Credential`, `Model`, `Temperature`, `Max Tokens`.
- Deve conter conteúdo do prompt: `System Prompt`, `User Prompt`.
- Deve aplicar dependência de seleção `Provider -> Credential` e `Provider -> Model`.

### RF-09 Pipeline de processamento
- Deve executar scraping Amazon e Goodreads.
- Deve criar/atualizar registro em `books`.
- Deve gerar contexto em `knowledge_base`.
- Deve gerar artigo com validação de estrutura e persistência em `articles`.

### RF-10 Edição de artigo
- Deve permitir atualizar conteúdo e título de artigo.
- Deve permitir salvar draft separado do artigo publicado/gerado.

### RF-11 Publicação WordPress
- Deve publicar artigo via REST API do WordPress.
- Deve salvar `wordpress_post_id` e `wordpress_url` no artigo.
- Deve atualizar status da submission para `published` quando aplicável.

### RF-12 Segurança de credenciais e prompts
- Deve mascarar segredo (`key`) nas respostas de API.
- Não deve expor segredos completos na UI após salvar.
- Deve suportar controle de `active` em credenciais e prompts.

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

### RNF-05 Usabilidade e acessibilidade
- Interface deve operar em desktop e mobile.
- Campos devem ter label visível.
- Erros de validação devem aparecer próximos aos campos.

### RNF-06 Testabilidade
- Projeto deve possuir testes automatizados de unidade/integração.
- Suite atual executa com `pytest` e valida contratos principais.
