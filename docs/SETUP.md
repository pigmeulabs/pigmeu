# Setup & Installation Guide

## Prerequisites

- Python 3.10+
- Docker & Docker Compose
- MongoDB Atlas account (already configured)
- Git

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/pigmeulabs/pigmeu.git
cd pigmeu
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your credentials (already has MongoDB URI)
```

### 5. Run Database Migrations
```bash
python scripts/migrate.py
```

Expected output:
```
🚀 Starting migrations...

✓ submissions
✓ books
✓ summaries
✓ knowledge_base
✓ articles
✓ articles_drafts
✓ credentials
✓ prompts

🎉 All migrations completed!
```

### 6. Start Local Services with Docker Compose
```bash
docker-compose -f infra/docker-compose.yml up --build
```

This will start:
- **FastAPI API**: http://localhost:8000
- **Celery Worker**: Processing background jobs
- **Redis**: Cache and task queue

### 7. Verify Setup

Check health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "app": "Pigmeu Copilot API",
  "environment": "development"
}
```

View API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables Guide

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB Atlas connection string | `mongodb+srv://...` |
| `MONGO_DB_NAME` | Database name | `pigmeu` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `WORDPRESS_URL` | WordPress blog URL | `https://example.com` |
| `WORDPRESS_USERNAME` | WordPress admin username | `admin` |
| `WORDPRESS_PASSWORD` | WordPress admin password | `password` |
| `APP_ENV` | Environment (development/production) | `development` |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |

## Running Commands

### Run API Only (without Docker)
```bash
uvicorn src.app:app --reload
```

### Run Worker Only (without Docker)
```bash
celery -A src.workers.worker worker --loglevel=info
```

### Run Migrations Manually
```bash
python scripts/migrate.py
```

### View Logs
```bash
# API logs
tail -f logs/app.log

# Worker logs (in docker-compose)
docker-compose logs -f worker
```

## Troubleshooting

### MongoDB Connection Error
- Verify `MONGODB_URI` is correct in `.env`
- Check IP whitelist in MongoDB Atlas Network Access
- Ensure credentials are correct

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Redis Connection Error
- Ensure Redis is running: `docker-compose ps redis`
- Verify `REDIS_URL` in `.env`

### Playwright Browser Installation
If Playwright fails to install browsers:
```bash
playwright install
```

## Running Tests
```bash
pytest -v
pytest --cov=src  # With coverage
```

## Stopping Services
```bash
# Stop but keep containers
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything (including volumes)
docker-compose down -v
```

## Next Steps

After setup, see [API.md](../docs/API.md) for endpoint documentation and usage examples.
