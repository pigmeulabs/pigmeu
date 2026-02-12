# Módulo Article Generation

## Responsabilidade

Gerar artigo markdown a partir de metadados de livro + knowledge base, validando estrutura mínima.

## Componentes principais

- `src/workers/article_tasks.py`
- `src/workers/article_structurer.py`
- `src/workers/llm_client.py`

## Fluxo

1. Busca `submission`, `book` e `knowledge_base`.
2. Extrai tópicos (LLM + fallback determinístico).
3. Gera artigo (LLM + fallback template).
4. Valida regras estruturais.
5. Persiste em `articles` com `validation_report`.
6. Atualiza status da submission.

## Regras de validação (modo estrito)

- 1 H1 obrigatório.
- Exatamente 8 H2.
- Pelo menos 1 H2 com 2-4 H3.
- Word count total entre 800 e 1333.
- Parágrafos entre 50 e 100 palavras.
- H1 com no máximo 60 caracteres.

## Fallbacks

- Se LLM falhar, o módulo usa tópicos e template determinísticos para não bloquear pipeline.
- Se validação estrita falhar após retries, ainda pode salvar resultado fallback para continuidade operacional.

## Saídas persistidas

- `articles.content`
- `articles.word_count`
- `articles.validation_report`
- `articles.topics_used`
