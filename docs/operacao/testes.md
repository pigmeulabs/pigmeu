# Testes

Atualizado em: 2026-02-13

## 1. Objetivo

Descrever como validar comportamento funcional do sistema por testes automatizados e checagens tecnicas basicas.

## 2. Execucao da suite

```bash
source .venv/bin/activate
pytest -q
```

## 3. Pre-condicoes

- `MONGODB_URI` deve apontar para instancia acessivel.
- `MONGO_DB_NAME` deve ser apropriado para ambiente de teste.

Execucao tipica com banco local dedicado:

```bash
MONGODB_URI=mongodb://localhost:27017 MONGO_DB_NAME=pigmeu_test_local pytest -q
```

## 4. Resultado observado no estado atual

Execucao registrada em 2026-02-13:

- `45 passed, 13 errors`
- causa principal dos erros: configuracao de MongoDB (`ConfigurationError` por host SRV indisponivel no ambiente local).

## 5. Escopo coberto pela suite existente

- endpoints basicos da API
- fluxos de submissao/tasks
- validacao e estrutura de artigo (`ArticleStructurer`)
- utilitarios e componentes de scraping

## 6. Checagens complementares recomendadas no ciclo tecnico

Compilacao estatica Python:

```bash
source .venv/bin/activate
python -m compileall -q src tests scripts
```

Smoke checks manuais:

1. `GET /health`
2. `GET /tasks`
3. `GET /settings/pipelines`
4. criar submissao de teste via `/submit`

## 7. Observacoes sobre ambiente de teste

- testes que dependem de scraping/servicos externos podem exigir mocks/isolamento para execucao deterministica.
- quando executados sem isolamento de banco, podem conflitar com dados existentes (ex.: indice unico de `amazon_url`).
