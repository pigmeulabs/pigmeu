#!/usr/bin/env python3
"""
Seed script to initialize default prompts in MongoDB.

Run with: python scripts/seed_prompts.py
"""

import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.db.connection import get_database


INITIAL_PROMPTS = [
    {
        "name": "Book Metadata Extractor",
        "purpose": "Extract structured metadata from Amazon product pages",
        "category": "Book Review",
        "provider": "openai",
        "short_description": "Extracts normalized metadata from book pages.",
        "system_prompt": """You are a high-precision bibliographic extraction assistant optimized for API inference.
Use only the evidence present in the input.
Do not hallucinate missing values.
Respond in Portuguese (pt-BR).
Return only valid JSON following the expected output schema.""",
        "user_prompt": """Task: extract normalized metadata for a book.

Input source:
{{data}}

Rules:
1. Use only factual information from input.
2. Keep numbers as numbers where possible.
3. Use null for unknown fields.
4. Preserve identifiers exactly (ISBN, ASIN, URLs).
5. Respond in Portuguese (pt-BR), except identifiers/URLs.
6. Return only the JSON object.""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 500,
        "expected_output_format": """{
  "title_original": "string|null",
  "authors": ["string"],
  "theme": "string|null",
  "lang_original": "string|null",
  "lang_edition": "string|null",
  "edition": "string|null",
  "pub_date": "string|null",
  "publisher": "string|null",
  "isbn": "string|null",
  "pages": "number|null",
  "price_physical": "number|string|null",
  "price_ebook": "number|string|null",
  "amazon_rating": "number|null"
}""",
        "schema_example": """{
  "title_original": "Scrum and Kanban",
  "authors": ["Chico Alff"],
  "theme": "Gestão ágil",
  "lang_original": "Inglês",
  "lang_edition": "Português",
  "edition": "2ª edição",
  "pub_date": "2025-03-05",
  "publisher": "Editora Exemplo",
  "isbn": "9781234567897",
  "pages": 312,
  "price_physical": 89.9,
  "price_ebook": 39.9,
  "amazon_rating": 4.6
}""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "Context Generator - Technical Books",
        "purpose": "context",
        "category": "Book Review",
        "provider": "openai",
        "short_description": "Gera contexto editorial estruturado para artigo de book review.",
        "system_prompt": """You are a senior editorial researcher for technical book reviews.
Your job is to transform noisy evidence into a reliable context package for article generation.
Separate facts from interpretation, avoid unsupported claims, and preserve source traceability.
All output must be in Portuguese (pt-BR).""",
        "user_prompt": """Task: build the editorial context package for "{{title}}" by {{author}}.

Input data:
{{data}}

Requirements:
1. Use concise, didactic and objective language.
2. Explicitly distinguish confirmed facts from inferences.
3. Highlight practical applications, target audience and editorial angle.
4. Capture strengths, limitations and controversies when present.
5. Include SEO-relevant terms and FAQ candidates.
6. Mention missing evidence clearly.
7. Respond in Portuguese (pt-BR).
8. Follow the expected output format exactly.""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.5,
        "max_tokens": 1800,
        "expected_output_format": """Markdown template:
# Base de Conhecimento: <titulo>

## Visão Editorial
- Tese central do livro (2-3 frases)
- Relevância para profissionais de software/produto

## Conceitos-Chave
- conceito 1
- conceito 2
- conceito 3

## Problemas que o Livro Resolve
- problema 1
- problema 2

## Público-Alvo
- para quem o livro é recomendado
- em qual estágio de carreira faz mais sentido

## Aplicações Práticas
- aplicação 1
- aplicação 2
- aplicação 3

## Pontos Fortes e Limitações
- forças principais
- limitações/riscos de interpretação

## Dados Bibliográficos Confirmados
- autor
- editora
- edição
- ISBN/ASIN
- páginas
- links oficiais

## SEO e Intenção de Busca
- keyword principal
- keywords secundárias
- termos relacionados

## FAQ Candidata
- pergunta 1
- pergunta 2
- pergunta 3""",
        "schema_example": """# Base de Conhecimento: Scrum e Kanban

## Visão Editorial
- Tese central: o livro conecta Scrum e Kanban para times que precisam ganhar previsibilidade sem perder adaptabilidade.
- Relevância: útil para equipes de produto/engenharia que enfrentam gargalos, retrabalho e baixa cadência.

## Conceitos-Chave
- Limites de WIP
- Ciclo de feedback curto
- Fluxo puxado

## Problemas que o Livro Resolve
- Acúmulo de trabalho em progresso e baixa previsibilidade
- Dificuldade de equilibrar planejamento com adaptação contínua

## Público-Alvo
- Líderes técnicos, POs e agilistas
- Times em fase de escala ou reorganização de fluxo

## Aplicações Práticas
- Definição de políticas explícitas de fluxo
- Uso de métricas de lead time para tomada de decisão
- Ajustes de cadência de planejamento e revisão

## Pontos Fortes e Limitações
- Forte em aplicabilidade operacional
- Limitação: depende de maturidade da equipe para manter disciplina de métricas

## Dados Bibliográficos Confirmados
- Autor: Chico Alff
- Editora: Exemplo
- ISBN: 9781234567897
- Páginas: 312
- Amazon: https://amazon.com/exemplo

## SEO e Intenção de Busca
- keyword principal: scrum e kanban livro
- keywords secundárias: gestão ágil, fluxo de trabalho, melhoria contínua
- termos relacionados: lead time, throughput, WIP

## FAQ Candidata
- Este livro é indicado para iniciantes em métodos ágeis?
- O livro compara Scrum e Kanban com exemplos práticos?
- Quais métricas o autor recomenda para melhorar previsibilidade?""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "Topic Extractor for Books",
        "purpose": "topic_extraction",
        "category": "Book Review",
        "provider": "openai",
        "short_description": "Extrai 3 eixos editoriais para estruturar H2/H3 do artigo.",
        "system_prompt": """You are a book analysis assistant specialized in editorial topic planning.
Identify exactly 3 complementary themes that can structure a high-quality review article.
Use only provided evidence and avoid generic labels.
Respond in Portuguese (pt-BR).
Return strict JSON only.""",
        "user_prompt": """Task: analyze "{{title}}" by {{author}} and extract exactly 3 core editorial themes.

Book evidence:
{{data}}

Rules:
1. Theme names must be concise (2 to 5 words) and useful as H2 titles.
2. Descriptions must be objective (1 to 2 sentences) with practical focus.
3. Provide 3 to 5 subtopics per theme suitable for H3.
4. Avoid overlap between themes and subtopics.
5. Prioritize topics that answer real reader intent.
6. Respond in Portuguese (pt-BR).
7. Return only the JSON object.""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.5,
        "max_tokens": 750,
        "expected_output_format": """{
  "topics": [
    {
      "name": "string",
      "description": "string",
      "reader_benefit": "string",
      "subtopics": ["string", "string", "string"]
    },
    {
      "name": "string",
      "description": "string",
      "reader_benefit": "string",
      "subtopics": ["string", "string", "string"]
    },
    {
      "name": "string",
      "description": "string",
      "reader_benefit": "string",
      "subtopics": ["string", "string", "string"]
    }
  ]
}""",
        "schema_example": """{
  "topics": [
    {
      "name": "Gestão de Fluxo",
      "description": "Explica como visualizar trabalho, limitar WIP e melhorar previsibilidade.",
      "reader_benefit": "Ajuda a reduzir gargalos e aumentar estabilidade de entrega.",
      "subtopics": ["Quadro visual", "Limites de WIP", "Lead time"]
    },
    {
      "name": "Entrega Incremental",
      "description": "Mostra como reduzir risco por ciclos curtos de entrega e validação.",
      "reader_benefit": "Permite validar valor mais cedo e corrigir rota rapidamente.",
      "subtopics": ["Lotes menores", "Feedback contínuo", "Priorização"]
    },
    {
      "name": "Melhoria Contínua",
      "description": "Aborda métricas e rotinas para evoluir o processo de forma sustentável.",
      "reader_benefit": "Cria disciplina de evolução baseada em dados reais do time.",
      "subtopics": ["Métricas operacionais", "Retrospectivas", "Ajustes de processo"]
    }
  ]
}""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "SEO-Optimized Article Writer",
        "purpose": "article",
        "category": "Book Review",
        "provider": "openai",
        "short_description": "Gera artigo final de book review em estilo editorial técnico, em pt-BR.",
        "system_prompt": """You are a senior Brazilian technical columnist writing book reviews for a professional audience.
Your style must be analytical, practical, and trustworthy.
Prioritize factual consistency, clarity, and reader value.
Never fabricate bibliographic data or claims.
All output must be in Portuguese (pt-BR).""",
        "user_prompt": """Task: write a complete SEO-oriented review article for "{{title}}" by {{author}}.

Themes:
- Theme 1: {{topic1}}
- Theme 2: {{topic2}}
- Theme 3: {{topic3}}

Context:
{{context}}

Requirements:
1. Write in natural Brazilian Portuguese (pt-BR), with clear and didactic tone.
2. Use markdown headings (H2/H3) with strong readability.
3. Keep the article factual; when evidence is weak, state uncertainty.
4. Include practical implications and examples for software/product professionals.
5. Use concise paragraphs and bullet lists where they improve scanning.
6. Ensure SEO intent: semantic relevance, related terms, and useful headings.
7. Respect schema constraints when provided (order, word targets, links).
8. Follow the expected output format exactly.""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.55,
        "max_tokens": 3200,
        "expected_output_format": """Markdown template:
# <Título SEO do artigo>

<Parágrafo de abertura com contexto e promessa de valor ao leitor>

## Introdução ao Tema do Livro
## Resumo da Obra
## Contexto e Motivação
## Impacto e Aplicabilidade
## {{topic1}}
### Subtópico 1
### Subtópico 2

## {{topic2}}
### Subtópico 1
### Subtópico 2

## {{topic3}}
### Subtópico 1
### Subtópico 2

## Pontos Fortes e Limitações
## Detalhes do Livro
## Sobre o Autor
## Conclusão e Recomendação
## Perguntas Frequentes
## Onde Comprar e Formatos
## Assuntos Relacionados
## Artigos Recomendados

Regras adicionais:
- Usar links internos e externos em markdown quando relevante.
- Não incluir notas de bastidor, disclaimers de IA ou texto fora do artigo.""",
        "schema_example": """# Arquitetura Limpa: princípios para software sustentável

Arquitetura limpa não é apenas organização de código: é uma forma de reduzir acoplamento e preservar capacidade de mudança. Neste review, você entende a proposta central do livro, os conceitos que mais impactam o dia a dia e quando a abordagem entrega mais valor para times de produto e engenharia.

## Introdução ao Tema do Livro
## Resumo da Obra
## Contexto e Motivação
## Impacto e Aplicabilidade

## Dependência e Fronteiras de Camadas
### Regra da dependência
### Isolamento do domínio

## Decisões Arquiteturais Evolutivas
### Trade-offs de design
### Como evitar overengineering

## Testabilidade como critério arquitetural
### Estratégias de teste
### Benefícios para manutenção

## Pontos Fortes e Limitações
## Detalhes do Livro
## Sobre o Autor
## Conclusão e Recomendação
## Perguntas Frequentes
## Onde Comprar e Formatos
## Assuntos Relacionados
## Artigos Recomendados""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "Link Summarizer",
        "purpose": "Summarize external web page content into structured markdown for knowledge base",
        "category": "Book Review",
        "provider": "openai",
        "short_description": "Summarizes external pages using deterministic markdown sections.",
        "system_prompt": """You are a web-content summarization assistant optimized for API workflows.
Extract key facts, insights, and relevance for editorial usage.
Do not invent information not present in the source.
Respond in Portuguese (pt-BR).""",
        "user_prompt": """Task: summarize this web content about "{{title}}".

Source content:
{{content}}

Requirements:
1. Keep summary concise and factual.
2. Prioritize relevance for book/author analysis.
3. Explicitly indicate credibility level.
4. Respond in Portuguese (pt-BR).
5. Follow the expected output format exactly.""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.5,
        "max_tokens": 400,
        "expected_output_format": """Markdown template:
## Ideia Principal
<2-3 frases>

## Pontos-Chave
- ponto 1
- ponto 2
- ponto 3

## Tópicos Relevantes
- tópico 1
- tópico 2

## Credibilidade da Fonte
<alta|media|baixa + justificativa curta>""",
        "schema_example": """## Ideia Principal
O conteúdo apresenta uma visão prática sobre aplicação de métodos ágeis em times de produto.

## Pontos-Chave
- Destaca limites de WIP para reduzir gargalos
- Mostra exemplos de melhoria contínua com métricas
- Relaciona processo com previsibilidade de entregas

## Tópicos Relevantes
- gestão ágil
- kanban
- métricas de fluxo

## Credibilidade da Fonte
media — apresenta exemplos úteis, mas sem referências metodológicas detalhadas.""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "Book Review - Additional Link Bibliographic Extractor",
        "purpose": "book_review_link_bibliography_extract",
        "category": "Book Review",
        "provider": "mistral",
        "short_description": "Extrai metadados bibliográficos de conteúdo de links adicionais.",
        "system_prompt": """You are a bibliographic extraction engine optimized for API usage.
Extract only factual information about a book and its author from the provided text.
Do not invent data.
Respond in Portuguese (pt-BR).
Return strict JSON only.""",
        "user_prompt": """Task: extract bibliographic metadata from source content.

Book title (reference): {{title}}
Author (reference): {{author}}

Source content:
{{content}}

Rules:
1. Use only information present in the source.
2. Keep numeric values as numbers where possible.
3. If a field is unknown, use null.
4. Respond in Portuguese (pt-BR), except URLs and identifiers.
5. Return only the JSON object.
6. Follow the expected output format exactly.""",
        "model_id": "mistral-large-latest",
        "temperature": 0.1,
        "max_tokens": 900,
        "expected_output_format": """{
  "title": "string|null",
  "title_original": "string|null",
  "authors": ["string"],
  "language": "string|null",
  "original_language": "string|null",
  "edition": "string|null",
  "average_rating": "number|null",
  "pages": "number|null",
  "publisher": "string|null",
  "publication_date": "string|null",
  "asin": "string|null",
  "isbn_10": "string|null",
  "isbn_13": "string|null",
  "price_book": "number|string|null",
  "price_ebook": "number|string|null",
  "cover_image_url": "string|null"
}""",
        "schema_example": """{
  "title": "Scrum e Kanban",
  "title_original": "Scrum and Kanban",
  "authors": ["Chico Alff"],
  "language": "Português",
  "original_language": "Inglês",
  "edition": "2ª edição",
  "average_rating": 4.6,
  "pages": 312,
  "publisher": "Editora Exemplo",
  "publication_date": "2024-06-18",
  "asin": "B0ABC12345",
  "isbn_10": "1234567890",
  "isbn_13": "9781234567897",
  "price_book": 89.9,
  "price_ebook": 39.9,
  "cover_image_url": "https://exemplo.com/capa.jpg"
}""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "Book Review - Additional Link Summary",
        "purpose": "book_review_link_summary",
        "category": "Book Review",
        "provider": "groq",
        "short_description": "Resume links adicionais com foco em livro, autor e valor editorial.",
        "system_prompt": """You summarize web content for editorial book research.
Focus strictly on insights about the book and author.
Preserve factual accuracy and avoid invented claims.
Respond in Portuguese (pt-BR).
Return strict JSON only.""",
        "user_prompt": """Task: produce a concise summary from this source.

Book title: {{title}}
Author: {{author}}
Source URL: {{url}}

Source content:
{{content}}

Rules:
1. Focus only on relevant information about the book and author.
2. Keep summary objective, factual and useful for writing an analytical review article.
3. Highlight practical insights, target audience clues and concrete examples when present.
4. Respond in Portuguese (pt-BR).
5. Return only the JSON object.
6. Follow the expected output format exactly.""",
        "model_id": "llama-3.3-70b-versatile",
        "temperature": 0.3,
        "max_tokens": 900,
        "expected_output_format": """{
  "summary": "string",
  "topics": ["string"],
  "key_points": ["string"],
  "reader_intent_clues": ["string"],
  "credibility": "alta|media|baixa"
}""",
        "schema_example": """{
  "summary": "O conteúdo destaca os principais conceitos do livro e relaciona os argumentos com a trajetória do autor.",
  "topics": ["gestão ágil", "kanban", "melhoria contínua"],
  "key_points": ["Explica fundamentos práticos", "Compara abordagens", "Apresenta exemplos reais"],
  "reader_intent_clues": ["busca por implementação prática", "comparação entre abordagens ágeis"],
  "credibility": "media"
}""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "Book Review - Web Research",
        "purpose": "book_review_web_research",
        "category": "Book Review",
        "provider": "groq",
        "short_description": "Pesquisa web sobre temas, contexto e intenção editorial do livro/autor.",
        "system_prompt": """You are a literary research analyst.
Synthesize topics, themes, and context about the book and author from web source excerpts.
Do not invent unsupported claims.
Organize output for downstream article writing.
Respond in Portuguese (pt-BR).
Return strict JSON only.""",
        "user_prompt": """Task: consolidate web research notes.

Book title: {{title}}
Author: {{author}}

Sources:
{{sources}}

Rules:
1. Prioritize themes, contexts, and discussion points useful for editorial analysis.
2. Keep statements grounded in provided sources.
3. Highlight practical applicability and reader value signals.
4. Include FAQ candidates and related SEO terms when possible.
5. Respond in Portuguese (pt-BR).
6. Return only the JSON object.
7. Follow the expected output format exactly.""",
        "model_id": "llama-3.3-70b-versatile",
        "temperature": 0.25,
        "max_tokens": 1100,
        "expected_output_format": """{
  "research_markdown": "string (markdown)",
  "topics": ["string"],
  "key_insights": ["string"],
  "seo_terms": ["string"],
  "faq_candidates": ["string"]
}""",
        "schema_example": """{
  "research_markdown": "## Pesquisa Web\\n\\n### Temas recorrentes\\n- Tema 1\\n- Tema 2",
  "topics": ["tema 1", "tema 2", "tema 3"],
  "key_insights": ["Insight objetivo 1", "Insight objetivo 2"],
  "seo_terms": ["resenha técnica", "vale a pena ler"],
  "faq_candidates": ["O livro é indicado para iniciantes?"]
}""",
        "created_at": datetime.utcnow(),
    },
]


