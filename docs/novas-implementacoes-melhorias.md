


Inclua as seguintes credenciais no banco de dados:
1. Credential name: Mistral A
   1. Service/Provider: Mistral
   2. API KEY: CN9fTAtnszPRB9HNSvOCSdeQltb86RGL
2. Credential name: GROC A
   1. Service/Provider: GROQ
   2. API KEY: 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

Vamos reestruturar a pipeline da tarefa de book review.


PASSOS:
1. Extraír informações bibliográficas da página da amazon
   1. Persistir na collection.
2. Scrap dos links adicionais informados (quando existir),
   1. Executar essa tarefa para cada link existente.
   2. Utilizar API de modelo de IA para analisar o conteúdo e tentar identificar os dados do livro. 
   3. Utilizar a credencial Mistral A.
   4. Criar e incluir no banco de dados prompt específico para essa tarefa.
      1. Uilizar modelo mistral-large-latest
3. Utilizar a API de modelo de IA para gerar um resumo com base no conteúdo do link, especificamente sobre informações relacioandas ao livro e autor. 
   1. Executar essa tarefa para cada link existente. 
   2. Utilizar a credencial GROQ A 
   3. Criar e incluir no banco de dados prompt específico para essa tarefa.
      1. Utilizar modelo llama-3.3-70b-versatile
   4. Persistir essas informações no banco
4. Analisar os dados bibliográficas extraídos da página da amazon e dos demais links, e consolidar as informações sem duplicidades.
   1. 
5. Utilizar a api de iIA para  buscar na internet sobre o livro e o autor, identificando Assuntos abordados no livro, temas, informações etc. 
   1. Utilizar credencial GROQ A  
   2. Criar e ncluir no banco de dados prompt específico para essa tarefa.
      1. Utilizar modelo llama-3.3-70b-versatile

6. ainda não definido.


Implementar:

### INTEFACE DE CONFIGURAÇÃO DE PIPELINES

Incluir no menu "Settings" um novo item chamado "Pipelines"

Disponibilizar interface que liste todas as pipelines disponíveis. Inicialmente incluir um card para a pipline de Book Review.
Ao clicar no card, deve exibir a modal com as informações da pipeline:
- DEtalhes da pipeline, tipo de uso, etc.
- Listar todas as etapas, com as informações: Nome etapa, Descrição, Tipo
- Quando a pipeline utilizar uma api de IA, disponibilizar a informação da credencial, e prompt utilizados
  - Permitir alterar essas informações, disponibilizando credenciais e prompts cadastrados no sistema.