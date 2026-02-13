# Ambiente e Env Vars

Atualizado em: 2026-02-13
Fonte de verdade: `src/config.py`

## 1. Variaveis suportadas

## 1.1 Banco

- `MONGODB_URI` (obrigatoria)
- `MONGO_DB_NAME` (default: `pigmeu`)

## 1.2 Fila

- `REDIS_URL` (default: `redis://localhost:6379`)

## 1.3 LLM providers

- `OPENAI_API_KEY` (opcional)
- `GROQ_API_KEY` (opcional)
- `MISTRAL_API_KEY` (opcional)

## 1.4 WordPress

- `WORDPRESS_URL` (opcional)
- `WORDPRESS_USERNAME` (opcional)
- `WORDPRESS_PASSWORD` (opcional)

## 1.5 Aplicacao

- `APP_ENV` (default: `development`)
- `LOG_LEVEL` (default: `INFO`)

## 2. Exemplo minimo local

```env
APP_ENV=development
LOG_LEVEL=INFO
MONGODB_URI=mongodb://localhost:27017
MONGO_DB_NAME=pigmeu
REDIS_URL=redis://localhost:6379
```

## 3. Exemplo com fallback WordPress por ambiente

```env
WORDPRESS_URL=https://exemplo.com
WORDPRESS_USERNAME=usuario
WORDPRESS_PASSWORD=senha-ou-app-password
```

## 4. Precedencia de credenciais WordPress em runtime

Na publicacao (`publish_article_task`):

1. tenta credencial ativa do banco (`service=wordpress`)
2. fallback para `WORDPRESS_*` do ambiente

## 5. Comportamento de parsing de settings

- leitura via Pydantic Settings (`BaseSettings`).
- `env_file=.env` e `case_sensitive=False`.
- `extra=ignore`: variaveis extras no `.env` nao quebram o startup.

## 6. Riscos e boas praticas operacionais

- manter `.env` fora de versionamento com segredos reais.
- nao depender de credenciais bootstrap hardcoded para ambiente produtivo.
- manter `MONGODB_URI` consistente entre API, worker e testes.
