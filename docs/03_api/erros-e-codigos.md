# Erros e Códigos

## HTTP codes usados

- `200 OK`: leitura/atualização bem-sucedida.
- `201 Created`: criação bem-sucedida.
- `202 Accepted`: tarefa enfileirada para processamento assíncrono.
- `204 No Content`: exclusão sem payload de retorno.
- `400 Bad Request`: regra de negócio violada.
- `404 Not Found`: recurso inexistente.
- `422 Unprocessable Entity`: validação de payload.
- `500 Internal Server Error`: falha inesperada.

## Erros frequentes por módulo

### Submissions
- `400`: duplicidade por `amazon_url`.
- `422`: URL inválida ou campos obrigatórios ausentes.

### Tasks
- `404`: submission/book/article não encontrados.
- `400`: publicação bloqueada por necessidade de aprovação.
- `422`: draft sem `content`.

### Credentials
- `404`: credencial não encontrada.
- `422`: update sem campos válidos.

### Prompts
- `404`: prompt não encontrado.
- `422`: update sem campos válidos.

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
