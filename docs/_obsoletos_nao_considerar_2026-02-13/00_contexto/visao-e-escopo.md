# Visão e Escopo

## Visão do produto

O PIGMEU é um sistema para gerar artigos de review de livros a partir de dados coletados da Amazon/Goodreads e de fontes externas, com fluxo de revisão e publicação em WordPress.

## Objetivos

- Reduzir tempo operacional de produção de artigos.
- Padronizar estrutura e qualidade mínima dos conteúdos.
- Permitir operação por dashboard web com ações de pipeline.
- Suportar múltiplos provedores LLM (OpenAI, Groq, Mistral).

## Escopo funcional atual

- Cadastro de tasks de livro (`/submit`).
- Pipeline de scraping (Amazon + Goodreads) e geração de contexto.
- Busca e sumarização de links externos.
- Geração e validação de artigo com estrutura definida.
- CRUD de credenciais e prompts.
- Edição de artigo/draft.
- Publicação em WordPress via REST API.
- Dashboard web para operação do fluxo.

## Fora de escopo atual

- Autenticação/autorização de usuários na API/UI.
- Scheduler de execução baseado em `schedule_execution` (campo é persistido, mas não há worker agendador nativo).
- Auditoria completa com trilha por usuário.
- Workflow de aprovação formal com endpoint dedicado para transição `approved`.

## Stakeholders

- Operação editorial: cria tasks, revisa e publica artigos.
- Engenharia: mantém pipeline, integrações e infraestrutura.
- Produto: define critérios de qualidade, escopo e priorização.

## Contexto técnico resumido

- API: FastAPI.
- Background jobs: Celery + Redis.
- Banco: MongoDB (Motor).
- Scraping: Playwright + BeautifulSoup.
- LLM: OpenAI-compatible clients.
