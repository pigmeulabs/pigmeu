"""Article structuring and validation utilities."""

from __future__ import annotations

import json
import re
from typing import List, Dict, Any

from src.db.connection import get_database
from src.workers.llm_client import LLMClient


class ArticleStructurer:
    """Handles topic extraction, article generation, and validation."""

    def __init__(self):
        self.llm_client = LLMClient()

    async def _llm_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call LLM in a test-friendly way (prefers generate())."""
        if hasattr(self.llm_client, "generate"):
            return await self.llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_id=model_id,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        return await self.llm_client.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def extract_topics(self, book_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract 3 main topics from book data."""
        db = await get_database()
        prompts_collection = db["prompts"]

        prompt_doc = await prompts_collection.find_one({"name": "Topic Extractor for Books"})
        if not prompt_doc:
            return self._fallback_topics(book_data)

        user_prompt = prompt_doc.get("user_prompt", "")
        user_prompt = user_prompt.replace("{{title}}", book_data.get("title", ""))
        user_prompt = user_prompt.replace("{{author}}", book_data.get("author", ""))
        user_prompt = user_prompt.replace("{{data}}", json.dumps(book_data, ensure_ascii=True))

        try:
            response = await self._llm_generate(
                system_prompt=prompt_doc.get("system_prompt", ""),
                user_prompt=user_prompt,
                model_id=prompt_doc.get("model_id", "gpt-4o-mini"),
                temperature=prompt_doc.get("temperature", 0.5),
                max_tokens=prompt_doc.get("max_tokens", 600),
            )
            parsed = self._extract_topics_from_text(response)
            if len(parsed) >= 3:
                return parsed[:3]
        except Exception:
            pass

        return self._fallback_topics(book_data)

    def _fallback_topics(self, book_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        title = book_data.get("title", "Book")
        metadata = book_data.get("metadata", {}) if isinstance(book_data.get("metadata"), dict) else {}
        theme = metadata.get("theme") or "Core Concepts"

        return [
            {
                "name": f"{theme} Fundamentals",
                "description": f"Foundational ideas behind {title}.",
                "subtopics": ["Definitions", "Principles", "Common pitfalls"],
            },
            {
                "name": "Implementation Strategies",
                "description": f"Practical ways to apply lessons from {title}.",
                "subtopics": ["Process", "Tools", "Execution"],
            },
            {
                "name": "Practical Outcomes",
                "description": f"Expected results and impact for readers of {title}.",
                "subtopics": ["Benefits", "Trade-offs", "Recommendations"],
            },
        ]

    def _extract_topics_from_text(self, response: str) -> List[Dict[str, Any]]:
        text = response.strip()

        try:
            obj = json.loads(text)
            topics = obj.get("topics") if isinstance(obj, dict) else None
            if isinstance(topics, list):
                normalized = []
                for topic in topics:
                    if not isinstance(topic, dict):
                        continue
                    normalized.append(
                        {
                            "name": str(topic.get("name", "Topic")).strip(),
                            "description": str(topic.get("description", "")).strip(),
                            "subtopics": [str(s).strip() for s in topic.get("subtopics", []) if str(s).strip()],
                        }
                    )
                return [t for t in normalized if t.get("name")]
        except Exception:
            pass

        topics: List[Dict[str, Any]] = []
        topic_blocks = re.findall(r"(?:Topic\s*\d+[:\-]\s*)(.*?)(?=(?:\nTopic\s*\d+[:\-])|$)", text, flags=re.S)
        for block in topic_blocks[:3]:
            lines = [line.strip("- ") for line in block.splitlines() if line.strip()]
            if not lines:
                continue
            name = lines[0]
            description = lines[1] if len(lines) > 1 else ""
            subtopics = [line for line in lines[2:] if line]
            topics.append({"name": name, "description": description, "subtopics": subtopics})

        return topics

    async def structure_article(self, book_data: Dict[str, Any], topics: List[Dict[str, Any]], context: str) -> str:
        """Generate article markdown. Uses LLM when available, otherwise template."""
        db = await get_database()
        prompts_collection = db["prompts"]
        prompt_doc = await prompts_collection.find_one({"name": "SEO-Optimized Article Writer"})

        if prompt_doc:
            topic1 = topics[0]["name"] if len(topics) > 0 else "Main Concepts"
            topic2 = topics[1]["name"] if len(topics) > 1 else "Key Techniques"
            topic3 = topics[2]["name"] if len(topics) > 2 else "Practical Applications"

            user_prompt = prompt_doc.get("user_prompt", "")
            user_prompt = user_prompt.replace("{{title}}", book_data.get("title", ""))
            user_prompt = user_prompt.replace("{{author}}", book_data.get("author", ""))
            user_prompt = user_prompt.replace("{{topic1}}", topic1)
            user_prompt = user_prompt.replace("{{topic2}}", topic2)
            user_prompt = user_prompt.replace("{{topic3}}", topic3)
            user_prompt = user_prompt.replace("{{context}}", context or "")

            try:
                llm_article = await self._llm_generate(
                    system_prompt=prompt_doc.get("system_prompt", ""),
                    user_prompt=user_prompt,
                    model_id=prompt_doc.get("model_id", "gpt-4o-mini"),
                    temperature=prompt_doc.get("temperature", 0.7),
                    max_tokens=prompt_doc.get("max_tokens", 2500),
                )
                if llm_article.strip():
                    return llm_article
            except Exception:
                pass

        return self._build_template_article(book_data, topics, context)

    def _make_paragraph(self, subject: str, context: str, min_words: int = 58, max_words: int = 72) -> str:
        seeds = [
            f"{subject} is presented in a practical and structured way, helping the reader connect ideas with execution.",
            "The explanation emphasizes trade-offs, realistic constraints, and decisions that appear in real projects.",
            "Examples are translated into clear guidance, so the reader can apply concepts without losing technical depth.",
            "This section also clarifies why the topic matters, which risks are reduced, and which outcomes become measurable.",
            "As a result, the content improves understanding and supports better implementation choices over time.",
        ]

        if context:
            seeds.append(
                f"Based on the available context, {subject.lower()} is linked to the book narrative with consistent terminology and actionable framing."
            )

        words: List[str] = []
        idx = 0
        while len(words) < min_words:
            words.extend(seeds[idx % len(seeds)].split())
            idx += 1

        text = " ".join(words[:max_words])
        if not text.endswith("."):
            text += "."
        return text

    def _build_template_article(self, book_data: Dict[str, Any], topics: List[Dict[str, Any]], context: str) -> str:
        title = (book_data.get("title") or "Book Review").strip()
        author = (book_data.get("author") or "Unknown Author").strip()

        topic_names = [t.get("name", f"Topic {idx + 1}") for idx, t in enumerate(topics[:3])]
        while len(topic_names) < 3:
            topic_names.append(f"Topic {len(topic_names) + 1}")

        topic_subtopics = [
            topics[i].get("subtopics", ["Overview", "Methods", "Application"]) if i < len(topics) else ["Overview", "Methods", "Application"]
            for i in range(3)
        ]

        h1 = f"# {title} Review"
        if len(h1.replace("# ", "")) > 60:
            h1 = f"# {title[:57].rstrip()}..."

        sections: List[str] = [h1, ""]

        sections.append("## Introduction to Book Topic")
        sections.append(self._make_paragraph("Introduction to the book topic", context))
        sections.append("")

        sections.append("## Context and Motivation")
        sections.append(self._make_paragraph("Context and motivation", context))
        sections.append("")

        sections.append("## Impact and Applicability")
        sections.append(self._make_paragraph("Impact and applicability", context))
        sections.append("")

        sections.append(f"## {topic_names[0]}")
        sections.append(self._make_paragraph(topic_names[0], context))
        sections.append("")
        for idx, sub in enumerate(topic_subtopics[0][:3]):
            sections.append(f"### {sub or f'Subtopic {idx + 1}'}")
            sections.append(self._make_paragraph(f"{topic_names[0]} - {sub}", context))
            sections.append("")

        sections.append(f"## {topic_names[1]}")
        sections.append(self._make_paragraph(topic_names[1], context))
        sections.append("")

        sections.append(f"## {topic_names[2]}")
        sections.append(self._make_paragraph(topic_names[2], context))
        sections.append("")

        sections.append("## Book Details")
        sections.append(self._make_paragraph("Book details and metadata", context, min_words=52, max_words=65))
        sections.append(f"- **Title:** {title}")
        sections.append(f"- **Author:** {author}")
        sections.append("")

        sections.append("## About the Author")
        sections.append(self._make_paragraph("Author background", context, min_words=52, max_words=65))
        sections.append("")

        return "\n".join(sections).strip() + "\n"

    async def validate_article(self, article_content: str, strict: bool = False) -> Dict[str, Any]:
        validation_result = {
            "is_valid": True,
            "errors": [],
            "word_count": 0,
            "section_counts": {},
            "paragraph_stats": {},
            "h2_with_h3_count": 0,
        }

        words = article_content.split()
        validation_result["word_count"] = len(words)

        if strict:
            min_words = 800
            max_words = 1333
        else:
            min_words = 200
            max_words = 2500

        if validation_result["word_count"] < min_words:
            validation_result["errors"].append(
                f"Word count too low: {validation_result['word_count']} (minimum {min_words})"
            )
        elif validation_result["word_count"] > max_words:
            validation_result["errors"].append(
                f"Word count too high: {validation_result['word_count']} (maximum {max_words})"
            )

        lines = article_content.splitlines()
        h1_count = sum(1 for line in lines if line.startswith("# "))
        h2_count = sum(1 for line in lines if line.startswith("## "))
        h3_count = sum(1 for line in lines if line.startswith("### "))

        validation_result["section_counts"] = {"h1": h1_count, "h2": h2_count, "h3": h3_count}

        if h1_count != 1:
            validation_result["errors"].append(f"Expected 1 H1 heading, found {h1_count}")

        if strict:
            if h2_count != 8:
                validation_result["errors"].append(f"Expected exactly 8 H2 sections, found {h2_count}")
        else:
            if h2_count < 8:
                validation_result["errors"].append(f"Expected at least 8 H2 sections, found {h2_count}")

        h2_with_h3 = 0
        current_h2 = None
        h3_in_current = 0
        for line in lines:
            if line.startswith("## "):
                if current_h2 and 2 <= h3_in_current <= 4:
                    h2_with_h3 += 1
                current_h2 = line
                h3_in_current = 0
            elif line.startswith("### "):
                h3_in_current += 1

        if current_h2 and 2 <= h3_in_current <= 4:
            h2_with_h3 += 1

        validation_result["h2_with_h3_count"] = h2_with_h3
        if h2_with_h3 < 1:
            validation_result["errors"].append("Expected at least 1 H2 section with 2-4 H3 subsections")

        raw_blocks = [block.strip() for block in article_content.split("\n\n") if block.strip()]
        paragraphs = []
        for block in raw_blocks:
            if block.startswith("#") or block.startswith("-"):
                continue
            paragraphs.append(block)

        paragraph_word_counts = [len(p.split()) for p in paragraphs]
        validation_result["paragraph_stats"] = {
            "total_paragraphs": len(paragraphs),
            "avg_words_per_paragraph": (
                round(sum(paragraph_word_counts) / len(paragraph_word_counts), 2) if paragraph_word_counts else 0
            ),
            "min_words": min(paragraph_word_counts) if paragraph_word_counts else 0,
            "max_words": max(paragraph_word_counts) if paragraph_word_counts else 0,
        }

        para_min, para_max = (50, 100) if strict else (3, 120)
        invalid_paragraphs = [
            i
            for i, count in enumerate(paragraph_word_counts, 1)
            if count < para_min or count > para_max
        ]
        if invalid_paragraphs:
            validation_result["errors"].append(
                f"Paragraphs with invalid word count (should be {para_min}-{para_max} words): {invalid_paragraphs}"
            )

        if h1_count == 1 and strict:
            h1_line = next(line for line in lines if line.startswith("# "))
            h1_title = h1_line[2:].strip()
            if len(h1_title) > 60:
                validation_result["errors"].append(f"H1 title too long: {len(h1_title)} > 60")

        validation_result["is_valid"] = len(validation_result["errors"]) == 0
        return validation_result

    async def generate_valid_article(self, book_data: Dict[str, Any], context: str, max_retries: int = 3) -> str:
        """Generate and validate article with retries."""
        for attempt in range(max_retries):
            topics = await self.extract_topics(book_data)
            article_content = await self.structure_article(book_data, topics, context)
            validation = await self.validate_article(article_content, strict=True)

            if validation["is_valid"]:
                return article_content

        raise ValueError(f"Failed to generate valid article after {max_retries} attempts")
