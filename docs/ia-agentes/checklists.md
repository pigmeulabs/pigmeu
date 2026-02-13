# Checklists para Agentes

Atualizado em: 2026-02-13

## 1. Checklist de alteracao em API

1. identificar arquivo de rota em `src/api/*`.
2. validar schema de entrada/saida (Pydantic) em `src/models/schemas.py` quando aplicavel.
3. confirmar repository/dependencia correta em `src/api/dependencies.py`.
4. validar codigos HTTP e mensagens de erro.
5. verificar side effects de enqueue/status.
6. atualizar documentacao (`docs/api.md` + modulo relacionado).

## 2. Checklist de alteracao em workers

1. validar registro/import do task module em `src/workers/worker.py`.
2. confirmar transicoes de `status` e `current_step` na submissao.
3. garantir persistencia dos artefatos esperados por etapa.
4. validar encadeamento da proxima etapa e delays configuraveis.
5. revisar comportamento de retry/fallback.
6. atualizar `docs/workers/*.md` e docs de modulo afetado.

## 3. Checklist de alteracao em dados/repositorio

1. revisar necessidade de novo indice em `src/db/migrations.py`.
2. manter padrao de `updated_at` nos updates.
3. tratar conversao segura de ObjectId.
4. validar impacto em cleanup de retry por etapa.
5. refletir alteracoes em `docs/modelo-de-dados.md`.

## 4. Checklist de alteracao em frontend

1. alinhar `index.html`, `app.js` e `styles.css` quando necessario.
2. garantir que cada acao de UI possua endpoint existente.
3. validar estados de loading/sucesso/erro.
4. validar acessibilidade minima (`aria-label`, keyboard em cards/botoes).
5. testar responsividade basica (desktop e mobile).
6. atualizar `docs/ui-ux/*.md` e referencias de wireframe quando houver impacto.

## 5. Checklist de alteracao em configuracao (settings)

1. validar regras de negocio no backend (`settings.py`).
2. garantir coerencia entre pipelines/prompts/credentials/content schemas.
3. testar telas de configuracao que consomem os endpoints.
4. validar se alteracao impacta bootstrap de defaults.
5. documentar efeito no runtime.

## 6. Checklist de validacao final

1. rodar testes automatizados disponiveis (`pytest -q`).
2. validar endpoints criticos:
   - `/health`
   - `/tasks`
   - `/submit`
   - `/settings/pipelines`
3. validar fluxo minimo de ponta a ponta:
   - criar submissao
   - acompanhar task
   - gerar artigo
4. confirmar que docs foram atualizadas nas secoes corretas.

## 7. Checklist de seguranca operacional

1. verificar ausencia de segredos novos hardcoded.
2. confirmar que logs nao expõem valores sensiveis indevidos.
3. revisar impacto de endpoints sem auth no ambiente alvo.
