# Worker: Link Tasks (Auxiliar)

Atualizado em: 2026-02-13
Implementacao: `src/workers/link_tasks.py`

## 1. Responsabilidade

Executar descoberta e sumarizacao de links externos para uma submissao, enriquecendo `summaries` e `knowledge_base`.

## 2. Task principal

- `find_and_summarize_links(submission_id, book_title, author)`

## 3. Fluxo de execucao

1. carrega submissao.
2. carrega book vinculado; se inexistente, cria entrada minima resiliente.
3. busca ate 3 links relevantes com `LinkFinder.search_book_links`.
4. resolve prompt de resumo por ordem de fallback:
   - `purpose=summarization`
   - `purpose=link_summarization`
   - `name=Link Summarizer`
5. para cada link valido:
   - faz fetch/parse do conteudo;
   - gera resumo;
   - grava em `summaries`.
6. se houver summaries:
   - mescla secao `External Sources` em KB;
   - atualiza `topics_index` deduplicado.

## 4. Persistencia afetada

- `summaries` (novos resumos por fonte)
- `knowledge_base` (secao adicional de fontes externas)
- `books` (cria book minimo se necessario)

## 5. Status no produto

- task implementada e registrada no worker.
- nao faz parte do encadeamento padrao iniciado por `POST /submit` no estado atual.

## 6. Dependencias

- repositories:
  - submission/book/summary/prompt/kb
- utilitarios:
  - `LinkFinder`

## 7. Uso recomendado

Este worker e util para enriquecimento adicional sob demanda ou para extensoes futuras de pipeline, sem impactar o fluxo principal atual.
