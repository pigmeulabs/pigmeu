# Setup

## Pré-requisitos

- Python 3.10+
- Docker + Docker Compose
- Acesso ao MongoDB Atlas

## Passo a passo local

```bash
cd /home/chico/pigmeulabs/pigmeu
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edite o .env e preencha principalmente MONGODB_URI com uma URI valida
python scripts/migrate.py
docker compose -f infra/docker-compose.yml up --build
```

## Endpoints locais

- API: `http://localhost:8000`
- UI: `http://localhost:8000/ui`
- Swagger: `http://localhost:8000/docs`

## Verificação rápida

```bash
curl http://localhost:8000/health
curl http://localhost:8000/tasks
```
