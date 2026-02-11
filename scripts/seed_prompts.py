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
        "system_prompt": """You are an expert data extractor specializing in book metadata from e-commerce platforms.
Your task is to extract structured information from book pages with high accuracy.
Always return valid JSON with the exact schema provided.""",
        "user_prompt": """Extract the following metadata from the given book information:
- title_original: Original title if different from current listing
- authors: List of author names
- theme: Main theme or category
- lang_original: Language the book was originally written in
- lang_edition: Language of this edition
- edition: Edition number or description
- pub_date: Publication date (YYYY-MM-DD format if possible)
- publisher: Publisher name
- isbn: ISBN number
- pages: Number of pages
- price_physical: Price of physical book
- price_ebook: Price of ebook version
- amazon_rating: Rating on Amazon (0-5 scale)

Return ONLY valid JSON with these keys. Use null for missing information.""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 500,
        "schema_example": """{
  "title_original": "string",
  "authors": ["string"],
  "theme": "string",
  "lang_original": "string",
  "lang_edition": "string",
  "edition": "string",
  "pub_date": "string",
  "publisher": "string",
  "isbn": "string",
  "pages": 0,
  "price_physical": 0.0,
  "price_ebook": 0.0,
  "amazon_rating": 0.0
}""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "Context Generator - Technical Books",
        "purpose": "Generate structured markdown context and knowledge base for technical books",
        "system_prompt": """You are an expert technical writer and knowledge architect.
Your role is to synthesize information about technical books into a well-structured, 
markdown-formatted knowledge base that will serve as context for AI models.

Create a comprehensive, organized, and searchable knowledge base in markdown format.""",
        "user_prompt": """Based on the book information and extracted data provided below, create a structured markdown 
knowledge base for "{{title}}" by {{author}}.

Structure it with:
1. Overview section: Main topic and relevance
2. Key Concepts: Main ideas and frameworks discussed
3. Technical Details: Specific technologies, tools, or methodologies
4. Target Audience: Who should read this
5. Prerequisites: What readers should know before reading
6. Main Takeaways: Key learnings

Make it comprehensive yet readable, using headings, lists, and clear hierarchy.
Data to incorporate:
{{data}}""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1500,
        "schema_example": None,
        "created_at": datetime.utcnow(),
    },
    {
        "name": "Topic Extractor for Books",
        "purpose": "Extract 3 main topics/themes from a book to structure article sections",
        "system_prompt": """You are a book analyst expert at identifying core topics and themes.
Extract the 3 most important, distinct topics that a reader should understand about this book.
These topics will form the thematic sections of a review article.""",
        "user_prompt": """Analyze the book "{{title}}" by {{author}} and extract exactly 3 main topics/themes.

For each topic provide:
1. Topic name (2-4 words)
2. Brief description (1-2 sentences)
3. Key subtopics (3-5 bullet points)

Format as JSON:
{
  "topics": [
    {
      "name": "Topic Name",
      "description": "What this topic covers",
      "subtopics": ["subtopic1", "subtopic2", "subtopic3"]
    }
  ]
}

Book info:
{{data}}""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.5,
        "max_tokens": 600,
        "schema_example": """{
  "topics": [
    {
      "name": "Distributed Systems",
      "description": "Principles and challenges of building reliable systems across multiple machines",
      "subtopics": ["Replication", "Consistency models", "Fault tolerance"]
    }
  ]
}""",
        "created_at": datetime.utcnow(),
    },
    {
        "name": "SEO-Optimized Article Writer",
        "purpose": "Generate a complete, SEO-optimized technical book review article with proper structure",
        "system_prompt": """You are an expert SEO-optimized technical writer and book reviewer.
Your goal is to write comprehensive, well-structured articles that rank well in search engines 
while being genuinely helpful to readers.

Key guidelines:
- Use natural language with target keywords incorporated smoothly
- Structure: 1 H1 title, 8 H2 sections (3 thematic + 5 fixed), 1 H2 can have 2-4 H3 subsections
- Total length: 800-1333 words
- Paragraphs: 3-6 sentences (50-100 words each)
- Every section must provide real value
- Include practical examples when relevant""",
        "user_prompt": """Write a comprehensive SEO-optimized review article for "{{title}}" by {{author}}.

Structure:
1. [Dynamic Theme 1]: {{topic1}} (H2, 200+ words)
   - Include 2-3 H3 subsections with specific details
2. [Dynamic Theme 2]: {{topic2}} (H2, 200+ words)
   - Include 2-3 H3 subsections with specific details
3. [Dynamic Theme 3]: {{topic3}} (H2, 200+ words)
   - Include 2-3 H3 subsections with specific details
4. Introduction to Book Topic (H2, 150+ words)
5. Context and Motivation (H2, 150+ words)
6. Impact and Applicability (H2, 150+ words)
7. Book Details (H2, 100+ words): metadata, ISBN, links
8. About the Author (H2, 100+ words): biography, notable works
9. Download & Links (H2, 50+ words): purchase/reading links
10. Related Subjects (H2, 80+ words): topical links for SEO

Total word count: 800-1333 words

Context and metadata:
{{context}}""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 2500,
        "schema_example": None,
        "created_at": datetime.utcnow(),
    },
    {
        "name": "Link Summarizer",
        "purpose": "Summarize external web page content into structured markdown for knowledge base",
        "system_prompt": """You are an expert at reading web content and extracting key information.
Summarize the provided web page content into a structured markdown summary.
Focus on extracting facts, data, insights, and topic keywords relevant to the context.""",
        "user_prompt": """Summarize this web page about "{{title}}":

[Content]:
{{content}}

Create a markdown summary with:
1. Main idea (2-3 sentences)
2. Key points (5-7 bullets)
3. Relevant topics/keywords (comma-separated list)
4. Credibility/source quality (one sentence)

Keep it concise but informative (150-250 words).""",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.5,
        "max_tokens": 400,
        "schema_example": None,
        "created_at": datetime.utcnow(),
    },
]


async def seed_prompts():
    """Insert initial prompts into the database."""
    db = await get_database()
    prompts_collection = db["prompts"]
    
    try:
        # Check if prompts already exist
        count = await prompts_collection.count_documents({})
        if count > 0:
            print(f"⚠️  Database already has {count} prompts. Skipping seed.")
            return
        
        # Insert initial prompts
        result = await prompts_collection.insert_many(INITIAL_PROMPTS)
        print(f"✅ Seeded {len(result.inserted_ids)} initial prompts:")
        for i, prompt in enumerate(INITIAL_PROMPTS, 1):
            print(f"   {i}. {prompt['name']} ({prompt['model_id']})")
        
        return result.inserted_ids
    
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
