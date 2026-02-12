# Testes

## Suite automatizada

Executar:

```bash
source .venv/bin/activate
pytest -q
```

## Verificação de sintaxe/compilação

```bash
python -m compileall -q src tests scripts
node --check src/static/app.js
```

## Áreas cobertas atualmente

- App e health endpoints
- Endpoints de ingest/tasks/settings
- Regras de geração/validação de artigo
- Scrapers e fluxo de workers (cenários unitários)

## Teste manual mínimo de fluxo

1. Criar submission via UI (`/ui`) ou `POST /submit`.
2. Verificar progressão em `GET /tasks/{id}`.
3. Acionar geração de contexto/artigo no modal.
4. Editar e salvar draft.
5. Publicar (com credenciais WordPress válidas).
