# Pigmeu Copilot - Documentação Estável

**Versão:** 0.1.0  
**Última Atualização:** 2026-02-14  
**Status:** Documentação Técnica Completa

---

## Visão Geral

O **Pigmeu Copilot** é um sistema automatizado para geração de artigos de revisão de livros técnicos, otimizados para SEO e prontos para publicação em WordPress. O sistema transforma informações de livros coletadas de múltiplas fontes (Amazon, Goodreads, sites de autores) em artigos completos e estruturados.

---

## Índice de Documentos

| Documento | Descrição |
|-----------|-----------|
| [01-visao-geral.md](./01-visao-geral.md) | Visão geral do sistema, objetivos e escopo |
| [02-arquitetura.md](./02-arquitetura.md) | Arquitetura técnica, componentes e fluxos |
| [03-modelo-de-dados.md](./03-modelo-de-dados.md) | Modelo de dados MongoDB, coleções e relacionamentos |
| [04-api-rest.md](./04-api-rest.md) | Endpoints da API REST, contratos e exemplos |
| [05-workers-pipelines.md](./05-workers-pipelines.md) | Workers Celery, pipelines de processamento |
| [06-scrapers-integracoes.md](./06-scrapers-integracoes.md) | Scrapers, extração de dados e integrações externas |
| [07-frontend-dashboard.md](./07-frontend-dashboard.md) | Interface web, componentes e fluxos de usuário |
| [08-infraestrutura-deploy.md](./08-infraestrutura-deploy.md) | Infraestrutura Docker, configuração e deploy |
| [09-requisitos-regras.md](./09-requisitos-regras.md) | Requisitos funcionais, regras de negócio e limites |

---

## Resumo Executivo

### O que o sistema faz

1. **Submissão de Livros**: Usuários submetem informações de livros técnicos via API ou interface web
2. **Extração de Dados**: Scrapers coletam metadados de Amazon, Goodreads e outras fontes
3. **Geração de Contexto**: IA processa e consolida informações em uma base de conhecimento
4. **Criação de Artigos**: Sistema gera artigos estruturados com SEO otimizado
5. **Publicação**: Artigos aprovados são publicados automaticamente no WordPress

### Stack Tecnológico

| Camada | Tecnologia |
|--------|------------|
| Backend API | FastAPI (Python 3.10+) |
| Processamento Assíncrono | Celery + Redis |
| Banco de Dados | MongoDB 7 |
| Scraping | Playwright + BeautifulSoup |
| IA/LLM | OpenAI, Groq, Mistral |
| Frontend | HTML/CSS/JavaScript (SPA) |
| Infraestrutura | Docker Compose |

### Principais Funcionalidades

- ✅ Extração automatizada de metadados de livros
- ✅ Geração de artigos via IA com estrutura SEO
- ✅ Pipeline configurável de processamento
- ✅ Dashboard web para gestão de tarefas
- ✅ CRUD de credenciais, prompts e schemas de conteúdo
- ✅ Integração com WordPress para publicação
- ✅ Sistema de retry e tratamento de erros

---

## Quick Start

```bash
# Clonar repositório
git clone https://github.com/pigmeulabs/pigmeu.git
cd pigmeu

# Configurar ambiente
cp .env.example .env
# Editar .env com suas credenciais

# Iniciar serviços
docker-compose -f infra/docker-compose.yml up --build

# Verificar saúde
curl http://localhost:8000/health
```

### URLs Principais

| Serviço | URL |
|---------|-----|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Dashboard Web | http://localhost:8000/ui |

---

## Estrutura do Projeto

```
pigmeu/
├── src/
│   ├── api/              # Endpoints FastAPI
│   │   ├── articles.py   # Gestão de artigos
│   │   ├── dependencies.py # Injeção de dependências
│   │   ├── ingest.py     # Submissão de livros
│   │   ├── operations.py # Operações auxiliares
│   │   ├── settings.py   # Configurações CRUD
│   │   └── tasks.py      # Gestão de tarefas
│   ├── db/               # Camada de persistência
│   │   ├── connection.py # Conexão MongoDB
│   │   ├── migrations.py # Migrações de schema
│   │   └── repositories.py # Repositórios CRUD
│   ├── models/           # Modelos Pydantic
│   │   ├── enums.py      # Enumerações
│   │   └── schemas.py    # Schemas de validação
│   ├── scrapers/         # Módulos de scraping
│   │   ├── amazon.py     # Scraper Amazon
│   │   ├── goodreads.py  # Scraper Goodreads
│   │   ├── extractors.py # Extratores de dados
│   │   ├── link_finder.py # Descoberta de links
│   │   ├── proxy_manager.py # Gerenciamento de proxies
│   │   ├── web_scraper.py # Scraper web genérico
│   │   └── wordpress_client.py # Cliente WordPress
│   ├── static/           # Frontend estático
│   │   ├── index.html    # SPA principal
│   │   ├── app.js        # Lógica JavaScript
│   │   └── styles.css    # Estilos CSS
│   ├── workers/          # Tasks Celery
│   │   ├── worker.py     # Configuração Celery
│   │   ├── article_tasks.py # Geração de artigos
│   │   ├── article_structurer.py # Estruturação de artigos
│   │   ├── scraper_tasks.py # Tasks de scraping
│   │   ├── link_tasks.py # Processamento de links
│   │   ├── publishing_tasks.py # Publicação WordPress
│   │   ├── llm_client.py # Cliente LLM
│   │   ├── prompt_builder.py # Construção de prompts
│   │   └── ai_defaults.py # Defaults de IA
│   ├── app.py            # Aplicação FastAPI
│   ├── config.py         # Configurações
│   └── logger.py         # Configuração de logs
├── infra/                # Infraestrutura
│   ├── docker-compose.yml # Orquestração
│   ├── Dockerfile        # Imagem API
│   └── Dockerfile.worker # Imagem Worker
├── config/               # Configurações YAML
├── docs/                 # Documentação
├── scripts/              # Scripts utilitários
├── tests/                # Testes automatizados
├── requirements.txt      # Dependências Python
└── README.md             # Este arquivo
```

---

## Contato e Suporte

**Desenvolvido por Pigmeu Labs**

- Repositório: https://github.com/pigmeulabs/pigmeu
- Licença: MIT
