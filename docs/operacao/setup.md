# Setup

Atualizado em: 2026-02-13

## 1. Objetivo

Preparar ambiente local completo para executar API, workers e UI do sistema PIGMEU.

## 2. Pre-requisitos

- Python 3.10+
- pip
- Docker + Docker Compose
- Redis e MongoDB acessiveis (local ou remoto)
- Browsers Playwright instalados para scraping baseado em navegador

## 3. Setup base do projeto

```bash
cd /home/chico/pigmeulabs/pigmeu
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 4. Subir infraestrutura local minima (Mongo + Redis)

```bash
docker compose -f infra/docker-compose.yml up -d mongo redis
```

## 5. Configurar variaveis de ambiente

Ajuste no `.env` (ou export no shell):

- `MONGODB_URI`
- `MONGO_DB_NAME`
- `REDIS_URL`
- chaves de LLM/WordPress quando necessario

Exemplo local minimo:

```env
APP_ENV=development
LOG_LEVEL=INFO
MONGODB_URI=mongodb://localhost:27017
MONGO_DB_NAME=pigmeu
REDIS_URL=redis://localhost:6379
```

## 6. Migracoes

```bash
source .venv/bin/activate
python scripts/migrate.py
```

Efeito:

- cria colecoes/indices das entidades principais.

## 7. Seed opcional de configuracoes

```bash
source .venv/bin/activate
python -m scripts.seed_prompts
python -m scripts.seed_content_schema
```

Observacao:

- mesmo sem seed manual, parte dos defaults e bootstrapada automaticamente pelos endpoints de settings/submit.

## 8. Execucao local da API

```bash
source .venv/bin/activate
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

## 9. Execucao local do worker

```bash
source .venv/bin/activate
celery -A src.workers.worker worker --loglevel=info --concurrency=2
```

## 10. URLs uteis

- API: `http://localhost:8000`
- UI: `http://localhost:8000/ui`
- OpenAPI/Swagger: `http://localhost:8000/docs`

## 11. Setup Playwright (obrigatorio para scraping Amazon)

```bash
source .venv/bin/activate
playwright install
```

Sem browser instalado, etapas de scraping baseadas em Playwright falham.

## 12. Checklist de validacao inicial

1. acessar `GET /health` e confirmar `status=ok`.
2. acessar `/ui` e confirmar carregamento da dashboard.
3. listar pipelines via `GET /settings/pipelines`.
4. criar uma task de teste em `POST /submit`.

