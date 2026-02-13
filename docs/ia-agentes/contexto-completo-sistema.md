# Contexto Completo do Sistema Pigmeu Copilot

## Visão Geral do Sistema

O **Pigmeu Copilot** é um sistema automatizado para geração de resenhas técnicas de livros e publicação de artigos otimizados para SEO no WordPress. O sistema utiliza uma arquitetura orientada a pipeline com processamento assíncrono para transformar informações de livros de fontes como Amazon, Goodreads e sites de autores em artigos completos prontos para publicação.

## Arquitetura do Sistema

### Componentes Principais

1. **API e Servidor UI**: FastAPI (`src/app.py`)
   - Expõe endpoints REST para operação
   - Serve SPA estática em `/ui`
   - Executa migrações de banco no startup

2. **Worker Assíncrono**: Celery (`src/workers/worker.py`)
   - Executa tarefas de scraping, contexto, artigo e publicação
   - Usa Redis como broker/backend
   - Tarefas com retry automático e backoff

3. **Persistência**: MongoDB (`src/db/*`)
   - Coleções por agregado (submissions, books, summaries, knowledge_base, articles, etc.)
   - Padrão repository para acesso e atualização
   - Índices otimizados para busca e ordenação

4. **Frontend Operacional**: HTML/CSS/JS vanilla (`src/static/*`)
   - Dashboard de tasks
   - CRUDs de configuração
   - Controles operacionais de pipeline

### Fluxo de Trabalho Principal

1. Usuário cria submissão via `/submit`
2. API grava `submissions` e enfileira `start_pipeline` se `run_immediately=true`
3. Worker executa cadeia de scraping/contexto/artigo:
   - Amazon → Links adicionais → Consolidação → Pesquisa web → Contexto → Artigo
4. UI acompanha status e permite retry por etapa, edição e publicação
5. Publicação cria post no WordPress e atualiza artigo/submissão

## Modelo de Dados

### Coleções Principais

- **submissions**: Comando inicial de trabalho
- **books**: Metadados extraídos e enriquecidos
- **summaries**: Resumos de links adicionais
- **knowledge_base**: Contexto editorial em markdown
- **articles**: Artigos gerados e versões
- **credentials**: Chaves de API para serviços externos
- **prompts**: Configurações de prompts para LLM
- **content_schemas**: Estrutura editorial para artigos
- **pipeline_configs**: Configuração de pipelines de processamento

### Relacionamentos

- `submissions (1) → (1) books` por `books.submission_id`
- `books (1) → (N) summaries` por `summaries.book_id`
- `books (1) → (0..1) knowledge_base` por `knowledge_base.book_id`
- `books (1) → (N) articles` por `articles.book_id`
- `articles (1) → (0..1) articles_drafts` por `article_id`

## Pipeline Operacional

### Pipeline Principal: `book_review_v2`

1. **amazon_scrape**: Extrair metadados do Amazon
2. **additional_links_scrape**: Processar links adicionais
3. **summarize_additional_links**: Gerar resumos de links
4. **consolidate_book_data**: Consolidar dados bibliográficos
5. **internet_research**: Pesquisa web adicional
6. **context_generation**: Gerar base de conhecimento
7. **article_generation**: Gerar artigo completo
8. **ready_for_review**: Pronto para revisão humana

### Estados de Submissão

- `pending_scrape`
- `scraping_amazon`
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

## Processamento de Tarefas

### Tarefas de Scraping (`src/workers/scraper_tasks.py`)

- **scrape_amazon_task**: Extrair metadados do Amazon
- **process_additional_links_task**: Processar links adicionais com LLM
- **consolidate_bibliographic_task**: Consolidar dados bibliográficos
- **internet_research_task**: Pesquisa web sobre livro/autor
- **generate_context_task**: Gerar base de conhecimento em markdown

### Tarefas de Artigos (`src/workers/article_tasks.py`)

- **generate_article_task**: Gerar artigo completo usando ArticleStructurer
- Validação estrutural com content_schema
- Geração com LLM configurável
- Fallback para templates quando LLM falha

### Tarefas de Publicação (`src/workers/publishing_tasks.py`)

- **publish_article_task**: Publicar no WordPress
- Conversão markdown → HTML
- Gerenciamento de categorias e tags
- Atualização de metadados de publicação

## Configuração e Personalização

### Configuração Orientada a Dados

- **pipeline_configs**: Configurar delays, credenciais e prompts por etapa
- **prompts**: Personalizar prompts para diferentes propósitos
- **credentials**: Gerenciar chaves de API para serviços externos
- **content_schemas**: Definir estrutura editorial (TOC, limites, links)

### Bootstrap Automático

O sistema garante configurações default no startup:
- Pipeline `book_review_v2`
- Content schema default
- Credenciais default de bootstrap

## Resiliência e Fallbacks

### Mecanismos de Resiliência

- **Retry automático**: Tarefas Celery com backoff exponencial
- **Fallbacks de scraping**: Quando dados mínimos não são obtidos
- **Fallbacks de LLM**: Geração de conteúdo alternativo quando LLM falha
- **Retry operacional**: Completo ou por etapa com limpeza de dados

### Limpeza por Retry de Etapa

Cada etapa de retry remove artefatos posteriores para evitar incoerência:
- `amazon_scrape`: Remove book + summaries + knowledge_base + articles
- `additional_links_scrape`: Remove summaries/kb/articles e limpa campos relacionados
- `consolidate_book_data`: Remove kb/articles e limpa campos de consolidação
- etc.

## Integrações Externas

### Serviços Integrados

