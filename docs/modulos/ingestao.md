# Modulo: Ingestao de Submissoes

Atualizado em: 2026-02-13
Implementacao principal: `src/api/ingest.py`

## 1. Responsabilidade

Este modulo e a porta de entrada do fluxo de negocio. Ele recebe a intencao de gerar conteudo, valida dados e cria a entidade raiz (`submission`) que sera processada no pipeline.

## 2. Entradas e saidas

## 2.1 Entrada HTTP

- `POST /submit`
- `GET /submit/health`

## 2.2 Saida persistida

- cria documento em `submissions` com:
  - metadados do livro
  - parametros de execucao
  - status inicial
  - auditoria de criacao/atualizacao

## 2.3 Saida assicrona (opcional)

- quando `run_immediately=true`, enfileira task Celery `start_pipeline`.

## 3. Regras implementadas

- valida schema de entrada via `SubmissionCreate`.
- aplica regra de agendamento:
  - se `run_immediately=false`, `schedule_execution` e obrigatorio.
- garante defaults de sistema antes da criacao:
  - pipelines
  - credenciais
  - content schema default
- valida existencia do `pipeline_id` informado.
- valida duplicidade por `amazon_url`.

## 4. Fluxo interno detalhado

1. endpoint recebe payload.
2. chama `_ensure_system_defaults`.
3. resolve pipeline com `_ensure_pipeline_by_id`.
4. consulta duplicidade (`SubmissionRepository.check_duplicate`).
5. cria submissao (`SubmissionRepository.create`).
6. recarrega doc criado para serializar resposta.
7. se `run_immediately=true`, enfileira:
   - `start_pipeline.delay(submission_id, amazon_url, pipeline_id)`.
8. retorna `SubmissionResponse` (`201`).

## 5. Dependencias tecnicas

- repositories:
  - `SubmissionRepository`
  - `PipelineConfigRepository`
  - `CredentialRepository`
  - `ContentSchemaRepository`
- configuracao/settings:
  - helpers de bootstrap em `src/api/settings.py`
- worker gateway:
  - `src/workers/worker.py` (`start_pipeline`)

## 6. Contrato de erro

- `400`: submissao duplicada por `amazon_url`.
- `422`: pipeline invalido ou payload invalido.
- `500`: falha inesperada na criacao/enfileiramento.

## 7. Efeitos sobre modulos adjacentes

- ativa modulo `tasks` e `workers` quando run imediato.
- depende do modulo `settings` para garantir baseline de configuracao.
- alimenta `frontend-dashboard` (a task aparece em listagem apos criacao).

## 8. Limitacoes atuais

- quando `run_immediately=false`, o sistema persiste `schedule_execution`, mas nao possui scheduler interno para disparo automatico futuro.
- nao ha autenticacao no endpoint.
