"""
Article structurer module for generating and validating article structures.
"""

from typing import List, Dict, Optional
from src.db.connection import get_database
from src.workers.llm_client import LLMClient
import re


class ArticleStructurer:
    """Handles article structure generation and validation."""

    def __init__(self):
        self.llm_client = LLMClient()

    async def extract_topics(self, book_data: Dict) -> List[Dict]:
        """
        Extract 3 main topics from the book data using LLM.
        
        Args:
            book_data: Dictionary containing book information
            
        Returns:
            List of 3 topic dictionaries with name, description, and subtopics
        """
        db = await get_database()
        prompts_collection = db["prompts"]
        
        # Get the topic extractor prompt
        prompt_doc = await prompts_collection.find_one({
            "name": "Topic Extractor for Books"
        })
        
        if not prompt_doc:
            raise ValueError("Topic Extractor prompt not found in database")
        
        # Prepare the prompt with book data
        user_prompt = prompt_doc["user_prompt"].replace("{{title}}", book_data.get("title", ""))
        user_prompt = user_prompt.replace("{{author}}", book_data.get("author", ""))
        user_prompt = user_prompt.replace("{{data}}", str(book_data))
        
        # Call LLM to extract topics
        response = await self.llm_client.generate(
            system_prompt=prompt_doc["system_prompt"],
            user_prompt=user_prompt,
            model_id=prompt_doc["model_id"],
            temperature=prompt_doc["temperature"],
            max_tokens=prompt_doc["max_tokens"]
        )
        
        # Parse the JSON response
        import json
        try:
            topics_data = json.loads(response)
            return topics_data.get("topics", [])
        except json.JSONDecodeError:
            # Fallback: try to extract topics from text
            topics = []
            topic_matches = re.findall(r"Topic\s*\d+:\s*(.*?)(?=\nTopic|$)", response, re.DOTALL)
            
            for i, match in enumerate(topic_matches[:3]):
                topic_lines = match.strip().split('\n')
                name = topic_lines[0].strip() if topic_lines else f"Topic {i+1}"
                description = topic_lines[1].strip() if len(topic_lines) > 1 else ""
                subtopics = [s.strip() for s in topic_lines[2:] if s.strip()] if len(topic_lines) > 2 else []
                
                topics.append({
                    "name": name,
                    "description": description,
                    "subtopics": subtopics
                })
            
            return topics

    async def structure_article(self, book_data: Dict, topics: List[Dict], context: str) -> str:
        """
        Generate a structured article in markdown format.
        
        Args:
            book_data: Dictionary containing book information
            topics: List of 3 topic dictionaries
            context: Generated context for the book
            
        Returns:
            Structured markdown article content
        """
        db = await get_database()
        prompts_collection = db["prompts"]
        
        # Get the article writer prompt
        prompt_doc = await prompts_collection.find_one({
            "name": "SEO-Optimized Article Writer"
        })
        
        if not prompt_doc:
            raise ValueError("SEO-Optimized Article Writer prompt not found in database")
        
        # Prepare topic information for the prompt
        topic1 = topics[0]["name"] if len(topics) > 0 else "Main Concepts"
        topic2 = topics[1]["name"] if len(topics) > 1 else "Key Techniques"
        topic3 = topics[2]["name"] if len(topics) > 2 else "Practical Applications"
        
        # Prepare the prompt
        user_prompt = prompt_doc["user_prompt"].replace("{{title}}", book_data.get("title", ""))
        user_prompt = user_prompt.replace("{{author}}", book_data.get("author", ""))
        user_prompt = user_prompt.replace("{{topic1}}", topic1)
        user_prompt = user_prompt.replace("{{topic2}}", topic2)
        user_prompt = user_prompt.replace("{{topic3}}", topic3)
        user_prompt = user_prompt.replace("{{context}}", context)
        
        # Call LLM to generate the article
        article_content = await self.llm_client.generate(
            system_prompt=prompt_doc["system_prompt"],
            user_prompt=user_prompt,
            model_id=prompt_doc["model_id"],
            temperature=prompt_doc["temperature"],
            max_tokens=prompt_doc["max_tokens"]
        )
        
        return article_content

    async def validate_article(self, article_content: str) -> Dict:
        """
        Validate the article structure and word count.
        
        Args:
            article_content: Markdown content of the article
            
        Returns:
            Dictionary with validation results and errors
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "word_count": 0,
            "section_counts": {},
            "paragraph_stats": {}
        }
        
        # Calculate word count
        words = article_content.split()
        validation_result["word_count"] = len(words)
        
        # Check total word count (bounds kept flexible for shorter UX-friendly articles)
        MIN_WORDS = 200
        MAX_WORDS = 1800
        if validation_result["word_count"] < MIN_WORDS:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Word count too low: {validation_result['word_count']} (minimum {MIN_WORDS})"
            )
        elif validation_result["word_count"] > MAX_WORDS:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Word count too high: {validation_result['word_count']} (maximum {MAX_WORDS})"
            )
        
        # Parse markdown structure
        lines = article_content.split('\n')
        
        # Count headings
        h1_count = sum(1 for line in lines if line.startswith('# '))
        h2_count = sum(1 for line in lines if line.startswith('## '))
        h3_count = sum(1 for line in lines if line.startswith('### '))
        
        validation_result["section_counts"] = {
            "h1": h1_count,
            "h2": h2_count,
            "h3": h3_count
        }
        
        # Validate heading structure
        if h1_count != 1:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Expected 1 H1 heading, found {h1_count}")
        
        if h2_count < 8:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Expected at least 8 H2 sections, found {h2_count}")
        
        # Check for at least one H2 with 2-4 H3 subsections
        h2_with_h3 = 0
        current_h2 = None
        h3_in_section = 0
        
        for line in lines:
            if line.startswith('## '):
                if current_h2 and 2 <= h3_in_section <= 4:
                    h2_with_h3 += 1
                current_h2 = line
                h3_in_section = 0
            elif line.startswith('### '):
                h3_in_section += 1
        
        # Check last section
        if current_h2 and 2 <= h3_in_section <= 4:
            h2_with_h3 += 1
        
        if h2_with_h3 < 1:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Expected at least 1 H2 section with 2-4 H3 subsections")
        
        # Validate paragraph lengths
        paragraphs = [p.strip() for p in article_content.split('\n\n') if p.strip()]
        paragraph_word_counts = [len(p.split()) for p in paragraphs]
        
        validation_result["paragraph_stats"] = {
            "total_paragraphs": len(paragraphs),
            "avg_words_per_paragraph": sum(paragraph_word_counts) / len(paragraphs) if paragraphs else 0,
            "min_words": min(paragraph_word_counts) if paragraph_word_counts else 0,
            "max_words": max(paragraph_word_counts) if paragraph_word_counts else 0
        }
        
        # Check paragraph word count (short, scannable paragraphs)
        PARA_MIN = 3   # allow succinct intro sentences
        PARA_MAX = 120
        invalid_paragraphs = [
            i for i, count in enumerate(paragraph_word_counts, 1)
            if count < PARA_MIN or count > PARA_MAX
        ]
        if invalid_paragraphs:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Paragraphs with invalid word count (should be {PARA_MIN}-{PARA_MAX} words): {invalid_paragraphs}"
            )
        
        return validation_result

    async def generate_valid_article(self, book_data: Dict, context: str, max_retries: int = 3) -> str:
        """
        Generate and validate an article, retrying if validation fails.
        
        Args:
            book_data: Dictionary containing book information
            context: Generated context for the book
            max_retries: Maximum number of retries if validation fails
            
        Returns:
            Valid article content
            
        Raises:
            ValueError: If article cannot be generated after max retries
        """
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1} to generate valid article...")
            
            # Extract topics
            topics = await self.extract_topics(book_data)
            
            # Generate article
            article_content = await self.structure_article(book_data, topics, context)
            
            # Validate article
            validation = await self.validate_article(article_content)
            
            if validation["is_valid"]:
                print("✅ Article validation passed!")
                return article_content
            else:
                print(f"❌ Article validation failed (attempt {attempt + 1}):")
                for error in validation["errors"]:
                    print(f"   - {error}")
                
                # If this is the last attempt, raise an error
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to generate valid article after {max_retries} attempts")
                
                # Otherwise, adjust parameters for retry
                print("🔄 Retrying with adjusted parameters...")
                # Here you could adjust temperature, add more specific instructions, etc.
        
        raise ValueError("Failed to generate valid article")