1. **Amazon**: Scraping de metadados de livros
2. **DuckDuckGo/Links web**: Pesquisa de links relacionados
3. **Provedores LLM**: OpenAI, Groq, Mistral, Claude
4. **WordPress**: Publicação de artigos via REST API

### Provedores LLM Suportados

- **Mistral**: Para extração bibliográfica
- **Groq**: Para resumos e pesquisa web
- **OpenAI/Claude**: Para geração de contexto e artigos

## API Principal

### Endpoints Principais

- `POST /submit`: Criar nova submissão de livro
- `GET /tasks`: Listar todas as submissões
- `GET /tasks/{id}`: Detalhes de uma submissão
- `POST /tasks/{id}/retry`: Retentar processamento
- `POST /tasks/{id}/publish_article`: Publicar artigo no WordPress
- `GET /articles`: Listar artigos
- `GET /articles/{id}`: Detalhes de um artigo

### Configuração

- `GET/POST /settings/credentials`: Gerenciar credenciais
- `GET/POST /settings/prompts`: Gerenciar prompts
- `GET/POST /settings/content-schemas`: Gerenciar schemas de conteúdo
- `GET/POST /settings/pipeline-configs`: Gerenciar pipelines

## Segurança e Compliance

### Estado Atual

- Sem autenticação/autorização na API/UI
- Credenciais salvas no banco com flag `encrypted` mas sem criptografia real
- Bootstrap inclui credenciais default hardcoded em código
- Chamada ao WordPress usa Basic Auth

### Recomendações

- Implementar autenticação JWT/OAuth2
- Criptografar credenciais sensíveis
- Remover credenciais default hardcoded
- Implementar controle de acesso baseado em funções

## Limitações Conhecidas

1. **Agendamento**: `schedule_execution` é persistido mas não há scheduler nativo
2. **Goodreads**: Fluxo existe em código mas não é acionado automaticamente
3. **UI**: Alguns módulos são placeholders
4. **Multitenancy**: Não suportado
5. **Observabilidade**: Sem tracing distribuído ou métricas avançadas

## Tecnologias Utilizadas

- **Backend**: Python 3.10+, FastAPI, Celery
- **Banco de Dados**: MongoDB Atlas
- **Fila de Mensagens**: Redis
- **Frontend**: HTML/CSS/JS vanilla
- **Containerização**: Docker, Docker Compose
- **Scraping**: Playwright, httpx
- **LLM**: OpenAI SDK, Groq SDK, Mistral SDK

## Estrutura do Projeto

```
pigmeu/
├── src/
│   ├── app.py                  # Aplicação FastAPI principal
│   ├── config.py               # Configuração
│   ├── logger.py               # Configuração de logging
│   ├── models/                 # Modelos e schemas
│   ├── db/                     # Conexão e repositórios MongoDB
│   ├── api/                    # Endpoints API
│   ├── workers/                # Tarefas Celery
│   ├── scrapers/               # Scrapers e clientes externos
│   └── static/                 # Frontend estático
├── infra/                      # Docker e infraestrutura
├── scripts/                   # Scripts utilitários
├── docs/                      # Documentação
├── requirements.txt            # Dependências Python
└── README.md                  # Documentação principal
```

## Fluxo de Dados Detalhado

1. **Submissão**: Usuário envia URL do Amazon e informações básicas
2. **Scraping Amazon**: Extrair título, autor, ISBN, preço, avaliações, etc.
3. **Links Adicionais**: Processar links extras com LLM para extração bibliográfica e resumos
4. **Consolidação**: Unificar dados do Amazon e links adicionais
5. **Pesquisa Web**: Buscar informações adicionais sobre livro/autor
6. **Contexto**: Gerar base de conhecimento em markdown com todas as informações
7. **Artigo**: Gerar artigo completo com estrutura SEO-otimizada
8. **Revisão**: Artigo fica pronto para revisão humana
9. **Publicação**: Publicar no WordPress com categorias, tags e metadados

## Configuração de Ambiente

### Variáveis de Ambiente

- `MONGODB_URI`: URI de conexão MongoDB
- `REDIS_URL`: URL do Redis
- `OPENAI_API_KEY`: Chave OpenAI
- `GROQ_API_KEY`: Chave Groq
- `MISTRAL_API_KEY`: Chave Mistral
- `WORDPRESS_URL`: URL do WordPress
- `WORDPRESS_USERNAME`: Usuário WordPress
- `WORDPRESS_PASSWORD`: Senha WordPress

### Setup

```bash
cp .env.example .env
# Editar .env com credenciais
pip install -r requirements.txt
python scripts/migrate.py
docker-compose -f infra/docker-compose.yml up --build
```

## Melhores Práticas

1. **Configuração**: Sempre use configurações persistidas em vez de hardcoding
2. **Resiliência**: Implemente fallbacks para todas as operações críticas
3. **Logging**: Use logging estruturado para debug e observabilidade
4. **Validação**: Valide todas as entradas e saídas de dados
5. **Documentação**: Mantenha documentação atualizada com mudanças

## Considerações Operacionais

- A conexão Motor é recriada quando o event loop muda (importante para Celery)
- Dados de configuração influenciam diretamente o comportamento do runtime
- Sempre teste pipelines com dados reais antes de deploy em produção
- Monitore filas do Celery e logs para identificar gargalos

## Roadmap Futuro

1. Implementar autenticação e autorização
2. Adicionar suporte a agendamento nativo
3. Integrar Goodreads no pipeline principal
4. Implementar multitenancy
5. Adicionar métricas e tracing distribuído
6. Melhorar UI com frameworks modernos (React/Vue)
7. Adicionar testes automatizados completos
8. Implementar CI/CD pipeline
9. Adicionar suporte a mais provedores LLM
10. Melhorar documentação e exemplos