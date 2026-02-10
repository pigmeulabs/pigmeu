
# REQUISITOS WORFLOW ARTIGO LIVRO


## PASSOS

1. Usuário fornece os dados iniciais sobre o livro e o autor
   1. Título completo do livro
   2. Nome do Autor
   3. Link do livro na Amazon
   4. Link do livro no Goodreads (opcional)
   5. Link do site pessoal do autor (opcional).
   6. Outros links com informações sobre o livro ou sobre o autor (Opcional)

2. Sistema persiste essas informaçõe em um documento json da collection pertinente.
   1. Define status atual como não processado

3. Extrair dados e informações sobre o livro do conteúdo da página do livro na Amazon.
   1. Informações que devem ser extraídas
      1. Título original (se houver)
      2. Nome completo do autor, ou autores caso exista mais que um.
      3. Tema principa do livro.
      4. Idioma original
      5. Idioma da edição
      6. Edição
      7. Data de publicação
      8. Editora
      9.  ISBN
      10. Total de páginas do livro
      11. Preço livro físico
      12. Preço e-book
      13. Nota na Amazon
   2. **Nota para arquitetura do sistema**: Qual são os métodos/técnicas mais indicadas para realizar essa extração? 
      1. Obter o html via HTTP request, e extraindo com base em xpaths (por exemplo).  
      2. Extrair utilizando alguma solução de scraping diretamente da página.
      3. Utilizar algum agente de IA com  acesso à internet, para que acesse a página e retorne os dados.
      4. Outra?
   3. Persistir essas informações no respectivo documento na collection.

4. Obter conhecimento e gerar contexto sobre o livro e o autor.
   1. Agente IA: Acessar todos os links disponíveis, um de cada vez e criar um texto descritivo e detalhado com as informações disponíveis em cada um a respeito do livro e do autor. 
      1. Persistir esses resumos, eles serão utilizados logo mais para geração do contexto e da base de conhecimento sobre o livro.
   2. Agente IA: Buscar na internet pela correspondência exata do título do autor:
      1. Identificar 3 links que abordam diretamente o livro.
      2. Para cada link, o Agente deverá realizar ler uma página por vez, analisar o conteúdo e escrever um resumo do conteúdo, otimizado para ser utilizado como base de conhecimento para o Agente nas interações futuras.
      3. Identificar uma lista de Tópicos, discussões, temas e termos mais relevantes a respeito do conteúdo do livro.
      4. Persistir essas informações na collection.
   3. Após a conclusão dos itens acima, o sistema deverá obter todos os resumos e todas as listas de tópicos/discussões/etc, enviar para o Agente de IA, solicitando que ele crie contexto/base de conhecimento em formato markdown, estruturado e otimizado para alimentar o agente de ia nas próximas interaçõs
      1. Persistir no banco.
