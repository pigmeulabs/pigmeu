# Docker

Arquivo principal: `infra/docker-compose.yml`

## Serviços

### `api`
- Build: `infra/Dockerfile`
- Porta: `8000`
- Comando: `uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload`

### `worker`
- Build: `infra/Dockerfile.worker`
- Comando: `celery -A src.workers.worker worker --loglevel=info --concurrency=2`

### `redis`
- Imagem: `redis:7-alpine`
- Porta: `6379`

## Comandos úteis

Subir stack:

```bash
docker compose -f infra/docker-compose.yml up --build
```

Parar mantendo containers:

```bash
docker compose -f infra/docker-compose.yml stop
```

Parar e remover:

```bash
docker compose -f infra/docker-compose.yml down
```

Ver logs:

```bash
docker compose -f infra/docker-compose.yml logs -f api
docker compose -f infra/docker-compose.yml logs -f worker
```
