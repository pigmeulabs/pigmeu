# Infraestrutura e Deploy

**Versão:** 0.1.0  
**Última Atualização:** 2026-02-14

---

## 1. Visão Geral

O Pigmeu Copilot é containerizado usando Docker e pode ser executado localmente com Docker Compose ou implantado em ambientes de produção usando orquestradores como Kubernetes.

### 1.1 Stack de Infraestrutura

| Componente | Tecnologia | Versão |
|------------|------------|---------|
| Backend API | FastAPI (Python) | 3.10+ |
| Workers | Celery | 5.x |
| Broker | Redis | 7 |
| Banco de Dados | MongoDB | 7 |
| Scraping | Playwright | Latest |
| Orquestração | Docker Compose | Latest |

---

## 2. Docker Compose

### 2.1 Arquivo Principal

**Arquivo:** [`infra/docker-compose.yml`](../../infra/docker-compose.yml)

```yaml
services:
  api:
    build: 
      context: ..
      dockerfile: infra/Dockerfile
    env_file:
      - ../.env
    container_name: pigmeu-api
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017
      - MONGO_DB_NAME=pigmeu
      - REDIS_URL=redis://redis:6379
      - APP_ENV=development
      - LOG_LEVEL=INFO
    depends_on:
      - redis
      - mongo
    volumes:
      - ../:/app
    command: uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - pigmeu-network

  worker:
    build:
      context: ..
      dockerfile: infra/Dockerfile.worker
    env_file:
      - ../.env
    container_name: pigmeu-worker
    environment:
      - MONGODB_URI=mongodb://mongo:27017
      - MONGO_DB_NAME=pigmeu
      - REDIS_URL=redis://redis:6379
      - APP_ENV=development
      - LOG_LEVEL=INFO
    depends_on:
      - redis
      - mongo
    volumes:
      - ../:/app
    command: celery -A src.workers.worker worker --loglevel=info --concurrency=2
    networks:
      - pigmeu-network

  redis:
    image: redis:7-alpine
    container_name: pigmeu-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - pigmeu-network

  mongo:
    image: mongo:7
    container_name: pigmeu-mongo
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - pigmeu-network

volumes:
  redis_data:
  mongo_data:

networks:
  pigmeu-network:
    driver: bridge
```

### 2.2 Variáveis de Ambiente

#### Obrigatórias

| Variável | Descrição | Exemplo |
|----------|------------|---------|
| `MONGODB_URI` | String de conexão MongoDB | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | Nome do banco de dados | `pigmeu` |
| `REDIS_URL` | URL do Redis | `redis://localhost:6379` |

#### Opcionais - LLM

| Variável | Descrição |
|----------|------------|
| `OPENAI_API_KEY` | Chave API OpenAI |
| `GROQ_API_KEY` | Chave API Groq |
| `MISTRAL_API_KEY` | Chave API Mistral |

#### Opcionais - WordPress

| Variável | Descrição |
|----------|------------|
| `WORDPRESS_URL` | URL do site WordPress |
| `WORDPRESS_USERNAME` | Usuário WordPress |
| `WORDPRESS_PASSWORD` | Application Password |

#### Opcionais - App

| Variável | Default | Descrição |
|----------|---------|-----------|
| `APP_ENV` | `development` | Ambiente (development/production) |
| `LOG_LEVEL` | `INFO` | Nível de logging |

---

## 3. Dockerfiles

### 3.1 Dockerfile API

**Arquivo:** [`infra/Dockerfile`](../../infra/Dockerfile)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema (para Playwright)
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    fonts-liberation \
    fonts-unifont \
    fonts-noto-color-emoji \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libfontconfig1 \
    libfreetype6 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libxrender1 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
ENV PIP_DEFAULT_TIMEOUT=180
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright Chromium
RUN playwright install chromium

# Copiar código
COPY . .

# Criar diretório de logs
RUN mkdir -p logs

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Iniciar aplicação
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 Dockerfile Worker

**Arquivo:** [`infra/Dockerfile.worker`](../../infra/Dockerfile.worker)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
ENV PIP_DEFAULT_TIMEOUT=180
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright Chromium
RUN playwright install chromium

# Copiar código
COPY . .

# Criar diretório de logs
RUN mkdir -p logs

# Iniciar worker
CMD ["celery", "-A", "src.workers.worker", "worker", "--loglevel=info", "--concurrency=2"]
```

---

## 4. Configuração de Ambiente

### 4.1 Arquivo .env

**Arquivo:** `.env`

```bash
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGO_DB_NAME=pigmeu

# Redis
REDIS_URL=redis://localhost:6379

# LLM Providers
OPENAI_API_KEY=sk-your-openai-key
GROQ_API_KEY=gsk_your-groq-key
MISTRAL_API_KEY=your-mistral-key

# WordPress
WORDPRESS_URL=https://your-wordpress-site.com
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=app_password_generated_in_wp

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

### 4.2 Exemplo .env

```bash
# MongoDB (local com Docker)
MONGODB_URI=mongodb://mongo:27017
MONGO_DB_NAME=pigmeu

# Redis (local com Docker)
REDIS_URL=redis://redis:6379

# LLM Providers
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx

# WordPress
WORDPRESS_URL=https://analisederequisitos.com.br
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=xxxx xxxx xxxx xxxx xxxx

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

---

## 5. Execução Local

### 5.1 Iniciar Serviços

```bash
# Navegar para diretório do projeto
cd pigmeu

# Criar arquivo .env
cp .env.example .env
# Editar .env com suas credenciais

# Iniciar todos os serviços
docker-compose -f infra/docker-compose.yml up --build

