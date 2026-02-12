# Contexto para Agentes

## Objetivo

Fornecer contexto operacional e técnico mínimo para agentes (ex.: Codex) atuarem com segurança no projeto.

## Fontes de verdade por domínio

- Rotas e contratos HTTP: `src/api/`
- Regras de dados: `src/models/` e `src/db/repositories.py`
- Índices/migrações: `src/db/migrations.py`
- Pipeline e workers: `src/workers/`
- Scrapers e integrações externas: `src/scrapers/`
- UI web: `src/static/`

## Convenções de trabalho

- Não quebrar compatibilidade de status da submission.
- Ajuste de schema deve refletir em schema + repositório + migração.
- Toda mudança de endpoint deve atualizar `docs/03_api/`.
- Toda mudança de fluxo deve atualizar `docs/01_requisitos/estados-e-transicoes-pipeline.md`.

## Riscos recorrentes

- Divergência entre status persistido e status exibido na UI.
- Chave sensível em logs/respostas.
- Mudanças em prompts sem checagem de impacto na geração.
- Dependência de serviço externo indisponível sem fallback.

## Fluxo recomendado para mudanças

1. Ler módulo alvo em `docs/05_modulos/`.
2. Ajustar código.
3. Executar testes.
4. Atualizar documentação afetada.
