# Erros e Códigos

## HTTP codes usados

- `200 OK`: leitura/atualização bem-sucedida.
- `201 Created`: criação bem-sucedida.
- `202 Accepted`: tarefa enfileirada para processamento assíncrono.
- `204 No Content`: exclusão sem payload de retorno.
- `400 Bad Request`: regra de negócio violada.
- `404 Not Found`: recurso inexistente.
- `409 Conflict`: conflito de unicidade ou estado.
- `422 Unprocessable Entity`: validação de payload.
- `500 Internal Server Error`: falha inesperada.

## Erros frequentes por módulo

### Submissions
- `400`: duplicidade por `amazon_url`.
- `422`: URL inválida ou campos obrigatórios ausentes.
- `422`: `schedule_execution` ausente quando `run_immediately=false`.

### Tasks
- `404`: submission/book/article não encontrados.
- `400`: publicação bloqueada por necessidade de aprovação.
- `422`: draft sem `content`.

### Credentials
- `404`: credencial não encontrada.
- `422`: create/update sem campos obrigatórios.
- `422`: combinação inválida de campos por tipo de serviço.

### Prompts
- `404`: prompt não encontrado.
- `409`: `name` duplicado.
- `422`: create/update sem campos obrigatórios (`name`, `provider`, `credential_id`, `model_id`, `system_prompt`, `user_prompt`).
- `422`: `temperature` ou `max_tokens` fora da faixa permitida.

### Articles
- `404`: artigo não encontrado.
- `422`: nenhum campo permitido enviado em `PATCH`.

## Formato típico de erro

```json
{
  "detail": "mensagem de erro"
}
```

Ou validação do FastAPI/Pydantic:

```json
{
  "detail": [
    {
      "loc": ["body", "campo"],
      "msg": "descrição",
      "type": "..."
    }
  ]
}
```
