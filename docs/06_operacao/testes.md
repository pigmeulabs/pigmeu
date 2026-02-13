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

## Teste manual mínimo de fluxo (UI wireframes)

1. Abrir `http://localhost:8000/ui` e validar navegação lateral completa.
2. Em Book Review, criar task com campos obrigatórios e validar erro de obrigatoriedade quando faltar dado.
3. Desmarcar `Run immediately` e validar exigência de `Schedule execution`.
4. Inserir `Additional Content Link` dinâmico e validar inclusão/remoção sem reload.
5. Em Credentials, abrir modal via `Create Credential`, criar credencial e validar exibição em card.
6. Na listagem de credenciais, validar ações `active/inactive`, `edit` e `delete`.
7. Em Prompts, abrir modal via `Create Prompt`, preencher identificação + configuração técnica + conteúdo e salvar.
8. Validar dependência de seleção `Provider -> Credential` e `Provider -> Model` no modal de prompt.
9. Na listagem de prompts, validar `expand/collapse` com exibição completa de `System Prompt` e `User Prompt`.
10. No detalhe da task, acionar geração de contexto/artigo, salvar draft, editar artigo e publicar com credenciais válidas.
