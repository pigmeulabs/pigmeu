"""External link discovery and summarization utilities."""

from __future__ import annotations

import re
from typing import List, Dict, Any
from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup

from src.workers.ai_defaults import DEFAULT_MODEL_ID
from src.workers.llm_client import LLMClient
from src.workers.prompt_builder import build_user_prompt_with_output_format


class LinkFinder:
    """Find and summarize external links related to a book."""

    SEARCH_URL = "https://duckduckgo.com/html/"

    async def search_book_links(self, title: str, author: str, count: int = 3) -> List[Dict[str, str]]:
        query = f'"{title}" "{author}" book review summary'
        url = f"{self.SEARCH_URL}?q={quote_plus(query)}"

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: List[Dict[str, str]] = []

        # Preferred DDG selectors
        for result in soup.select("div.result"):
            link = result.select_one("a.result__a")
            snippet = result.select_one("a.result__snippet, div.result__snippet")
            if not link:
                continue
            href = link.get("href")
            if not href or not href.startswith("http"):
                continue
            results.append(
                {
                    "url": href,
                    "title": link.get_text(" ", strip=True),
                    "snippet": snippet.get_text(" ", strip=True) if snippet else "",
                }
            )
            if len(results) >= count:
                break

        if len(results) < count:
            # Generic fallback
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if not href.startswith("http"):
                    continue
                if any(href == item["url"] for item in results):
                    continue
                text = link.get_text(" ", strip=True)
                if not text:
                    continue
                results.append({"url": href, "title": text, "snippet": ""})
                if len(results) >= count:
                    break

        return results[:count]

    async def fetch_and_parse(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for node in soup(["script", "style", "noscript"]):
            node.decompose()

        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = "\n".join([p for p in paragraphs if p])
        text = re.sub(r"\s+", " ", text).strip()

        # Keep content bounded for prompts
        return text[:5000]

    async def summarize_page(
        self,
        content: str,
        title: str,
        prompt_doc: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not content.strip():
            return {
                "summary": "No relevant textual content extracted.",
                "topics": [],
                "key_points": [],
                "credibility": "low",
            }

        if not prompt_doc:
            prompt_doc = {
                "system_prompt": (
                    "You summarize web pages for editorial research. "
                    "Respond in Portuguese (pt-BR) and return strict JSON only."
                ),
                "user_prompt": (
                    "Task: summarize the source content for editorial research about the book.\n"
                    "Book title: {title}\n\n"
                    "Source content:\n{content}\n\n"
                    "Return only the JSON object in Portuguese (pt-BR)."
                ),
                "expected_output_format": (
                    "{\n"
                    '  "summary": "string",\n'
                    '  "topics": ["string"],\n'
                    '  "key_points": ["string"],\n'
                    '  "credibility": "alta|media|baixa"\n'
                    "}"
                ),
                "schema_example": (
                    "{\n"
                    '  "summary": "Resumo objetivo do conteúdo com foco editorial.",\n'
                    '  "topics": ["tema 1", "tema 2"],\n'
                    '  "key_points": ["Ponto-chave 1", "Ponto-chave 2"],\n'
                    '  "credibility": "media"\n'
                    "}"
                ),
                "model_id": DEFAULT_MODEL_ID,
                "temperature": 0.4,
                "max_tokens": 500,
            }

        user_prompt = prompt_doc.get("user_prompt", "")
        user_prompt = user_prompt.replace("{{title}}", title)
        user_prompt = user_prompt.replace("{title}", title)
        user_prompt = user_prompt.replace("{{content}}", content[:2500])
        user_prompt = user_prompt.replace("{content}", content[:2500])
        user_prompt = build_user_prompt_with_output_format(user_prompt, prompt_doc)

        llm = LLMClient()
        try:
            summary = await llm.generate_with_retry(
                system_prompt=prompt_doc.get("system_prompt", ""),
                user_prompt=user_prompt,
                model_id=prompt_doc.get("model_id", DEFAULT_MODEL_ID),
                temperature=prompt_doc.get("temperature", 0.4),
                max_tokens=prompt_doc.get("max_tokens", 500),
            )
        except Exception:
            summary = content[:700]

        # Lightweight extraction of topics from text
        words = [w.strip(".,:;!?()[]{}\"'") for w in summary.split()]
        words = [w for w in words if len(w) > 4 and w.isalpha()]
        freq: Dict[str, int] = {}
        for word in words:
            key = word.lower()
            freq[key] = freq.get(key, 0) + 1

        topics = [w for w, _ in sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:6]]
        key_points = [line.strip("- ") for line in summary.splitlines() if line.strip().startswith("-")][:5]

        credibility = "medium"
        return {
            "summary": summary,
            "topics": topics,
            "key_points": key_points,
            "credibility": credibility,
        }

    @staticmethod
    def get_domain(url: str) -> str:
        try:
            return urlparse(url).netloc
        except Exception:
            return ""
