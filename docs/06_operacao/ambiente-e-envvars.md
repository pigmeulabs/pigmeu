# Ambiente e Variáveis

## Fonte de configuração

Classe `Settings` em `src/config.py` (Pydantic Settings), com leitura de `.env`.

## Variáveis suportadas

- `MONGODB_URI` (obrigatória)
- `MONGO_DB_NAME` (default: `pigmeu`)
- `REDIS_URL` (default: `redis://localhost:6379`)
- `OPENAI_API_KEY` (opcional, mas necessária para OpenAI)
- `GROQ_API_KEY` (opcional)
- `MISTRAL_API_KEY` (opcional)
- `WORDPRESS_URL` (opcional)
- `WORDPRESS_USERNAME` (opcional)
- `WORDPRESS_PASSWORD` (opcional)
- `APP_ENV` (default: `development`)
- `LOG_LEVEL` (default: `INFO`)

## Exemplo mínimo `.env`

```env
APP_ENV=development
LOG_LEVEL=INFO
MONGODB_URI=mongodb+srv://...
MONGO_DB_NAME=pigmeu
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...
WORDPRESS_URL=https://example.com
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=senha
```

## Observações

- Configuração aceita variáveis extras (`extra=ignore`).
- Para publicação WordPress, é necessário configurar credenciais em `.env` ou em `credentials` ativos.
