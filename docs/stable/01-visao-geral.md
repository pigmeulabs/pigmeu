# Visão Geral do Sistema

**Versão:** 0.1.0  
**Última Atualização:** 2026-02-14

---

## 1. Introdução

### 1.1 O que é o Pigmeu Copilot

O **Pigmeu Copilot** é um sistema de automação para geração de conteúdo editorial focado em revisões de livros técnicos. O sistema utiliza técnicas de web scraping, processamento de linguagem natural via LLMs e integração com plataformas de publicação para transformar dados brutos de livros em artigos completos, estruturados e otimizados para SEO.

### 1.2 Objetivo Principal

Automatizar o ciclo completo de produção de artigos de revisão de livros técnicos:

1. **Coleta**: Extrair metadados e informações de múltiplas fontes (Amazon, Goodreads, sites de autores)
2. **Processamento**: Consolidar e enriquecer dados via IA
3. **Geração**: Criar artigos estruturados com qualidade editorial
4. **Publicação**: Publicar automaticamente no WordPress

### 1.3 Público-Alvo

- Editores de conteúdo técnico
- Blogueiros de tecnologia
- Equipes de marketing de conteúdo
- Produtores de conteúdo editorial automatizado

---

## 2. Funcionalidades Principais

### 2.1 Submissão de Livros

| Funcionalidade | Descrição |
|----------------|-----------|
| Formulário Web | Interface para submissão de dados do livro |
| API REST | Endpoint para integração programática |
| Validação de Duplicados | Impede submissão duplicada do mesmo livro |
| Agendamento | Permite agendar processamento para momento específico |
| Pipeline Configurável | Seleção de pipeline de processamento |

**Dados de Entrada:**

```json
{
  "title": "Designing Data-Intensive Applications",
  "author_name": "Martin Kleppmann",
  "amazon_url": "https://amazon.com/dp/1449373321",
  "goodreads_url": "https://goodreads.com/book/show/23463279",
  "author_site": "https://martin.kleppmann.com",
  "other_links": [],
  "textual_information": "Notas adicionais sobre o livro",
  "run_immediately": true,
  "pipeline_id": "book_review_v2",
  "content_schema_id": "default_book_review",
  "user_approval_required": false
}
```

### 2.2 Extração de Dados (Scraping)

| Fonte | Dados Extraídos |
|-------|-----------------|
| Amazon | Título, autor, ISBN, ASIN, preço, rating, capa, editora, data de publicação, idioma, páginas |
| Goodreads | Rating, reviews, gêneros, descrição |
| Sites de Autores | Biografia, outros livros, artigos relacionados |
| Links Adicionais | Dados bibliográficos complementares |

**Características do Scraper:**

- Rate limiting configurável
- Rotação de User-Agent
- Suporte a proxies
- Retry com backoff exponencial
- Renderização JavaScript via Playwright

### 2.3 Geração de Contexto

O sistema utiliza LLMs para:

1. **Resumir Conteúdo**: Processar texto de links adicionais
2. **Extrair Tópicos**: Identificar temas principais do livro
3. **Consolidar Dados**: Unificar informações de múltiplas fontes
4. **Pesquisa Web**: Buscar informações complementares na internet

### 2.4 Geração de Artigos

| Característica | Especificação |
|----------------|---------------|
| Formato | Markdown |
| Extensão | 800-1.333 palavras (configurável) |
| Estrutura | H2s temáticos + seções fixas |
| SEO | Títulos ≤60 caracteres, meta descriptions |
| Parágrafos | 3-6 sentenças por parágrafo |

**Seções do Artigo:**

1. **Introdução** (automática)
2. **3 Seções Temáticas** (baseadas em tópicos extraídos)
3. **Para quem é este livro**
4. **Prós e Contras**
5. **Sobre o Autor**
6. **Conclusão**
7. **Onde Comprar**

### 2.5 Publicação WordPress

- Integração via WordPress REST API
- Upload de imagem de capa
- Configuração de categorias e tags
- Suporte a rascunhos e publicação direta
- Link de retorno do post publicado

---

## 3. Fluxo de Processamento

### 3.1 Pipeline Padrão (Book Review v2)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE: BOOK REVIEW v2                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. AMAZON SCRAPE                                                        │
│     └── Extrai metadados da página do livro na Amazon                   │
│                                                                          │
│  2. ADDITIONAL LINKS SCRAPE                                              │
│     └── Processa links adicionais (Goodreads, site do autor, etc)       │
│     └── Usa IA para extrair dados bibliográficos                        │
│                                                                          │
│  3. SUMMARIZE ADDITIONAL LINKS                                           │
│     └── Gera resumos de cada link processado                            │
│     └── Identifica tópicos e pontos-chave                               │
│                                                                          │
│  4. CONSOLIDATE BOOK DATA                                                │
│     └── Unifica dados de todas as fontes                                │
│     └── Remove duplicatas e conflitos                                   │
│                                                                          │
│  5. INTERNET RESEARCH                                                    │
│     └── Pesquisa web sobre livro/autor                                  │
│     └── Sintetiza assuntos e temas relevantes                           │
│                                                                          │
│  6. CONTEXT GENERATION                                                   │
│     └── Gera base de conhecimento consolidada                           │
│     └── Prepara contexto para geração do artigo                         │
│                                                                          │
│  7. ARTICLE GENERATION                                                   │
│     └── Gera artigo final em markdown                                   │
│     └── Valida estrutura e contagem de palavras                         │
│                                                                          │
│  8. PUBLISHING (opcional)                                                │
│     └── Publica no WordPress                                            │
│     └── Atualiza status da submissão                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Estados da Submissão

