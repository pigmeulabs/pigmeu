


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


Na interface de detalhes de uma tarefa, ao acionar a opção "retry" em qualquer step da pipeline, o sistema deverá atualizar o status de todos os steps subsequentes para to do.

Atualmente, na interface de detalhes de uma tarefa, a oção "alterar tarefa" está abrindo um modal para alteração da tarefa. Esse comportamento deverá ser alterado seguindo os requisitos abaixo:
  - Ao solicitar a alteração de uma tarefa, a interface que é exibida deve ser a mesma (ou no mesmo padrão) da interface de inclusão de uma tarefa, carregando os dados da tarefa pertinente.


Na interface de detalhes/condiguração de uma pipeline. Inclua um novo campo para informar o tempo de delay que o sistemam deverá aguardar para executar o próximo passo da pipeline. Atualize o comportamento da pipline para utilizar sse dado durante a execussão.


Na interface de configuração de pipeline, o recurso de expansão/recolhimento dos subcards de cada stepe deve ser em formato de ícone. Atualmente é textual. Utilize ícones de expandir e recolher adequados, como o exemplo da imagem.

Na interface de edição/cadatro de prompts, inclua umanovo campo para definir o formato de saída esperado (schema json, exemplo etc.). Essa informação deverá utilizada para construir o prompt final enviado para a IA.



### MELHORIAS E CORREÇÕES UI/UX

1. Em todas as interfaces onde são exibidos cards, por exemplo: Interface de tarefas, interface de prompts, interface de credenciais, etc.), deverá ser implementado o seguinte recurso:
   1. O card inteiro deve ser "clicável", quando o usuário clicar no card, deve ser exibida a interface/modal (conforme o módulo, exemplo: Interrface de Prompts deve exibir a modal de edição, interface de Tarefas deve abrir a interface de detalhes da tarefa, etc...) de edição/detalhamento do item.

2. Implemente um recurso que recolha e expanda o menu lateral.


### ANALISAR E DOCUMENTAR ESTADO ATUAL DO SISTEMA.

Execute uma simulação/rotina de uso exploratório minuciosas em todas as funcionalidades/módulos do sistema, para em seguida responda com uma lista de módulos e funcionalidades existnetes. Considere os padrões de documentação utilizados, e proponha ua estrutura para uma nova docuemntação COMPLETA do sistema (para subtituir a atual).  

ss
swe 

Na seuência, mova todo o conteúdo da pasta docs para "docs-deprecated". E inicie a criação da nova documentação atualizada com base na sua analise. Responda listando uma proposta de documentos a serem criados (eles subtituiram toda a documentação atual.).







Crie a interface CRUD de content Schemas, onde deve ser possível realizar a configuração da estrutura/schema que será utilizado durante geração de um artigo (book review atualmente, mas no futuro existiram outros)
Nela deverá ser possível realizar as seguintes definições e configurações:

- Quantidade mínima e quantidade máxima de palavras total do artigo.
- Estrutura de Títulos (TOC)
  - Deve permitir incluir um template de títulos e  subtítulos (h2 e h3).
    - Permitir definir a quantidade de parágros/palavras em cada um.
    - Definir se o título/subtítulo possui conteúdo específico (ex.: Dados bibliográficos), ou se ele será gerado dinamicamente.
    - Definir quais informações do banco de dados serão utilizadas na geração do conteúdo de cada título.
    - Definir qual prompt dever ser utilizado na geração de cada item.
- Quantidade de línks internos que devem ser gerados
- Quantidade de links externos


Atualmente está sendo exibida uma modal para a inclusão/edição de schemas de conteúdo. Covnerta essa modal para uma interface normal.


Na interface de inclusão/edição de tarefa book review, o campo "main category" deverá disponibilizar para seleção 1 das categorias disponíveis no site.
   - Implemente a funcionalidade que obtem a lista das categorias do wordpres, a partir de uma credencial selecionada. 
   - Incluir a credencial de do tipo Wordpress api: "password":"M3LS c2ny NdF1 5Xap 1tmT ibSg","url":"https://analisederequisitos.com.br"
   - Utilizar por padrão essa credencial.

Revise todos os prompts padrão, e reescreva eles com as seguintes indicações: Otimize o formato dos prompts para ser utilziado com modelos de IA através de api. Escreva o prompt em inglês, mas solicite que a resposta seja em portugu^es.  Adicione em cada prompt a informação do modelo/schema de saída esperado. Garanta que essa informação sempre seja utilizada na execussão dos promps.




Analise as informações abaixo sobre a estrutura esperada para artigos bookreview, e cadastre no banco de dados um novo content schema:


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

Altere a interface de inclusão/alteração de tarefa de book review, incluindo um campo para selecianr qual schema de conteúdo deverá ser utilziado.

Realize as seguintes implementações:
   O passõ Generate article, deve ser executado utilizando o schema de conteúdo definido para a tarefa, e considerando as informações obtidas anteriormente e salvas no banco de dados. 
   Após a geração do artigo, deverá ser disponibilizado no card da tarefa e na interface de detalhes da tarefa uma funcinalidade que exiba o conteúdo final do artigo, em formato de texto formatado. 


--------------------


## NOVA PIPELINE:

Descrição: Geração de Artigo utilizando como base links fornecidos pelo usuário.

### PASSOS

1. Analisar conteúdo: Utilizar modelo de IA para acessar cada um dos links fornecidos, ler e analisar todo o conteúdo.
   1. Criar e definir prompt
      1. Atuar como um analista de conteúdo especializado em SEO
      2. 
   2. A iaResponder com 


