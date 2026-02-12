# Módulo Tasks

## Responsabilidade

Gerenciar ciclo de vida da submission e operações do pipeline.

## Endpoints

- `GET /tasks`
- `GET /tasks/{submission_id}`
- `PATCH /tasks/{submission_id}`
- `POST /tasks/{submission_id}/generate_context`
- `POST /tasks/{submission_id}/generate_article`
- `POST /tasks/{submission_id}/retry`
- `POST /tasks/{submission_id}/draft_article`
- `POST /tasks/{submission_id}/publish_article`
- `GET /tasks/stats`

## Repositórios envolvidos

- `SubmissionRepository`
- `BookRepository`
- `KnowledgeBaseRepository`
- `ArticleRepository`

## Integração com workers

- Entrada: `start_pipeline` (Celery)
- Contexto: `generate_context_task`
- Artigo: `generate_article_task`
- Publicação: `publish_article_task`

## Regras relevantes

- Retry limpa erros e volta status para `pending_scrape`.
- Publicação com aprovação exigida só aceita status `approved` ou `ready_for_review`.
- Draft exige `content` não vazio.