async def seed_prompts():
    """Upsert default prompts into the database."""
    db = await get_database()
    prompts_collection = db["prompts"]
    
    try:
        created = 0
        updated = 0
        now = datetime.utcnow()
        touched_ids = []

        for prompt in INITIAL_PROMPTS:
            name = prompt["name"]
            existing = await prompts_collection.find_one({"name": name})
            payload = {**prompt, "updated_at": now}

            if existing:
                # Keep original creation timestamp when prompt already exists.
                payload["created_at"] = existing.get("created_at", prompt.get("created_at", now))
                await prompts_collection.update_one({"_id": existing["_id"]}, {"$set": payload})
                touched_ids.append(existing["_id"])
                updated += 1
            else:
                payload.setdefault("created_at", now)
                result = await prompts_collection.insert_one(payload)
                touched_ids.append(result.inserted_id)
                created += 1

        print(f"✅ Default prompts synchronized. Created: {created}, Updated: {updated}.")
        for i, prompt in enumerate(INITIAL_PROMPTS, 1):
            print(f"   {i}. {prompt['name']} ({prompt['model_id']})")

        return touched_ids
    
    except Exception as e:
        print(f"❌ Error seeding prompts: {e}")
        raise


async def main():
    """Main entry point."""
    print("🌱 Seeding initial prompts...")
    try:
        await seed_prompts()
        print("✨ Seed complete!")
    except Exception as e:
        print(f"Failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
