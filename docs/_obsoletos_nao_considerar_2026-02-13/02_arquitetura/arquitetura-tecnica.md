# Arquitetura Técnica

## Componentes

- API FastAPI (`src/app.py`)
- Workers Celery (`src/workers/*.py`)
- Redis (broker/backend de fila)
- MongoDB Atlas (persistência)
- UI web estática (`src/static/`)
- Integrações externas:
  - Amazon/Goodreads (scraping)
  - Web pages externas (link finder)
  - WordPress REST API
  - Provedores LLM (OpenAI/Groq/Mistral)

## Diagrama lógico

```text
[UI / Client]
    |
    v
[FastAPI]
    |  \__ leitura/escrita __ [MongoDB]
    |
    +-- enqueue --> [Redis/Celery] --> [Workers]
                                 |        |
                                 |        +--> Amazon/Goodreads
                                 |        +--> Fontes externas
                                 |        +--> LLM providers
                                 |        +--> WordPress API
                                 |
                                 +--> atualiza MongoDB
```

## Fluxos principais

### Fluxo de ingestão
1. Cliente envia `POST /submit`.
2. API valida e grava submission.
3. Se `run_immediately=true`, enfileira `start_pipeline`.

### Fluxo de scraping/contexto
1. Worker executa scrape Amazon.
2. Worker enriquece com Goodreads.
3. Worker gera contexto em markdown.
4. Worker de links externos pode rodar em paralelo para enriquecer `knowledge_base`.

### Fluxo de artigo
1. Worker de artigo busca submission/book/kb.
2. Extrai tópicos e gera artigo validado.
3. Salva artigo e atualiza estado da submission.

### Fluxo de publicação
1. API valida pré-condição de publicação.
2. Enfileira `publish_article_task`.
3. Worker publica no WordPress e persiste metadados.

## Camadas de código

- `src/api/`: contratos HTTP e orquestração de entrada.
- `src/db/`: conexão, migrações e repositórios.
- `src/workers/`: orquestração assíncrona e integrações.
- `src/scrapers/`: scraping e clientes externos.
- `src/models/`: enums e schemas.
