# Índices e Migrações

## Migração atual

Arquivo: `src/db/migrations.py`

Execução:

```bash
python scripts/migrate.py
```

A API também executa migrações no startup (`lifespan`).

## Índices por coleção

### `submissions`
- `(status ASC, created_at DESC)`
- `TEXT(title, author_name)`
- `UNIQUE(amazon_url)`

### `books`
- `UNIQUE(submission_id)`
- `UNIQUE(extracted.isbn)` sparse

### `summaries`
- `(book_id ASC, created_at DESC)`
- `(source_domain ASC)`

### `knowledge_base`
- `(book_id ASC)` sparse
- `(submission_id ASC)` sparse

### `articles`
- `(book_id ASC, created_at DESC)`
- `(submission_id ASC, created_at DESC)` sparse
- `(wordpress_post_id ASC)` sparse

### `articles_drafts`
- `UNIQUE(article_id)`

### `credentials`
- `(service ASC, active ASC)`
- `(name ASC)`

### `prompts`
- `UNIQUE(name)`
- `(purpose ASC, active ASC)`
- `(model_id ASC)`

## Observações operacionais

- Índices únicos podem causar erro de gravação se já houver dados conflitantes.
- A coleção `books` usa `submission_id` único; cada submission mantém um registro de metadados consolidado.
- Alterações de schema devem ser acompanhadas de update em:
  - `src/models/schemas.py`
  - `src/db/repositories.py`
  - `src/db/migrations.py`
