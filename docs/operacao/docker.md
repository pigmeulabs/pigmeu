# Docker

Atualizado em: 2026-02-13
Arquivo principal: `infra/docker-compose.yml`

## 1. Objetivo

Executar stack completa do sistema em ambiente containerizado.

## 2. Servicos da stack

- `api`
  - FastAPI + UI estatica
  - porta exposta: `8000`
- `worker`
  - Celery worker
  - consome Redis e Mongo
- `mongo`
  - banco de dados principal
  - porta exposta: `27017`
- `redis`
  - broker/backend Celery
  - porta exposta: `6379`

## 3. Comandos principais

## 3.1 Subir stack completa

```bash
docker compose -f infra/docker-compose.yml up --build
```

## 3.2 Subir apenas dependencias de infra

```bash
docker compose -f infra/docker-compose.yml up -d mongo redis
```

## 3.3 Acompanhar logs

```bash
docker compose -f infra/docker-compose.yml logs -f api
docker compose -f infra/docker-compose.yml logs -f worker
```

## 3.4 Encerrar stack

```bash
docker compose -f infra/docker-compose.yml down
```

## 4. Variaveis de ambiente no compose

- `env_file` carrega variaveis padrao do projeto.
- variaveis em bloco `environment` do compose sobrescrevem `env_file` quando houver conflito.
- compose ja configura `MONGODB_URI` interno apontando para `mongo` em rede docker (`mongodb://mongo:27017`).

## 5. Fluxo esperado em container

1. subir stack.
2. API executa startup e migracoes automaticamente.
3. worker registra tasks e aguarda jobs.
4. usuario acessa UI em `http://localhost:8000/ui`.

## 6. Diagnostico rapido

- API sem resposta:
  - verificar logs do container `api`.
  - confirmar readiness de `mongo` e `redis`.
- tasks nao processam:
  - verificar logs do `worker`.
  - confirmar `REDIS_URL`/`MONGODB_URI` alinhados.
- erro de scraping Amazon:
  - validar que imagem/ambiente tem dependencias Playwright necessarias.
