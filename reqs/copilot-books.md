
# PIGMEU COPILOT [BOOK REVIEW]

## ESCOPO MACRO

Desenvolver um sistema automatizado para gerar artigos de review de livros técnicos, otimizados para SEO e prontos para publicação em WordPress, a partir de informações e dados extraídos de páginas de livros na Amazon, Goodreads, sites pessoais dos autores e outras fontes relevantes. 

O objetivo principal é automatizar a criação de artigos críticos e analíticos sobre livros, reduzindo o tempo de produção manual e garantindo consistência editorial, técnica e de otimização para mecanismos de busca.

## REQUISITOS GLOBAIS

### BANCO DE DADOS MONGODB


## RESULTADO FINAL ESPERADO ARTIGO DE REVIEW

Ao final da execução do fluxo, o resultado esperado é um artigo de review completo, estruturado e otimizado para SEO, adequado para publicação em um blog WordPress através de sua API. O artigo deve conter a seguinte estrutura e características:

1. **Características**
   1. Total de palavras: 800–1.333 (excluindo metadados e seções fixas curtas).
   2. Parágrafos:
      1. Mínimo: 3 frases (≈50 palavras).
      2. Máximo: 6 frases (≈100 palavras).
      3. Média ideal: 4–5 frases (≈70–80 palavras).
   3. Seções (H2):
      1. 3 seções temáticas (variáveis) + 5 seções fixas (obrigatórias).
      2. seção com subseções (H3): 2–4 H3s por H2.
   4.  Hierarquia de títulos:
       1.  H1: Título principal (único).
       2.  H2: 8 no total (3 temáticas + 5 fixas).
       3.  H3: Apenas 1 H2 pode conter H3s (2–4 itens).

2. **Estrutura do Artigo**  

```markdown
   
- Título do Artigo (≤60 caracteres)
   - H2: Introdução ao Tema do Livro Conteúdo mínimo: 150 palavras (Contexto geral, relevância do tema para o público-alvo)
   - H2: Contexto e Motivação Conteúdo mínimo: 150 palavras (Problemas que o livro resolve, lacunas na literatura)
   - H2: Impacto e Aplicabilidade Conteúdo mínimo: 150 palavras (Aplicação prática dos conceitos, casos de uso)
   - H2: [Tópico Específico do Livro] (ex.: Metodologia, Framework, Estudo de Caso) Conteúdo mínimo: 200 palavras
      - H3: [Subtema 1] Conteúdo mínimo: 80 palavras
      - H3: [Subtema 2] Conteúdo mínimo: 80 palavras
      - H3: [Subtema 3] (opcional) Conteúdo mínimo: 80 palavras
      - H3: [Subtema 4] (opcional) Conteúdo mínimo: 80 palavras
   - H2: Detalhes do Livro Conteúdo mínimo: 100 palavras (Metadados técnicos: autor, ISBN, editora, links para Goodreads/Amazon)
   - H2: Sobre o Autor Conteúdo mínimo: 100 palavras (Biografia resumida, principais obras)
   - H2: Download Conteúdo mínimo: 50 palavras (Links para compra/download legal do livro)
   - H2: Assuntos Relacionados Conteúdo mínimo: 80 palavras (Lista de tópicos com links internos para SEO)
   - H2: Artigos Recomendados Conteúdo mínimo: 80 palavras (3-5 artigos do site com links)
```

## INTERFACE DE USUÁRIO

Requisitos relacionados à interface de usuário para o gerenciamento dos livros e autores, bem como para a visualização dos dados extraídos e do contexto gerado:

- **Gerenciamento Web**
   - Interface web simples e intuitiva.
   - Responsiva e acessível via qualquer dispositivo com navegador moderno.
   - Utilizar frameworks e tecnologias open-source de UI/UX para ganhar agilidade no desenvolvimento e garantir uma boa experiência do usuário.

---

- **Requisitos Funcionais e de Interface**

Deverão ser disponibilziados na aplicação web os seguintes módulos:

1. **Manter tarefas**
   1. Cadastro e agendamento das tarefas de extração de dados, e criação do artigo completo.
   2. Diponibilizar para o usuário uma interface para cadastrar os dados iniciais do livro e do autor, como título, nome do autor, links relevantes, etc.
   3. Disponibilizar lista de tarefas cadastradas, com status de processamento (não processado, em andamento, concluído, etc).
   4. Visualizar detalhes da tarefa
      1. Para cada tarefa cadastrada, o usuário deve poder acessar uma página de detalhes, onde poderá visualizar todas as informações extraídas até o momento, bem como o contexto gerado e o status atual do processo.
      2. ve ser possível alterar manualmente as informações geradas, caso o usuário deseje corrigir ou complementar os dados extraídos automaticamente. (Informações do artigo de review, ou informações sobre o livro e o autor).
2. **Interface de configurações**
   1. Credenciais: disponibilizar uma interface para o usuário inserir e gerenciar as credenciais necessárias para o funcionamento do sistema:
      1.  Credenciais de API dos modelos de IA
      2.  Credenciais de do WordPress.
   2.  Prompts: disponibilizar uma interface para o usuário incluir, editar e  visualizar os prompts utilizados pelo agente de IA para a extração de dados, geração de contexto e criação do artigo de review. 
      1. Deverá ser possível informar:
         1. Nome do prompt
         2. Descrição do propósito do prompt
         3. System prompt
         4. User prompt
         5. Selecionar o modelo de IA (cadastrado na seção de credenciais)
         6. Parametros de geração (temperatura, max tokens, etc)
         7. Outras configurações relevantes para a execução do prompt.
         8. Exemplo de output esperado, exemplo: Schema JSON (opcional)
 

Interface web simples, acessível via qualquer dispositivo com navegador moderno.

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