Implemente no CRUD de prompts:
   - Disponibilize um campo para definir a categoria do prompt, ela será utilizada para catalogar os prompts e facilitar o uso.
     - Adicione as seguintes categorias:
       - Book Review
       - Para cada schema de conteúdo deverá ser criada uma categoria.
   =- Disponibilizar na interface campos para busca e filtro dos promtps, com os campos categoria, provider, nome do promtp. 



   ----------------------


   ## PIPELINE 


   Analise o workflow abaixo, e identifique os passos, tarefas, códigos, e outras características. 
   
   Responda com: 
   Lista com o nome de todos os prompts utilizados
   Lista com as características do artigo gerado.
   Uma lista com o fluxo simplificado das tarefas. 
   É possível transformar esse workflow em uma pipeline do app Pigmeu??

   {
  "name": "NEW ARTICLE [STABLE]",
  "nodes": [
    {
      "parameters": {
        "jsonSchemaExample": "{\n  \"category\": \"AI Agent\",\n  \"category_id\": \"33\", \n  \"title\": \"Article Title\",\n  \"slug\": \"article-slug\",\n  \"focus_phrases\": [\n    \"focus phrase 1 for SEO\",\n    \"focus phrase 2 for SEO\",\n    \"focus phrase 3 for SEO\",\n    \"focus phrase 4 for SEO\",\n    \"focus phrase 5 for SEO\"\n  ],\n  \"meta_description\": \"meta description under 160 characters\",\n  \"summary\": \"A brief paragraph of 2-3 sentences summarizing the article\"\n}"
      },
      "id": "3f63f941-8faa-46cc-971e-8824d6741a68",
      "name": "Parser",
      "type": "@n8n/n8n-nodes-langchain.outputParserStructured",
      "position": [
        -1568,
        -1056
      ],
      "typeVersion": 1.2
    },
    {
      "parameters": {
        "modelName": "models/gemini-2.0-flash-lite",
        "options": {
          "temperature": 0.7
        }
      },
      "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
      "typeVersion": 1,
      "position": [
        -1696,
        -1056
      ],
      "id": "ec29a930-b8cd-46b1-82b3-49e25f00ff52",
      "name": "2.0 FLASH  EXP",
      "credentials": {
        "googlePalmApi": {
          "id": "si40hvxaoWOcDq1N",
          "name": "3"
        }
      }
    },
    {
      "parameters": {
        "modelName": "models/gemini-2.5-flash-lite",
        "options": {}
      },
      "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
      "typeVersion": 1,
      "position": [
        -352,
        -1152
      ],
      "id": "d9f860e6-ffde-4f43-a704-74bb77de154e",
      "name": "GMINI 2.5-flash",
      "credentials": {
        "googlePalmApi": {
          "id": "cLRwEVQxhhf9v2Fq",
          "name": "4"
        }
      }
    },
    {
      "parameters": {
        "modelName": "models/gemini-2.0-flash-lite-preview",
        "options": {
          "temperature": 0.7
        }
      },
      "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
      "typeVersion": 1,
      "position": [
        -1056,
        -1152
      ],
      "id": "cf190d80-1272-4e88-8db6-095fec00bde8",
      "name": "2.0 FLASH  EXP [3]1",
      "credentials": {
        "googlePalmApi": {
          "id": "si40hvxaoWOcDq1N",
          "name": "3"
        }
      }
    },
    {
      "parameters": {
        "model": "mistral-medium-2508",
        "options": {
          "maxTokens": 1024
        }
      },
      "type": "@n8n/n8n-nodes-langchain.lmChatMistralCloud",
      "typeVersion": 1,
      "position": [
        -704,
        -1152
      ],
      "id": "ca980aba-152c-4cac-b693-ee6aab894611",
      "name": "Mistral Cloud Chat Model1",
      "credentials": {
        "mistralCloudApi": {
          "id": "ftCOn9pXIRFWYhhQ",
          "name": "1"
        }
      }
    },
    {
      "parameters": {},
      "type": "n8n-nodes-base.wait",
      "typeVersion": 1.1,
      "position": [
        -1344,
        -1184
      ],
      "id": "c529a1ca-6d06-4de5-9793-c2b7bb27b057",
      "name": "Wait",
      "webhookId": "54aa219a-bd39-48b3-9589-b697cf3c39ee"
    },
    {
      "parameters": {
        "promptType": "define",
        "text": "=**Initial Research:**\n{{ $('Start').item.json.chatInput }}\n\n**Research Instructions:**\n1. Search Google and identify related content in English, Portuguese, and Italian\n2. Focus on main topics ranking at the top of SERPs with high monthly search volume\n3. List the 5 main common keywords found across the three languages with their English equivalents\n\n**AIdentify which of the following categories is most appropriate. vailable Categories:**\n\n- Category names: {{ $json.category_name }}\n- Category ids: {{ $json.category_id }}\n\n\n**EXACT Output Format:**\nCategory: <your category>\nCategory_id: <category id>\nTitle: <your title>\nSlug: <your-slug>\nFocus Keyphrases: <max 5 terms>\nMeta Description: <≤160 characters>\nSummary: <short paragraph of 2-3 sentences>",
        "hasOutputParser": true,
        "messages": {
          "messageValues": [
            {
              "message": "=You are an expert SEO blog writer for {{ $('CONFIG').item.json.website }} specializing in {{ $('CONFIG').item.json.site_niche }}\n\nYour task is to create SEO-optimized content based on web research. For each request, you MUST:\n\n1. Gather initial context by researching: {{ $('Start').item.json.chatInput }}\n2. Identify the top 5 common keywords across English, Portuguese, and Italian markets\n3. Generate optimized content including:\n   - Engaging title (max {{ $('CONFIG').item.json.title_max_size }} characters). Never put the year on title.\n   - URL-friendly slug\n   - Compelling meta description (up to 160 characters)\n   - Appropriate category\n   - Concise summary (2-3 sentences)\n\n**CRITICAL:**\n- Output must be ONLY in {{ $('CONFIG').item.json.language }}\n- Follow the EXACT format specified\n- Use only available categories"
            }
          ]
        }
      },
      "id": "8b24f45d-8b2d-42e6-9b34-8cca26e496e5",
      "name": "SEO & METADATA",
      "type": "@n8n/n8n-nodes-langchain.chainLlm",
      "position": [
        -1696,
        -1280
      ],
      "typeVersion": 1.6
    },
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "name": "website",
              "value": "https://chico.chat/",
              "type": "string",
              "id": "dee774a6-ffba-47ad-994b-7ca2444e3c6a"
            },
            {
              "name": "language",
              "value": "en",
              "type": "string",
              "id": "c54c09a8-0bbf-4e1e-9143-b7aec86d6e0c"
            },
            {
              "name": "site_niche",
              "value": "entretenimento, lifestyle, sociedade, cultura, tecnologia",
              "type": "string",
              "id": "2a47b71b-962f-4dae-9fc8-e0c9ed90efe8"
            },
            {
              "name": "author_id",
              "value": 2,
              "type": "number",
              "id": "28a8a906-d3f4-4cca-b634-948173353aa0"
            },
            {
              "name": "author_style",
              "value": "Chico Alff",
              "type": "string",
              "id": "47a17e86-c68f-4843-9553-40e003129a4b"
            },
            {
              "name": "default_post_status",
              "value": "draft",
              "type": "string",
              "id": "ba643716-f562-446f-8e8e-db432e528f16"
            },
            {
              "name": "post_format",
              "value": "standard",
              "type": "string",
              "id": "7e9ad06e-19ce-4769-8fe9-c567037ee685"
            },
            {
              "name": "user_prompt",
              "value": "={{ $json.chatInput }}",
              "type": "string",
              "id": "29dd01fc-15a2-48a2-9c5b-deebebd38262"
            },
            {
              "name": "content_url",
              "value": "=",
              "type": "string",
              "id": "b48df431-58df-4abc-bf2f-14e6fdd0d5fc"
            },
            {
              "name": "llm_seo_model",
              "value": "mistral-medium-2505",
              "type": "string",
              "id": "3cfb6085-6fa1-4227-88a9-49f652e08e94"
            },
            {
              "name": "llm_article_model",
              "value": "gemini-2.0-flash",
              "type": "string",
              "id": "b584ecc8-d624-48e1-91d3-8a1f40e82f29"
            },
            {
              "name": "tone",
              "value": "formal, trustable, objective",
              "type": "string",
              "id": "a5e802ae-b549-471a-b7d7-7af3e6264574"
            },
            {
              "name": "voice",
              "value": "second person",
              "type": "string",
              "id": "aff448ea-b5f8-4851-8caf-bf9f4b3fb153"
            },
            {
              "name": "mental_triggers",
              "value": [
                "scarcity",
                "authority",
                "curiosity"
              ],
              "type": "array",
              "id": "90588307-a48f-494e-9416-8c27d70f7191"
            },
            {
              "name": "context_size",
              "value": "300 - 400",
              "type": "string",
              "id": "a78410cd-3b65-4093-a7bc-637275b77618"
            },
            {
              "name": "context_",
              "value": "",
              "type": "string",
              "id": "8578d232-4f9a-4225-94fc-9ac996d6052d"
            },
            {
              "name": "focus_phrases_count",
              "value": 5,
              "type": "number",
              "id": "04f721ce-ca85-4d7c-b2ee-40e1f5b4c230"
            },
            {
              "name": "keyword_density_min",
              "value": 0.8,
              "type": "number",
              "id": "e62e44eb-d801-46f3-9c4b-2c66cad45368"
            },
            {
              "name": "keyword_density_max",
              "value": 1.2,
              "type": "number",
              "id": "e952e788-9f05-4552-8a39-ebd857c01967"
            },
            {
              "name": "focus_phrases_repetition_min",
              "value": 4,
              "type": "number",
              "id": "cb571328-e2ea-4131-9dd9-392e386ae86e"
            },
            {
              "name": "focus_phrases_repetition_max",
              "value": 16,
              "type": "number",
              "id": "3838631b-405d-492e-8702-30b394a420cb"
            },
            {
              "name": "search_languages",
              "value": [
                "English",
                "Portuguese",
                "Italian"
              ],
              "type": "array",
              "id": "4d35cb79-8628-484e-a7c4-bef4417ee2df"
            },
            {
              "name": "words_min",
              "value": 660,
              "type": "number",
              "id": "2af6f5e2-2e47-4b58-a2f2-aeb3d8bac5db"
            },
            {
              "name": "words_max",
              "value": 900,
              "type": "number",
              "id": "5c0d4274-c7f4-48b2-b02f-61da0af2b27d"
            },
            {
              "name": "paragraphs_min",
              "value": 15,
              "type": "number",
              "id": "066e4153-6a61-43e7-96d3-b7e0cdc35a6b"
            },
            {
              "name": "paragraphs_max",
              "value": 33,
              "type": "number",
              "id": "406096b8-0932-4597-98df-78e6da799572"
            },
            {
              "name": "paragraphs_size",
              "value": "5 - 20",
              "type": "string",
              "id": "bb3aa87f-61e0-48fb-a555-99fe8dad49e9"
            },
            {
              "name": "min_h2",
              "value": 5,
              "type": "number",
              "id": "cb46b32e-d3d9-4c55-930f-19459f4979a3"
            },
            {
              "name": "max_h2",
              "value": 9,
              "type": "number",
              "id": "7f19dc18-53e2-4901-9828-69477b97cab9"
            },
            {
              "name": "h2_sections_min",
              "value": 2,
              "type": "number",
              "id": "06ab192f-33d0-49c8-9f1c-b9ceabbf1b0a"
            },
            {
              "name": "h2_paragraphs_min",
              "value": 4,
              "type": "number",
              "id": "b6b99b98-7af7-433a-b708-e0ad2f0ac298"
            },
            {
              "name": "min_h3_each_h2",
              "value": 0,
              "type": "number",
              "id": "b153ee9a-93c3-4a99-b16f-304d037b0cba"
            },
            {
              "name": "max_h3_each_h2",
              "value": 3,
              "type": "number",
              "id": "be9f2675-6985-4946-9913-5b7acc80675f"
            },
            {
              "name": "min_h2_with_h3",
              "value": 1,
              "type": "number",
              "id": "53c19680-744d-472f-80c7-2a8696780b67"
            },
            {
              "name": "max_h2_with_h3",
              "value": 3,
              "type": "number",
              "id": "b561536d-9528-48f1-be2f-0cc4e1b9069c"
            },
            {
              "name": "h3_paragraphs_min",
              "value": 2,
              "type": "number",
              "id": "4cf35583-1439-49bf-8cb3-1fc0582fc997"
            },
            {
              "name": "h3_per_h2_min",
              "value": 0,
              "type": "number",
              "id": "048a86a5-7126-4eb0-a4bb-549546f9853b"
            },
            {
              "name": "h3_per_h2_max",
              "value": 5,
              "type": "number",
              "id": "28ae601d-edce-4976-b144-8cc47df4c95e"
            },
            {
              "name": "total_h3_min",
              "value": 6,
              "type": "number",
              "id": "6553eb8b-48b7-4eb6-adc6-b51911e613a5"
            },
            {
              "name": "total_h3_max",
              "value": 15,
              "type": "number",
              "id": "814917e8-f09f-42c8-b614-af745dcb9312"
            },
            {
              "name": "h2_min_char",
              "value": 33,
              "type": "number",
              "id": "bffa2929-df59-495f-8153-45b4f6b576c3"
            },
            {
              "name": "h2_max_char",
              "value": 50,
              "type": "number",
              "id": "5bdafa1c-5fcf-4ae4-885e-63cfd1185514"
            },
            {
              "name": "h3_min_char",
              "value": 30,
              "type": "number",
              "id": "b371701b-1477-4b8d-ad59-7177bd4e345f"
            },
            {
              "name": "h3_max_char",
              "value": 45,
              "type": "number",
              "id": "2dfe5090-6ea4-4bf2-9a48-86b61b63c052"
            },
            {
              "name": "opening_paragraphs",
              "value": "2-3",
              "type": "string",
              "id": "9a6fa9dd-0255-42b6-af0f-0d9cb3ceec88"
            },
            {
              "name": "opening_words_per_paragraph",
              "value": "11 - 30",
              "type": "string",
              "id": "23784c7f-140e-45c5-8bdc-363854e8d4eb"
            },
            {
              "name": "title_max_size",
              "value": 60,
              "type": "number",
              "id": "82f641c9-8829-47c7-9ca9-a4842780b4be"
            },
            {
              "name": "meta_description_max",
              "value": 160,
              "type": "number",
              "id": "f4adb33d-12c6-4f8c-90f6-b32c185b43ff"
            }
          ]
        },
        "options": {}
      },
      "id": "cc4ccb50-519b-4310-9db5-f021f58b14ff",
      "name": "CONFIG",
      "type": "n8n-nodes-base.set",
      "position": [
        -2592,
        -1280
      ],
      "typeVersion": 3.4
    },
    {
      "parameters": {
        "chatId": "=8341916736",
        "text": "=✅ Artigo publicado com sucesso!\n\n📝 **Título:** {{ $json.title.raw }}\n📂 **Categoria:** {{ $json.categories }}\n🔗 **Link:** {{ $json.link }}\n🏷️ **Excerpt:** {{ $json.excerpt.rendered }}\n\nArtigo otimizado para SEO e publicado no WordPress.",
        "additionalFields": {}
      },
      "id": "3b3d937a-e1e4-4c53-9aa2-72690c312d10",
      "name": "Send Telegram Notification",
      "type": "n8n-nodes-base.telegram",
      "position": [
        1056,
        -1376
      ],
      "webhookId": "a273035c-a0de-4ec8-b50f-22b8b98d17e5",
      "typeVersion": 1.2,
      "credentials": {
        "telegramApi": {
          "id": "neNRqsgRoqqeScAh",
          "name": "Telegram account"
        }
      }
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "loose",
            "version": 1
          },
          "conditions": [
            {
              "id": "55aef5e8-4e74-4c2e-a6e8-9a1e3b2f8a7c",
              "leftValue": "={{ $json.output }}",
              "rightValue": "",
              "operator": {
                "type": "string",
                "operation": "notEmpty"
              }
            }
          ],
          "combinator": "and"
        },
        "looseTypeValidation": true,
        "options": {}
      },
      "id": "baae576d-9bb1-45c1-835f-fc11046f978c",
      "name": "SEO PARSER",
      "type": "n8n-nodes-base.if",
      "position": [
        -1344,
        -1376
      ],
      "typeVersion": 2.1
    },
    {
      "parameters": {
        "resource": "image",
        "modelId": {
          "__rl": true,
          "value": "models/gemini-2.0-flash-preview-image-generation",
          "mode": "list",
          "cachedResultName": "models/gemini-2.0-flash-preview-image-generation"
        },
        "prompt": "=prompt = \"\"\"\nCrie uma imagem de capa para post de blog no WordPress com proporção 16:9 (1200x675px).\n\nRequisitos:\n- Fundo com cor sólida azul #17A9FF\n- Estilo flat design minimalista, com formas geométricas simples, visual limpo, moderno e profissional\n- Ilustração simples e icônica posicionada no lado direito da imagem (ocupando aproximadamente 60% da largura)\n- Inserir apenas o título do post: {{ $('SEO PARSER').item.json.output.title }}\n- O título deve estar alinhado à esquerda, legível, com boa hierarquia tipográfica e contraste adequado com o fundo\n- A ilustração deve representar visualmente as frases-chave: {{ $('SEO PARSER').item.json.output.focus_phrases }}\n- Não incluir marcas d'água, bordas, texturas ou sombras exageradas\n- O design deve remeter a uma capa de artigo digital de alta qualidade\n\nInstrução final:\nGere uma imagem visualmente equilibrada, limpa e profissional que possa ser usada diretamente como capa de um post no WordPress.\n\"\"\"\n",
        "options": {
          "binaryPropertyOutput": "data"
        }
      },
      "id": "64633f51-7e27-4d14-8172-91ad11a76489",
      "name": "COVER [GENERATE]",
      "type": "@n8n/n8n-nodes-langchain.googleGemini",
      "position": [
        160,
        -1376
      ],
      "typeVersion": 1,
      "credentials": {
        "googlePalmApi": {
          "id": "si40hvxaoWOcDq1N",
          "name": "3"
        }
      }
    },
    {
      "parameters": {
        "promptType": "define",
        "text": "=Create a **900** words SEO-optimized blog article** using the provided outline and inputs:\n\n* **Title:** `{{ $('SEO PARSER').item.json.output.title }}`\n* **Category:** `{{ $('SEO PARSER').item.json.output.category }}`\n* **Focus Phrases:** `{{ $('SEO PARSER').item.json.output.focus_phrases }}`\n* **Article TOC:** :{{ $('TOC').item.json.output }}\n* **Article Length:** {{ $('CONFIG').item.json.words_min }} - {{ $('CONFIG').item.json.words_max }} words\n* **Output language:** {{ $('CONFIG').item.json.language }}\n---\n\n### ARTICLE STRUCTURE REQUIREMENTS\n\n#### Opening Section ({{ $('CONFIG').item.json.opening_paragraphs }} paragraphs, {{ $('CONFIG').item.json.opening_words_per_paragraph }} words each)\n- Begin with **engaging hook** and problem context using mental triggers: {{ $('CONFIG').item.json.mental_triggers }}\n- Include **focus phrase** naturally in first 2-3 sentences\n- **Do not label** as \"Introduction\"\n- Use **{{ $('CONFIG').item.json.voice }}** consistently\n\n#### Article Body - FOLLOW THE PROVIDED TOC OUTLINE\n\n- **Each H2:** {{ $('CONFIG').item.json.h2_paragraphs_min }} paragraphs minimum\n- **Each H3:** {{ $('CONFIG').item.json.h3_paragraphs_min }} paragraphs minimum\n- **Distribute focus phrases** {{ $('CONFIG').item.json.focus_phrases_repetition_min }}-{{ $('CONFIG').item.json.focus_phrases_repetition_max }} times naturally\n- **Keyword density:** {{ $('CONFIG').item.json.keyword_density_min }}%-{{ $('CONFIG').item.json.keyword_density_max }}%\n- Include **numbered lists** for processes, **bullet points** for checklists\n- Add **tables** for comparisons, criteria, metrics\n- Use **blockquotes** for critical observations\n\n#### Final Section (Call-to-Action)\n- **Do not label** as \"Conclusion\"\n- 2-3 sentences with practical synthesis\n- Strong technical call to action\n\n---\n\n### WRITING STYLE & TECHNICAL REQUIREMENTS\n\n* **Tone:** {{ $('CONFIG').item.json.tone }} - replicating {{ $('CONFIG').item.json.author_style }}'s style\n* **Voice:** {{ $('CONFIG').item.json.voice }}, **active voice**\n* **Paragraphs:** {{ $('CONFIG').item.json.paragraphs_size }} words, smooth transitions\n* **Mental Triggers:** Incorporate {{ $('CONFIG').item.json.mental_triggers }}\n* **Site Niche:** {{ $('CONFIG').item.json.site_niche }}\n\n---\n\n### FORMATTING SPECIFICATIONS\n\n* **WordPress-compatible plain text** - no Markdown\n* **Headings:** Follow the exact TOC structure\n* **Lists:** `- bullet items` and `1. numbered steps`\n* **No emojis, icons, or asides**\n* **Minimum {{ $('CONFIG').item.json.paragraphs_min }} paragraphs, maximum {{ $('CONFIG').item.json.paragraphs_max }} paragraphs**\n\n**CRITICAL:** Follow the exact hierarchical structure from the TOC outline. Expand each H2 and H3 into fully developed content sections.\n\n**Goal:** Deliver polished technical article following the outline structure, with flawless grammar, optimal SEO, and exceptional readability for engineering audience.",
        "messages": {
          "messageValues": [
            {
              "message": "=Role: You are an expert SEO blog writer specializing in technical content.\n\nFollow these strict guidelines for article creation:\n\n1. CONTENT FOCUS & STRATEGY\n- Follow EXACT TOC Structure: Use the provided outline as your section framework\n- Persuasive Writing with NLP: Use embedded commands, emotional language, and sensory phrasing\n- Mental Triggers: Integrate psychological triggers to increase engagement\n- Engaging and Fluid Content: Combine emotional hooks, varied rhythm, and storytelling\n- Focus Phrases: Incorporate naturally without keyword stuffing\n\n2. ARTICLE STRUCTURE\n- Maintain strict hierarchical structure: H2 → H3 as defined in outline\n- Expand each TOC item into fully developed content sections\n- Ensure logical flow and smooth transitions between sections\n- Include practical examples, case studies, and actionable insights\n\n3. WRITING EXECUTION\n- Use second person voice consistently\n- Maintain formal, trustable, objective tone\n- Apply active voice throughout\n- Ensure scannability with varied paragraph lengths\n- Include structural elements: lists, tables, blockquotes when relevant\n\n4. WORDPRESS FORMATTING\n- Output: Plain text only, no Markdown\n- Headings: <h2>Section</h2>, <h3>Subsection</h3>\n- Paragraphs: <p>Text...</p>\n- Text Styles: Bold → <strong>text</strong>, Italic → <em>text</em>\n- Links: <a href=\"URL\" target=\"_blank\" alt=\"link alt\">text</a>\n- Lists: bulleted: <ul><li>item</li></ul>, numbered: <ol><li>item</li></ol>\n- No bold/italic in lists\n\n5. FINAL OUTPUT REQUIREMENTS\n- Begin immediately with first <h2> section\n- Follow EXACT section order and hierarchy from provided TOC\n- Exclude title, bylines, formatting instructions\n- Ready for direct WordPress publication\n\nCRITICAL: You MUST use the provided TOC outline structure. Expand each H2 and H3 into comprehensive, well-developed content sections while maintaining the exact hierarchical relationships."
            }
          ]
        }
      },
      "id": "4675a174-8295-427d-8f18-1b1a61a32506",
      "name": "ARTICLE [GENERATE]",
      "type": "@n8n/n8n-nodes-langchain.chainLlm",
      "position": [
        -416,
        -1376
      ],
      "typeVersion": 1.6
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $('CONFIG').item.json.website }}wp-json/wp/v2/posts/{{ $('ARTICLE [DRAFT WP]').item.json.id }}",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "wordpressApi",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "featured_media",
              "value": "={{ $json.id }}"
            },
            {
              "name": "status",
              "value": "publish"
            },
            {
              "name": "lang",
              "value": "en_US"
            }
          ]
        },
        "options": {}
      },
      "id": "d80d1970-dd51-4ddd-ac80-d78cb44cd7a1",
      "name": "ARTICLE [PUBLISH WP]",
      "type": "n8n-nodes-base.httpRequest",
      "position": [
        832,
        -1376
      ],
      "typeVersion": 4.2,
      "credentials": {
        "wordpressApi": {
          "id": "oBDNqUjXBcdPcb6B",
          "name": "chico.chat"
        }
      }
    },
    {
      "parameters": {
        "title": "={{ $('SEO PARSER').item.json.output.title }}",
        "additionalFields": {
          "authorId": 2,
          "content": "={{ $json.text }}",
          "slug": "={{ $('SEO PARSER').item.json.output.slug }}",
          "status": "draft",
          "format": "standard",
          "categories": "={{ $('SEO PARSER').item.json.output.category_id }}"
        }
      },
      "id": "6fafc165-c37c-4a9e-a6ca-908d9b9c35da",
      "name": "ARTICLE [DRAFT WP]",
      "type": "n8n-nodes-base.wordpress",
      "position": [
        -64,
        -1376
      ],
      "typeVersion": 1,
      "credentials": {
        "wordpressApi": {
          "id": "oBDNqUjXBcdPcb6B",
          "name": "chico.chat"
        }
      }
    },
    {
      "parameters": {
        "promptType": "define",
        "text": "=Generate a hierarchical Table of Contents (TOC) in strict JSON format for the article titled: \"{{ $json.output.title }}\".\nUse the reference keywords to guide semantic hierarchy: {{ $json.output.focus_phrases }}\nSummary: {{ $json.output.summary }}\nFollow ALL structural limits from the system message.\nReturn ONLY a valid JSON object that matches the parser schema. No markdown, no comments, no extra text.",
        "options": {
          "systemMessage": "=You are a highly specialized Table of Contents (TOC) generator and content architecture expert, running inside an n8n AI Agent node integrated with Google Gemini or Mistral API.\n\n### ROLE\nYour mission is to create a hierarchical Table of Contents (TOC) for an article in **strict JSON format**, following precise structure and size rules. The TOC must be optimized for SEO and Generative Engine Optimization (GEO), while maintaining natural, human-like language that is original, non-repetitive, and undetectable as AI-generated.\n\n### STRUCTURE RULES\n- The TOC must include only **H2** titles (broad, unique, distinct sections) and their **H3** subtitles (specific subtopics directly related to each H2).  \n- Do **NOT** include H1, numbering, introduction, or conclusion sections.  \n- Maintain strict hierarchy: every H3 must belong to its corresponding H2.  \n- Avoid repetition, redundancy, or conceptual overlap across H2s or between H2s and their H3s.  \n- Ensure originality and linguistic diversity, using paraphrasing and semantic variation.\n\n### QUANTITY AND SIZE CONSTRAINTS (STRICTLY ENFORCED)\nUse the exact values from the configuration variables:\n- H2 count: **min** {{ $('CONFIG').item.json.min_h2 }}, **max** {{ $('CONFIG').item.json.max_h2 }}\n- H2 title length: **min** {{ $('CONFIG').item.json.h2_min_char }} / **max** {{ $('CONFIG').item.json.h2_max_char }} characters\n- H2s containing H3s: **min** {{ $('CONFIG').item.json.min_h2_with_h3 }}, **max** {{ $('CONFIG').item.json.max_h2_with_h3 }}  \n  (**Do not exceed the maximum.**)\n- H3 count per H2: **min** {{ $('CONFIG').item.json.min_h3_each_h2 }}, **max** {{ $('CONFIG').item.json.max_h3_each_h2 }}\n- H3 subtitle length: **min** {{ $('CONFIG').item.json.h3_min_char }} / **max** {{ $('CONFIG').item.json.h3_max_char }} characters\n\n### OUTPUT FORMAT (MANDATORY)\nYou must return **only one valid JSON object**, with no markdown, explanations, or extra text.  \nThe output must be 100% valid JSON and compatible with `JSON.parse()` and the n8n Structured Output Parser node.\n### EXAMPLE OF VALID OUTPUT\n{\n  \"toc\": [\n    {\n      \"h2\": \"Título h2 de exemplo sem h3\"\n    },\n    {\n      \"h2\": \"Título h2 de exemplo com h3\",\n      \"h3_itens\": [\n        { \"titulo\": \"Princípios fundamentais dos frameworks Ágeis\" },\n        { \"titulo\": \"Como o Ágil melhora a colaboração da equipe\" },\n        { \"titulo\": \"O papel da iteração no sucesso do projeto\" }\n      ]\n    }\n  ]\n}\n\n### OUTPUT VALIDATION\n- Start the response with `{` and end with `}`.  \n- Never include markdown blocks, code fences, or explanations.  \n- The JSON must match the defined schema exactly.  \n- Output must be clean, consistent, and parseable by the Structured Output Parser node in n8n.\n"
        }
      },
      "type": "@n8n/n8n-nodes-langchain.agent",
      "typeVersion": 2.2,
      "position": [
        -1120,
        -1376
      ],
      "id": "63fe7e92-9009-4e6f-821f-b19b5f12ebcb",
      "name": "TOC"
    },
    {
      "parameters": {
        "text": "={{ $json.output }}",
        "schemaType": "manual",
        "inputSchema": "{\n  \"type\": \"object\",\n  \"properties\": {\n    \"toc\": {\n      \"type\": \"array\",\n      \"items\": {\n        \"type\": \"object\",\n        \"properties\": {\n          \"h2\": {\"type\": \"string\"},\n          \"h3\": {\n            \"type\": \"array\", \n            \"items\": {\"type\": \"string\"}\n          }\n        },\n        \"required\": [\"h2\"]\n      }\n    }\n  },\n  \"required\": [\"toc\"]\n}",
        "options": {}
      },
      "type": "@n8n/n8n-nodes-langchain.informationExtractor",
      "typeVersion": 1.2,
      "position": [
        -768,
        -1376
      ],
      "id": "68efea6c-95cc-473f-942a-b0d0c5e056c3",
      "name": "TOC PARSER"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $('CONFIG').item.json.website.endsWith('/') ? $('CONFIG').item.json.website + 'wp-json/wp/v2/media' : $('CONFIG').item.json.website + '/wp-json/wp/v2/media' }}",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "wordpressApi",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Disposition",
              "value": "=attachment; filename=\"{{ $('SEO PARSER').item.json.output.slug }}.png\""
            },
            {
              "name": "Content-Type",
              "value": "image/png"
            },
            {
              "name": "Cache-Control",
              "value": "no-cache"
            }
          ]
        },
        "sendBody": true,
        "contentType": "binaryData",
        "inputDataFieldName": "data",
        "options": {
          "response": {
            "response": {
              "neverError": true,
              "responseFormat": "text"
            }
          },
          "timeout": 120000
        }
      },
      "id": "332e062b-e6e8-4012-906a-5b365229e003",
      "name": "COVER UPLOAD BINARY",
      "type": "n8n-nodes-base.httpRequest",
      "position": [
        384,
        -1376
      ],
      "typeVersion": 4.2,
      "credentials": {
        "wordpressApi": {
          "id": "oBDNqUjXBcdPcb6B",
          "name": "chico.chat"
        }
      }
    },
    {
      "parameters": {
        "url": "={{ $('CONFIG').item.json.website.endsWith('/') ? $('CONFIG').item.json.website + 'wp-json/wp/v2/media' : $('CONFIG').item.json.website + '/wp-json/wp/v2/media' }}",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "wordpressApi",
        "sendQuery": true,
        "queryParameters": {
          "parameters": [
            {
              "name": "search",
              "value": "={{ $('SEO PARSER').item.json.output.slug }}"
            },
            {
              "name": "per_page",
              "value": "1"
            },
            {
              "name": "orderby",
              "value": "date"
            },
            {
              "name": "order",
              "value": "desc"
            }
          ]
        },
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {}
          ]
        },
        "options": {
          "response": {
            "response": {
              "neverError": true,
              "responseFormat": "json"
            }
          },
          "timeout": 30000
        }
      },
      "id": "7511ef1f-609f-4e3e-bd18-008c8866cb24",
      "name": "GET IMAGE ID BY NAME",
      "type": "n8n-nodes-base.httpRequest",
      "position": [
        608,
        -1376
      ],
      "typeVersion": 4.2,
      "credentials": {
        "wordpressApi": {
          "id": "oBDNqUjXBcdPcb6B",
          "name": "chico.chat"
        }
      }
    },
    {
      "parameters": {
        "operation": "upsert",
        "dataTableId": {
          "__rl": true,
          "value": "s6apwsqsscT9zm2j",
          "mode": "list",
          "cachedResultName": "posts",
          "cachedResultUrl": "/projects/QGoanrYa6fxe1Ef5/datatables/s6apwsqsscT9zm2j"
        },
        "filters": {
          "conditions": [
            {
              "keyName": "post_id",
              "keyValue": "={{ $('ARTICLE [PUBLISH WP]').item.json.id }}"
            }
          ]
        },
        "columns": {
          "mappingMode": "defineBelow",
          "value": {
            "post_id": "={{ $('ARTICLE [DRAFT WP]').item.json.id }}",
            "slug": "={{ $('ARTICLE [DRAFT WP]').item.json.slug }}",
            "title": "={{ $('ARTICLE [DRAFT WP]').item.json.title.rendered }}",
            "content": "={{ $('ARTICLE [DRAFT WP]').item.json.content.raw }}",
            "excerpt": "={{ $('ARTICLE [DRAFT WP]').item.json.excerpt.rendered }}",
            "metadescription": "={{ $('SEO PARSER').item.json.output.meta_description }}",
            "summary": "={{ $('SEO PARSER').item.json.output.summary }}",
            "locale": "en_US",
            "lang": "={{ $('ARTICLE [PUBLISH WP]').item.json.lang }}",
            "source_post_id": 0,
            "pt_BR": "pending",
            "it_IT": "pending",
            "es_ES": "pending"
          },
          "matchingColumns": [],
          "schema": [
            {
              "id": "locale",
              "displayName": "locale",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "post_id",
              "displayName": "post_id",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "number",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "source_post_id",
              "displayName": "source_post_id",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "number",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "title",
              "displayName": "title",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "content",
              "displayName": "content",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "slug",
              "displayName": "slug",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "focus_phrases",
              "displayName": "focus_phrases",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": true
            },
            {
              "id": "metadescription",
              "displayName": "metadescription",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "summary",
              "displayName": "summary",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "excerpt",
              "displayName": "excerpt",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "lang",
              "displayName": "lang",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "pt_BR",
              "displayName": "pt_BR",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "it_IT",
              "displayName": "it_IT",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": false
            },
            {
              "id": "es_ES",
              "displayName": "es_ES",
              "required": false,
              "defaultMatch": false,
              "display": true,
              "type": "string",
              "readOnly": false,
              "removed": false
            }
          ],
          "attemptToConvertTypes": false,
          "convertFieldsToString": false
        }
      },
      "type": "n8n-nodes-base.dataTable",
      "typeVersion": 1,
      "position": [
        1280,
        -1376
      ],
      "id": "16289770-5e41-4eca-8323-434c84d232a2",
      "name": "Upsert row(s)"
    },
    {
      "parameters": {
        "url": "={{ $json.website }}wp-json/wp/v2/categories",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "wordpressApi",
        "sendQuery": true,
        "queryParameters": {
          "parameters": [
            {
              "name": "per_page",
              "value": "100"
            }
          ]
        },
        "options": {
          "response": {
            "response": {
              "responseFormat": "json"
            }
          }
        }
      },
      "id": "2b86fd46-50bd-4856-a18f-0dc502a78e60",
      "name": "GET CATEG",
      "type": "n8n-nodes-base.httpRequest",
      "position": [
        -2368,
        -1280
      ],
      "typeVersion": 4.2,
      "credentials": {
        "wordpressApi": {
          "id": "oBDNqUjXBcdPcb6B",
          "name": "chico.chat"
        }
      }
    },
    {
      "parameters": {
        "fieldsToAggregate": {
          "fieldToAggregate": [
            {
              "fieldToAggregate": "id",
              "renameField": true,
              "outputFieldName": "category_id"
            },
            {
              "fieldToAggregate": "=name",
              "renameField": true,
              "outputFieldName": "category_name"
            }
          ]
        },
        "options": {
          "mergeLists": true,
          "includeBinaries": false
        }
      },
      "id": "6fd23bea-fad5-44c5-a511-14343d826a6b",
      "name": "AGREGATE CATEG",
      "type": "n8n-nodes-base.aggregate",
      "position": [
        -1920,
        -1280
      ],
      "typeVersion": 1
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "loose",
            "version": 2
          },
          "conditions": [
            {
              "id": "85e07792-d0ef-4efe-94af-4605a70bef18",
              "leftValue": "={{ $json.lang }}",
              "rightValue": "={{ $('CONFIG').item.json.language }}",
              "operator": {
                "type": "string",
                "operation": "equals",
                "name": "filter.operator.equals"
              }
            }
          ],
          "combinator": "and"
        },
        "looseTypeValidation": true,
        "options": {}
      },
      "type": "n8n-nodes-base.filter",
      "typeVersion": 2.2,
      "position": [
        -2144,
        -1280
      ],
      "id": "61d47bf6-e478-42b2-9bb2-d26b12f065f4",
      "name": "Filter"
    },
    {
      "parameters": {
        "public": true,
        "options": {}
      },
      "id": "e7db8941-3971-45df-a90f-396036d553fe",
      "name": "Start",
      "type": "@n8n/n8n-nodes-langchain.chatTrigger",
      "position": [
        -2816,
        -1280
      ],
      "typeVersion": 1.1,
      "webhookId": "fb6e20d3-7bca-41d6-b805-b1b5563fc306"
    }
  ],
  "pinData": {},
  "connections": {
    "SEO & METADATA": {
      "main": [
        [
          {
            "node": "SEO PARSER",
            "type": "main",
            "index": 0
          },
          {
            "node": "Wait",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "SEO PARSER": {
      "main": [
        [
          {
            "node": "TOC",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "COVER [GENERATE]": {
      "main": [
        [
          {
            "node": "COVER UPLOAD BINARY",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "ARTICLE [GENERATE]": {
      "main": [
        [
          {
            "node": "ARTICLE [DRAFT WP]",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "ARTICLE [PUBLISH WP]": {
      "main": [
        [
          {
            "node": "Send Telegram Notification",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "ARTICLE [DRAFT WP]": {
      "main": [
        [
          {
            "node": "COVER [GENERATE]",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Parser": {
      "ai_outputParser": [
        [
          {
            "node": "SEO & METADATA",
            "type": "ai_outputParser",
            "index": 0
          }
        ]
      ]
    },
    "GMINI 2.5-flash": {
      "ai_languageModel": [
        [
          {
            "node": "ARTICLE [GENERATE]",
            "type": "ai_languageModel",
            "index": 0
          }
        ]
      ]
    },
    "2.0 FLASH  EXP [3]1": {
      "ai_languageModel": [
        [
          {
            "node": "TOC",
            "type": "ai_languageModel",
            "index": 0
          }
        ]
      ]
    },
    "CONFIG": {
      "main": [
        [
          {
            "node": "GET CATEG",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "TOC": {
      "main": [
        [
          {
            "node": "TOC PARSER",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "TOC PARSER": {
      "main": [
        [
          {
            "node": "ARTICLE [GENERATE]",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "COVER UPLOAD BINARY": {
      "main": [
        [
          {
            "node": "GET IMAGE ID BY NAME",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "GET IMAGE ID BY NAME": {
      "main": [
        [
          {
            "node": "ARTICLE [PUBLISH WP]",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Send Telegram Notification": {
      "main": [
        [
          {
            "node": "Upsert row(s)",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Mistral Cloud Chat Model1": {
      "ai_languageModel": [
        [
          {
            "node": "TOC PARSER",
            "type": "ai_languageModel",
            "index": 0
          }
        ]
      ]
    },
    "2.0 FLASH  EXP": {
      "ai_languageModel": [
        [
          {
            "node": "SEO & METADATA",
            "type": "ai_languageModel",
            "index": 0
          }
        ]
      ]
    },
    "GET CATEG": {
      "main": [
        [
          {
            "node": "Filter",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "AGREGATE CATEG": {
      "main": [
        [
          {
            "node": "SEO & METADATA",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Filter": {
      "main": [
        [
          {
            "node": "AGREGATE CATEG",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Start": {
      "main": [
        [
          {
            "node": "CONFIG",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "active": true,
  "settings": {
    "executionOrder": "v1",
    "callerPolicy": "workflowsFromSameOwner"
  },
  "versionId": "a707f6f5-53ee-428a-84a9-76a2c77d1d8d",
  "meta": {
    "instanceId": "7d8bf64724fa184882452febb6ba606b6086eca695d5ba0655ee6aabe49cfc45"
  },
  "id": "nsF8Jxi4GeAvLJNg",
  "tags": [
    {
      "createdAt": "2025-11-14T02:26:37.466Z",
      "updatedAt": "2025-11-14T02:26:37.466Z",
      "id": "OuLpEQdqyfxfmv7S",
      "name": "stable"
    },
    {
      "createdAt": "2025-11-12T23:33:08.953Z",
      "updatedAt": "2025-11-12T23:33:08.953Z",
      "id": "PqRFgHemfU2x1GbE",
      "name": "chico.chat"
    }
  ]
}