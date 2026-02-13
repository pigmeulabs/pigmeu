# Modulo: Gestao de Artigos

Atualizado em: 2026-02-13
Implementacao principal: `src/api/articles.py`

## 1. Responsabilidade

Fornecer edicao manual de artigos ja persistidos, permitindo ajustes editoriais apos geracao automatica e antes/depois da publicacao.

## 2. Endpoint

- `PATCH /articles/{article_id}`

## 3. Campos permitidos para atualizacao

O endpoint aplica whitelist explicita:

- `title`
- `content`
- `status`
- `validation_report`
- `wordpress_post_id`
- `wordpress_url`

Qualquer outro campo enviado e ignorado.

Se nenhum campo valido for informado, retorna `422`.

## 4. Fluxo interno

1. valida existencia do artigo por ID.
2. filtra payload pelos campos permitidos.
3. executa update via `ArticleRepository.update`.
4. recarrega artigo atualizado.
5. retorna snapshot resumido.

## 5. Relacao com outros modulos

- `tasks`
  - salva draft via `/tasks/{id}/draft_article`.
  - este modulo (`/articles/{id}`) cobre update direto do artigo principal.
- `workers/article_tasks`
  - cria artigo inicial e validation_report.
- `workers/publishing_tasks`
  - atualiza campos de publicacao WordPress no mesmo documento.

## 6. Casos de uso principais

- corrigir titulo e corpo apos revisao humana;
- atualizar status editorial;
- ajustar metadados de publicacao quando necessario;
- manter `validation_report` sincronizado com regras internas.

## 7. Limitacoes atuais

- nao ha controle de permissao (sem auth);
- endpoint nao aplica workflow formal de aprovacao, apenas atualiza campos permitidos;
- nao cria historico de versoes do artigo (apenas ultimo estado persistido).