| Status | Descrição |
|--------|-----------|
| `pending_scrape` | Aguardando início do scraping |
| `scraping_amazon` | Scraping da Amazon em andamento |
| `scraping_goodreads` | Scraping do Goodreads em andamento |
| `scraped` | Scraping concluído |
| `pending_context` | Aguardando geração de contexto |
| `context_generation` | Gerando contexto via IA |
| `context_generated` | Contexto gerado com sucesso |
| `pending_article` | Aguardando geração do artigo |
| `article_generated` | Artigo gerado |
| `ready_for_review` | Pronto para revisão humana |
| `approved` | Aprovado para publicação |
| `published` | Publicado no WordPress |
| `scraping_failed` | Falha no scraping |
| `failed` | Falha genérica |

---

## 4. Componentes do Sistema

### 4.1 API REST (FastAPI)

- **Porta**: 8000
- **Documentação**: `/docs` (Swagger), `/redoc`
- **Health Check**: `/health`

**Módulos:**

| Módulo | Prefixo | Descrição |
|--------|---------|-----------|
| Ingest | `/submit` | Submissão de livros |
| Tasks | `/tasks` | Gestão de tarefas |
| Settings | `/settings` | Configurações CRUD |
| Articles | `/articles` | Gestão de artigos |
| Operations | `/operations` | Operações auxiliares |

### 4.2 Workers (Celery)

- **Broker**: Redis
- **Backend**: Redis
- **Concorrência**: 2 workers padrão

**Tasks Principais:**

| Task | Descrição |
|------|-----------|
| `start_pipeline` | Inicia pipeline de processamento |
| `scrape_amazon_task` | Scraping da Amazon |
| `process_additional_links_task` | Processa links adicionais |
| `consolidate_bibliographic_task` | Consolida dados bibliográficos |
| `internet_research_task` | Pesquisa web |
| `generate_context_task` | Gera contexto via IA |
| `generate_article_task` | Gera artigo final |
| `publish_article_task` | Publica no WordPress |

### 4.3 Banco de Dados (MongoDB)

**Coleções:**

| Coleção | Descrição |
|---------|-----------|
| `submissions` | Submissões de livros |
| `books` | Dados extraídos dos livros |
| `summaries` | Resumos de links processados |
| `knowledge_base` | Base de conhecimento gerada |
| `articles` | Artigos gerados |
| `articles_drafts` | Rascunhos de artigos |
| `credentials` | Credenciais de serviços |
| `prompts` | Templates de prompts |
| `content_schemas` | Schemas de estrutura de conteúdo |
| `pipeline_configs` | Configurações de pipelines |

### 4.4 Interface Web (Dashboard)

- **URL**: `/ui`
- **Tecnologia**: SPA (HTML/CSS/JavaScript vanilla)
- **Funcionalidades**:
  - Listagem de tarefas com filtros
  - Detalhes de cada tarefa
  - Formulário de submissão
  - CRUD de credenciais, prompts, schemas
  - Visualização de artigos
  - Ações: retry, publicar, editar

---

## 5. Integrações Externas

### 5.1 Provedores de IA

| Provedor | Modelos Suportados | Uso Principal |
|----------|-------------------|---------------|
| OpenAI | GPT-4, GPT-3.5 | Geração de artigos |
| Groq | Llama 3.3 70B | Contexto, resumos |
| Mistral | Mistral Large | Extração de dados |
| Claude | Claude 3 | Alternativa para artigos |

### 5.2 WordPress

- Integração via REST API
- Autenticação: Application Password
- Operações: criar post, upload de mídia, categorias/tags

### 5.3 Amazon

- Scraping via Playwright
- Dados: preço, rating, ASIN, ISBN, capa

### 5.4 Goodreads

- Scraping via Playwright
- Dados: rating, reviews, gêneros

---

## 6. Configuração e Ambiente

### 6.1 Variáveis de Ambiente Obrigatórias

```bash
MONGODB_URI=mongodb://localhost:27017
MONGO_DB_NAME=pigmeu
REDIS_URL=redis://localhost:6379
```

### 6.2 Variáveis de Ambiente Opcionais

```bash
# LLM Providers
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
MISTRAL_API_KEY=...

# WordPress
WORDPRESS_URL=https://seu-site.com
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=application_password

# Aplicação
APP_ENV=development
LOG_LEVEL=INFO
```

### 6.3 Configuração de Pipelines

Pipelines são configurados na coleção `pipeline_configs` e definem:

- Sequência de steps
- Provedores de IA por step
- Prompts associados
- Delays entre steps

---

## 7. Limites e Restrições

### 7.1 Rate Limiting

| Serviço | Limite |
|---------|--------|
| Amazon | 0.5 req/s, 100 req/h |
| Goodreads | 0.3 req/s |
| LLM APIs | Conforme plano do provedor |

### 7.2 Timeouts

| Operação | Timeout |
|----------|---------|
| Task Celery | 30 minutos |
| Request HTTP | 30 segundos |
| Scraping | 60 segundos por página |

### 7.3 Validações

| Campo | Restrição |
|-------|-----------|
| Título do livro | Mínimo 1 caractere |
| Nome do autor | Mínimo 1 caractere |
| Amazon URL | URL válida obrigatória |
| Título do artigo | Máximo 60 caracteres (SEO) |
| Artigo | 800-1.333 palavras |

---

## 8. Próximos Passos

Para detalhes técnicos de cada componente, consulte:

- [Arquitetura Técnica](./02-arquitetura.md)
- [Modelo de Dados](./03-modelo-de-dados.md)
- [API REST](./04-api-rest.md)
- [Workers e Pipelines](./05-workers-pipelines.md)
