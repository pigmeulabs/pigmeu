# UI-UX: Configuracao de Pipelines

Atualizado em: 2026-02-13
Tela: secao `#pipelines-section`

## 1. Objetivo da tela

Permitir ajuste operacional das etapas de pipeline sem alterar codigo fonte.

## 2. Blocos da tela

## 2.1 Grid de pipelines (cards)

Cada card mostra:

- nome
- descricao
- usage type
- versao
- quantidade total de steps
- quantidade de steps com AI

Acao principal:

- `Configure pipeline` abre detalhe do pipeline selecionado.

## 2.2 Painel de detalhe

Mostra:

- slug, usage type e versao
- descricao
- lista de steps em cards expansivos

Cada step card traz:

- nome da etapa
- tipo (`AI`/`System`)
- descricao
- ID interno
- Usage Type da etapa
- `Step Delay (seconds)`
- para steps AI:
  - provider
  - model
  - select de credential
  - select de prompt
- botao salvar configuracao da etapa

## 3. Comportamentos de interacao

- cards de step iniciam colapsados;
- toggle expande/recolhe detalhes;
- salvar step envia somente campos suportados para o endpoint de patch;
- apos salvar com sucesso, painel recarrega detalhes para refletir estado persistido.

## 4. Regras de payload no frontend

Sempre envia:

- `delay_seconds`

Envia condicionalmente:

- `credential_id` (se o step possui select de credencial)
- `prompt_id` (se o step possui select de prompt)

Validacao local:

- `delay_seconds` deve ser inteiro >= 0.

Validacao servidor (reforcada):

- para step sem AI, `credential_id`/`prompt_id` sao rejeitados;
- `delay_seconds <= 86400`;
- IDs precisam existir.

## 5. Endpoints usados

- `GET /settings/pipelines`
- `GET /settings/pipelines/{pipeline_id}`
- `PATCH /settings/pipelines/{pipeline_id}/steps/{step_id}`

## 6. Integracao com execucao

As configuracoes salvas nesta tela impactam diretamente workers:

- `delay_seconds`
  - controla countdown antes da proxima task de step.
- `credential_id`
  - define credencial preferencial para chamadas LLM do step.
- `prompt_id`
  - define prompt preferencial da etapa.

## 7. UX operacional

- feedback textual centralizado em `pipelines-result`.
- mensagens de erro detalham validacoes retornadas pela API.
- scroll automatico para painel ao abrir pipeline pelo card.

## 8. Limitacoes atuais

- tela configura pipelines existentes; nao ha CRUD de pipelines inteiros no frontend atual.
- `links_content_v1` pode ser configurado, mas o encadeamento automatico principal continua orientado ao fluxo `book_review_v2`.
