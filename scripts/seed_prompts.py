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
        "purpose": "Generate structured markdown context and knowledge base for technical books",
        "short_description": "Builds a reusable knowledge base context in Markdown.",
        "system_prompt": """You are an expert technical writer and knowledge architect optimized for API execution.
Synthesize the provided evidence into structured Markdown suitable for downstream LLM tasks.
Do not invent facts.
Respond in Portuguese (pt-BR).""",
        "user_prompt": """Task: generate a structured knowledge base for "{{title}}" by {{author}}.

Input data:
{{data}}

Requirements:
1. Use concise and objective language.
2. Keep section hierarchy clear and deterministic.
3. Highlight actionable insights.
4. Mention uncertainties explicitly when data is incomplete.
5. Respond in Portuguese (pt-BR).
6. Follow the expected output format exactly.""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1500,
        "expected_output_format": """Markdown template:
# Base de Conhecimento: <titulo>

## Visão Geral
- Tema principal
- Relevância

## Conceitos-Chave
- Conceito 1
- Conceito 2

## Detalhes Técnicos
- Ferramentas / métodos / práticas

## Público-Alvo
- Perfil recomendado

## Pré-requisitos
- Conhecimentos prévios

## Principais Aprendizados
- Aprendizado 1
- Aprendizado 2""",
        "schema_example": """# Base de Conhecimento: Scrum e Kanban

## Visão Geral
- Tema principal: gestão ágil de fluxo de trabalho
- Relevância: melhoria de previsibilidade e entrega contínua

## Conceitos-Chave
- Limites de WIP
- Ciclo de feedback curto

## Detalhes Técnicos
- Quadro Kanban
- Métricas de lead time e throughput

## Público-Alvo
- Times de produto e engenharia

## Pré-requisitos
- Noções básicas de processos de software

## Principais Aprendizados
- Como reduzir gargalos
- Como evoluir o processo com dados""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "Topic Extractor for Books",
        "purpose": "Extract 3 main topics/themes from a book to structure article sections",
        "short_description": "Extracts exactly three editorial themes in JSON.",
        "system_prompt": """You are a book analysis assistant optimized for API-based topic extraction.
Identify exactly 3 distinct themes that maximize editorial value.
Use only provided evidence.
Respond in Portuguese (pt-BR).
Return strict JSON only.""",
        "user_prompt": """Task: analyze "{{title}}" by {{author}} and extract exactly 3 core themes.

Book evidence:
{{data}}

Rules:
1. Theme names must be concise (2 to 5 words).
2. Descriptions must be objective (1 to 2 sentences).
3. Provide 3 to 5 subtopics per theme.
4. Avoid overlap between themes.
5. Respond in Portuguese (pt-BR).
6. Return only the JSON object.""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.5,
        "max_tokens": 600,
        "expected_output_format": """{
  "topics": [
    {
      "name": "string",
      "description": "string",
      "subtopics": ["string", "string", "string"]
    },
    {
      "name": "string",
      "description": "string",
      "subtopics": ["string", "string", "string"]
    },
    {
      "name": "string",
      "description": "string",
      "subtopics": ["string", "string", "string"]
    }
  ]
}""",
        "schema_example": """{
  "topics": [
    {
      "name": "Gestão de Fluxo",
      "description": "Explica como visualizar trabalho, limitar WIP e melhorar previsibilidade.",
      "subtopics": ["Quadro visual", "Limites de WIP", "Lead time"]
    },
    {
      "name": "Entrega Incremental",
      "description": "Mostra como reduzir risco por ciclos curtos de entrega e validação.",
      "subtopics": ["Lotes menores", "Feedback contínuo", "Priorização"]
    },
    {
      "name": "Melhoria Contínua",
      "description": "Aborda métricas e rotinas para evoluir o processo de forma sustentável.",
      "subtopics": ["Métricas operacionais", "Retrospectivas", "Ajustes de processo"]
    }
  ]
}""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "SEO-Optimized Article Writer",
        "purpose": "Generate a complete, SEO-optimized technical book review article with proper structure",
        "short_description": "Generates SEO article in Markdown with deterministic structure.",
        "system_prompt": """You are an SEO-focused technical reviewer optimized for API generation.
Produce high-quality, factual, and readable Markdown articles.
Use only available context and avoid unsupported claims.
Respond in Portuguese (pt-BR).""",
        "user_prompt": """Task: write a complete SEO-oriented review article for "{{title}}" by {{author}}.

Themes:
- Theme 1: {{topic1}}
- Theme 2: {{topic2}}
- Theme 3: {{topic3}}

Context:
{{context}}

Requirements:
1. Use deterministic section structure.
2. Keep clear headings and strong readability.
3. Include practical insights and editorial relevance.
4. Keep style objective and useful for readers.
5. Respond in Portuguese (pt-BR).
6. Follow the expected output format exactly.""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 2500,
        "expected_output_format": """Markdown template:
# <Título SEO do artigo>

## {{topic1}}
### Subtópico 1
### Subtópico 2

## {{topic2}}
### Subtópico 1
### Subtópico 2

## {{topic3}}
### Subtópico 1
### Subtópico 2

## Introdução ao Tema do Livro
## Contexto e Motivação
## Impacto e Aplicabilidade
## Detalhes do Livro
## Sobre o Autor
## Download e Links
## Assuntos Relacionados""",
        "schema_example": """# Scrum e Kanban: Guia Prático para Times de Produto

## Gestão de Fluxo
### Visualização do Trabalho
### Limites de WIP

## Entrega Incremental
### Redução de Risco
### Feedback Contínuo

## Melhoria Contínua
### Métricas Operacionais
### Evolução de Processo

## Introdução ao Tema do Livro
## Contexto e Motivação
## Impacto e Aplicabilidade
## Detalhes do Livro
## Sobre o Autor
## Download e Links
## Assuntos Relacionados""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "Link Summarizer",
        "purpose": "Summarize external web page content into structured markdown for knowledge base",
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
