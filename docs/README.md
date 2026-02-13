# Documentacao Ativa do Sistema PIGMEU

Atualizado em: 2026-02-13

Este diretorio contem a documentacao oficial e ativa do sistema. O conteudo foi consolidado a partir do estado atual do codigo fonte, dos fluxos implementados na API/workers/frontend e dos wireframes historicos de operacao.

## Como esta documentacao esta organizada

- `docs/arquitetura.md`
  - documento unico de arquitetura tecnica, fluxos de ponta a ponta, componentes e trade-offs.
- `docs/api.md`
  - documento unico de contratos HTTP implementados na API FastAPI.
- `docs/modelo-de-dados.md`
  - documento unico de modelo de dados MongoDB, relacionamentos, indices e regras de persistencia.
- `docs/requisitos.md`
  - documento unico de requisitos funcionais, nao funcionais, regras de negocio e limites atuais.
- `docs/modulos/`
  - indice de modulos e um documento detalhado por modulo tecnico.
- `docs/ui-ux/`
  - documento principal de UI/UX e um documento por modulo/tela operacional.
- `docs/workers/`
  - documento principal e um documento por worker/task pipeline.
- `docs/operacao/`
  - setup, docker, env vars, execucao local e testes.
- `docs/ia-agentes/`
  - contexto tecnico objetivo para execucao por agentes e checklists operacionais.

## Estado funcional documentado

A documentacao cobre o estado implementado em `src/`:

- Backend/API: `src/app.py`, `src/api/*`
- Persistencia/Migracoes: `src/db/*`
- Modelos e validacao: `src/models/*`
- Workers assicronos: `src/workers/*`
- Scrapers e integracoes externas: `src/scrapers/*`
- Frontend web operacional: `src/static/*`

## Principios de leitura

- Esta base descreve **o que existe hoje no codigo**, nao um roadmap idealizado.
- Regras e comportamentos citados referenciam endpoints, tasks e campos reais.
- Quando houver diferenca entre wireframe e implementacao, a implementacao atual tem precedencia e a diferenca e registrada em `docs/ui-ux/*`.

## Conteudo obsoleto

A documentacao legada foi movida para:

- `docs/_obsoletos_nao_considerar_2026-02-13/`

Esse conteudo e mantido apenas para historico e **nao deve ser utilizado como contexto ativo**.
