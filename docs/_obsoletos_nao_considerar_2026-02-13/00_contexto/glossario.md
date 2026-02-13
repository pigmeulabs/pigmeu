# Glossário

- Submission: task de entrada para processar um livro.
- Pipeline: sequência de etapas de processamento de uma submission.
- Scraping: extração de dados de páginas externas (Amazon/Goodreads).
- Knowledge Base: conteúdo em markdown com contexto consolidado do livro.
- Summary: resumo de uma fonte externa armazenado na coleção `summaries`.
- Article: conteúdo final gerado para publicação.
- Draft: versão editável do artigo (coleção `articles_drafts`).
- Prompt: template de instrução para tarefas de LLM.
- Credential: segredo/configuração de acesso a serviço externo.
- `run_immediately`: flag para enfileirar pipeline imediatamente ao criar submission.
- `schedule_execution`: data/hora planejada (persistida; sem scheduler nativo).
- `user_approval_required`: exige revisão antes de publicar.
- WordPress publish: publicação via endpoint `/wp-json/wp/v2/posts`.