# Ou em background
docker-compose -f infra/docker-compose.yml up -d --build
```

### 5.2 Verificar Status

```bash
# Verificar containers
docker-compose -f infra/docker-compose.yml ps

# Ver logs da API
docker logs pigmeu-api

# Ver logs do worker
docker logs pigmeu-worker

# Ver logs do Redis
docker logs pigmeu-redis

# Ver logs do MongoDB
docker logs pigmeu-mongo
```

### 5.3 Acessar Serviços

| Serviço | URL |
|---------|-----|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Dashboard | http://localhost:8000/ui |
| MongoDB | localhost:27017 |
| Redis | localhost:6379 |

### 5.4 Health Checks

```bash
# API
curl http://localhost:8000/health

# Redis
redis-cli ping

# MongoDB
mongosh --eval "db.adminCommand('ping')"
```

### 5.5 Comandos Úteis

```bash
# Parar serviços
docker-compose -f infra/docker-compose.yml down

# Parar e remover volumes
docker-compose -f infra/docker-compose.yml down -v

# Rebuild de um serviço específico
docker-compose -f infra/docker-compose.yml up -d --build api

# Escalar workers
docker-compose -f infra/docker-compose.yml up -d --scale worker=4
```

---

## 6. Produção

### 6.1 Considerações de Produção

1. **Segurança**
   - Não expor portas desnecessárias
   - Usar secrets do Docker/Kubernetes
   - Habilitar HTTPS/TLS
   - Validar todas as entradas

2. **Performance**
   - Aumentar concorrência de workers
   - Configurar limits de memória/CPU
   - Usar Redis com persistência
   - Configurar MongoDB com replicação

3. **Monitoramento**
   - Logs centralizados
   - Métricas de saúde
   - Alertas

### 6.2 Exemplo de Configuração de Produção

```yaml
# docker-compose.prod.yml
services:
  api:
    build:
      context: .
      dockerfile: infra/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo-primary:27017,mongo-secondary:27017/?replicaSet=rs0
      - REDIS_URL=redis://redis:6379
      - APP_ENV=production
      - LOG_LEVEL=warning
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    restart: unless-stopped

  worker:
    build:
      context: .
      dockerfile: infra/Dockerfile.worker
    environment:
      - MONGODB_URI=mongodb://mongo-primary:27017,mongo-secondary:27017/?replicaSet=rs0
      - REDIS_URL=redis://redis:6379
      - APP_ENV=production
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '2'
          memory: 2G
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  mongo:
    image: mongo:7
    command: mongod --replSet rs0
    volumes:
      - mongo_data:/data/db
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### 6.3 Kubernetes (Opcional)

Para implantações em Kubernetes, você pode criar manifestos YAML para:

- Deployments (API, Worker)
- Services
- ConfigMaps
- Secrets
- Ingress
- PersistentVolumeClaims

---

## 7. Banco de Dados

### 7.1 Conexão

O sistema usa o driver **Motor** (async MongoDB driver):

```python
# src/db/connection.py
from motor.motor_asyncio import AsyncIOMotorClient

async def get_database() -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(settings.mongodb_uri)
    return client[settings.mongo_db_name]
```

### 7.2 Migrações

```python
# src/db/migrations.py
async def run_migrations():
    db = await get_database()
    
    # Criar índices
    await db.submissions.create_index("amazon_url", unique=True)
    await db.submissions.create_index("status")
    await db.submissions.create_index("created_at")
    
    # Popular dados iniciais
    await _seed_pipelines(db)
    await _seed_prompts(db)
    await _seed_content_schemas(db)
```

### 7.3 Backups

```bash
# Backup completo
mongodump --uri="mongodb://localhost:27017" --out=./backups/$(date +%Y%m%d)

# Backup de coleção específica
mongodump --uri="mongodb://localhost:27017" --collection=submissions --db=pigmeu

# Restore
mongorestore --uri="mongodb://localhost:27017" ./backups/20260214/
```

---

## 8. Celery

### 8.1 Configurações de Workers

```python
# Configurações de timeout
task_time_limit = 30 * 60  # 30 minutos
task_soft_time_limit = 25 * 60  # 25 minutos (soft limit)

# Retry
task_acks_late = True
task_reject_on_worker_lost = True
```

### 8.2 Monitoramento (Flower)

```bash
# Instalar
pip install flower

# Executar
celery -A src.workers.worker flower --port=5555
```

Acesse: http://localhost:5555

---

## 9. SSL/TLS (Produção)

### 9.1 Usando Nginx como Reverse Proxy

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 10. CI/CD

### 10.1 Exemplo de GitHub Actions

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: |
          docker-compose -f infra/docker-compose.yml build
      
      - name: Run tests
        run: |
          docker-compose -f infra/docker-compose.yml run api pytest
      
      - name: Deploy to server
        run: |
          # Seu script de deploy
```

---

## 11. Troubleshooting

### 11.1 Problemas Comuns

| Problema | Solução |
|----------|---------|
| API não inicia | Verificar variáveis de ambiente |
| Worker não conecta ao Redis | Verificar REDIS_URL |
| Worker não conecta ao MongoDB | Verificar MONGODB_URI |
| Scraping falha | Verificar conectividade com internet |
| LLM retorna erro | Verificar API keys |

### 11.2 Logs

```bash
# Ver todos os logs
docker-compose -f infra/docker-compose.yml logs

# Filtrar por serviço
docker-compose -f infra/docker-compose.yml logs api

# Seguir logs em tempo real
docker-compose -f infra/docker-compose.yml logs -f
```

---

## Próximos Passos

- [Requisitos e Regras de Negócio](./09-requisitos-regras.md)
