"""Article structuring and validation utilities."""

from __future__ import annotations

import json
import math
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urlparse

from bson import ObjectId

from src.db.connection import get_database
from src.workers.ai_defaults import (
    BOOK_REVIEW_ARTICLE_MODEL_ID,
    DEFAULT_MODEL_ID,
    MODEL_MISTRAL_LARGE_LATEST,
)
from src.workers.llm_client import LLMClient
from src.workers.prompt_builder import build_user_prompt_with_output_format


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
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        allow_fallback: bool = True,
    ) -> str:
        """Call LLM in a test-friendly way (prefers generate())."""
        if hasattr(self.llm_client, "generate"):
            return await self.llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_id=model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                provider=provider,
                api_key=api_key,
                allow_fallback=allow_fallback,
            )
        return await self.llm_client.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=provider,
            api_key=api_key,
            allow_fallback=allow_fallback,
        )

    async def extract_topics(
        self,
        book_data: Dict[str, Any],
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Extract 3 main topics from book data."""
        db = await get_database()
        prompts_collection = db["prompts"]
        config = llm_config or {}

        prompt_doc = await prompts_collection.find_one({"name": "Topic Extractor for Books"})
        if not prompt_doc:
            return self._fallback_topics(book_data)

        user_prompt = prompt_doc.get("user_prompt", "")
        user_prompt = user_prompt.replace("{{title}}", book_data.get("title", ""))
        user_prompt = user_prompt.replace("{{author}}", book_data.get("author", ""))
        user_prompt = user_prompt.replace("{{data}}", json.dumps(book_data, ensure_ascii=True))
        user_prompt = build_user_prompt_with_output_format(user_prompt, prompt_doc)

        model_id = str(config.get("model_id") or prompt_doc.get("model_id", MODEL_MISTRAL_LARGE_LATEST))
        try:
            temperature = float(config.get("temperature") if config.get("temperature") is not None else prompt_doc.get("temperature", 0.5))
        except (TypeError, ValueError):
            temperature = 0.5
        try:
            max_tokens = int(config.get("max_tokens") if config.get("max_tokens") is not None else prompt_doc.get("max_tokens", 600))
        except (TypeError, ValueError):
            max_tokens = 600
        provider = str(config.get("provider") or "").strip().lower() or None
        api_key = str(config.get("api_key") or "").strip() or None
        allow_fallback = bool(config.get("allow_fallback", True))

        try:
            response = await self._llm_generate(
                system_prompt=prompt_doc.get("system_prompt", ""),
                user_prompt=user_prompt,
                model_id=model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                provider=provider,
                api_key=api_key,
                allow_fallback=allow_fallback,
            )
            parsed = self._extract_topics_from_text(response)
            if len(parsed) >= 3:
                return parsed[:3]
        except Exception:
            pass

        return self._fallback_topics(book_data)

    def _fallback_topics(self, book_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        title = book_data.get("title", "Livro")
        metadata = book_data.get("metadata", {}) if isinstance(book_data.get("metadata"), dict) else {}
        theme = metadata.get("theme") or "Conceitos Centrais"

        return [
            {
                "name": f"Fundamentos de {theme}",
                "description": f"Apresenta as ideias essenciais do livro {title}.",
                "subtopics": ["Definições", "Princípios", "Erros comuns"],
            },
            {
                "name": "Estratégias de Implementação",
                "description": f"Mostra formas práticas de aplicar os aprendizados de {title}.",
                "subtopics": ["Processo", "Ferramentas", "Execução"],
            },
            {
                "name": "Resultados na Prática",
                "description": f"Resume impactos esperados para quem aplicar os conceitos de {title}.",
                "subtopics": ["Benefícios", "Trade-offs", "Recomendações"],
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
                            "name": str(topic.get("name", "Tópico")).strip(),
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

    def _normalize_schema_toc(self, content_schema: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not isinstance(content_schema, dict):
            return []

        raw_items = content_schema.get("toc_template")
        if not isinstance(raw_items, list):
            return []

        normalized: List[Dict[str, Any]] = []
        for idx, raw in enumerate(raw_items):
            if not isinstance(raw, dict):
                continue

            level = str(raw.get("level") or "h2").strip().lower()
            if level not in {"h2", "h3"}:
                level = "h2"

            title_template = str(raw.get("title_template") or "").strip() or f"Section {idx + 1}"
            try:
                position = int(raw.get("position", idx))
            except Exception:
                position = idx
            normalized.append(
                {
                    "index": idx,
                    "position": position,
                    "level": level,
                    "title_template": title_template,
                    "content_mode": str(raw.get("content_mode") or "dynamic"),
                    "specific_content_hint": str(raw.get("specific_content_hint") or "").strip(),
                    "min_paragraphs": raw.get("min_paragraphs"),
                    "max_paragraphs": raw.get("max_paragraphs"),
                    "min_words": raw.get("min_words"),
                    "max_words": raw.get("max_words"),
                    "source_fields": raw.get("source_fields") if isinstance(raw.get("source_fields"), list) else [],
                    "prompt_id": str(raw.get("prompt_id")) if raw.get("prompt_id") else None,
                }
            )

        normalized.sort(key=lambda item: (item.get("position", 0), item.get("index", 0)))
        return normalized

    @staticmethod
    def _is_optional_toc_item(item: Dict[str, Any]) -> bool:
        title_template = str(item.get("title_template") or "").lower()
        hint = str(item.get("specific_content_hint") or "").lower()
        return "optional" in title_template or "opcional" in title_template or "optional" in hint or "opcional" in hint

    def _render_title_template(
        self,
        template: str,
        level: str,
        topic_names: List[str],
        subtopic_names: List[str],
        fallback_index: int,
    ) -> str:
        title = str(template or "").strip() or f"Section {fallback_index}"
        lowered = title.lower()

        replacement = None
        if "[" in title and "]" in title:
            if "subtema" in lowered or "subtopic" in lowered:
                replacement = subtopic_names.pop(0) if subtopic_names else f"Subtema {fallback_index}"
            elif "tópico" in lowered or "topico" in lowered or "topic" in lowered:
                replacement = topic_names.pop(0) if topic_names else f"Tópico {fallback_index}"
            else:
                replacement = (
                    (subtopic_names.pop(0) if subtopic_names else None)
                    if level == "h3"
                    else (topic_names.pop(0) if topic_names else None)
                ) or f"Tópico {fallback_index}"
            title = re.sub(r"\[[^\]]+\]", replacement, title, count=1)

        title = re.sub(r"\((?:optional|opcional)\)", "", title, flags=re.I).strip()
        return title or f"Section {fallback_index}"

    @staticmethod
    def _to_positive_int(value: Any, default: int) -> int:
        try:
            parsed = int(value)
            return parsed if parsed > 0 else default
        except Exception:
            return default

    @staticmethod
    def _to_non_negative_int(value: Any, default: int) -> int:
        try:
            parsed = int(value)
            return parsed if parsed >= 0 else default
        except Exception:
            return default

    def _section_word_bounds(self, item: Dict[str, Any], level: str) -> tuple[int, int]:
        default_min = 90 if level == "h2" else 70
        min_words = self._to_positive_int(item.get("min_words"), default_min)
        max_words = self._to_positive_int(item.get("max_words"), max(min_words + 30, int(min_words * 1.35)))
        if max_words < min_words:
            max_words = min_words
        return min_words, max_words

    @staticmethod
    def _is_empty_value(value: Any) -> bool:
        return value in (None, "", [], {}, ())

    @staticmethod
    def _stringify_value(value: Any) -> str:
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (int, float, bool)):
            return str(value)
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            return str(value)

    def _resolve_source_field_values(self, data: Any, path: str) -> List[Any]:
        tokens = [segment.strip() for segment in str(path or "").split(".") if segment.strip()]
        if not tokens:
            return []

        def _walk(current: Any, remaining: List[str]) -> List[Any]:
            if not remaining:
                return [current]

            token = remaining[0]
            tail = remaining[1:]
            results: List[Any] = []

            if isinstance(current, list):
                if token.isdigit():
                    index = int(token)
                    if 0 <= index < len(current):
                        results.extend(_walk(current[index], tail))
                else:
                    for item in current:
                        results.extend(_walk(item, remaining))
                return results

            if isinstance(current, dict):
                if token in current:
                    results.extend(_walk(current[token], tail))
                return results

            return []

        resolved = _walk(data, tokens)
        if resolved:
            return resolved
        return [data.get(path)] if isinstance(data, dict) and path in data else []

    def _schema_reference_lines(self, item: Dict[str, Any], book_data: Dict[str, Any]) -> List[str]:
        source_fields = item.get("source_fields") if isinstance(item.get("source_fields"), list) else []
        if not source_fields:
            return []

        scoped_data = {
            **book_data,
            "metadata": book_data.get("metadata", {}) if isinstance(book_data.get("metadata"), dict) else {},
            "consolidated_bibliographic": (
                book_data.get("consolidated_bibliographic", {})
                if isinstance(book_data.get("consolidated_bibliographic"), dict)
                else {}
            ),
            "web_research": book_data.get("web_research", {}) if isinstance(book_data.get("web_research"), dict) else {},
            "summaries": book_data.get("summaries", []) if isinstance(book_data.get("summaries"), list) else [],
        }

        lines: List[str] = []
        for field in source_fields:
            field_name = str(field or "").strip()
            if not field_name:
                continue

            raw_values = self._resolve_source_field_values(scoped_data, field_name)
            values = []
            for raw in raw_values:
                if self._is_empty_value(raw):
                    continue
                if isinstance(raw, list):
                    for item_value in raw:
                        if not self._is_empty_value(item_value):
                            values.append(item_value)
                else:
                    values.append(raw)

            if not values:
                continue

            formatted_values: List[str] = []
            for value in values:
                rendered_value = self._stringify_value(value)
                if rendered_value:
                    formatted_values.append(rendered_value)
            if not formatted_values:
                continue

            unique_values: List[str] = []
            for value in formatted_values:
                if value not in unique_values:
                    unique_values.append(value)
            rendered = "; ".join(unique_values[:3])
            lines.append(f"- **{field_name}**: {rendered}")

        return lines

    @staticmethod
    def _word_count(text: str) -> int:
        if not text:
            return 0
        return len(re.findall(r"\b[\wÀ-ÿ'-]+\b", text))

    @staticmethod
    def _truncate_to_words(text: str, max_words: int) -> str:
        if max_words <= 0:
            return ""
        words = re.findall(r"\S+", text)
        if len(words) <= max_words:
            return text.strip()
        trimmed = " ".join(words[:max_words]).strip()
        if trimmed and trimmed[-1] not in ".!?":
            trimmed += "."
        return trimmed

    def _split_paragraphs(self, text: str) -> List[str]:
        if not text:
            return []
        normalized = text.strip()
        if not normalized:
            return []

        blocks = [block.strip() for block in re.split(r"\n\s*\n", normalized) if block.strip()]
        paragraphs: List[str] = []
        for block in blocks:
            lines = [line.rstrip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue
            joined = "\n".join(lines).strip()
            if not joined or joined.startswith("#"):
                continue
            paragraphs.append(joined)

        if paragraphs:
            return paragraphs

        line_paragraphs = [line.strip() for line in normalized.splitlines() if line.strip() and not line.strip().startswith("#")]
        return line_paragraphs

    def _section_paragraph_bounds(self, item: Dict[str, Any], level: str) -> tuple[int, int]:
        default_min = 2 if level == "h2" else 1
        default_max = 4 if level == "h2" else 3

        min_paragraphs = self._to_non_negative_int(item.get("min_paragraphs"), default_min)
        max_paragraphs = self._to_non_negative_int(item.get("max_paragraphs"), default_max)
        if max_paragraphs < min_paragraphs:
            max_paragraphs = min_paragraphs
        if max_paragraphs == 0:
            max_paragraphs = default_max
        if min_paragraphs == 0:
            min_paragraphs = default_min
        return min_paragraphs, max_paragraphs

    def _strip_section_heading(self, content: str, expected_title: str) -> str:
        text = str(content or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text).strip()

        lines = [line for line in text.splitlines()]
        while lines and not lines[0].strip():
            lines.pop(0)

        if lines:
            first = lines[0].strip()
            if first.startswith("#"):
                first_clean = re.sub(r"^#{1,6}\s*", "", first).strip().lower()
                if first_clean == expected_title.strip().lower() or first_clean:
                    lines = lines[1:]

        cleaned = "\n".join(lines).strip()
        return cleaned

    def _enforce_section_constraints(
        self,
        section_text: str,
        title: str,
        context: str,
        min_words: int,
        max_words: int,
        min_paragraphs: int,
        max_paragraphs: int,
    ) -> str:
        content = str(section_text or "").strip()
        paragraphs = self._split_paragraphs(content)
        if not paragraphs:
            paragraphs = [self._make_paragraph(title, context, min_words=max(18, min_words // max(min_paragraphs, 1)), max_words=max(28, max_words // max(min_paragraphs, 1)))]

        if len(paragraphs) > max_paragraphs:
            kept = paragraphs[:max_paragraphs]
            overflow = " ".join(paragraphs[max_paragraphs:])
            if overflow.strip():
                kept[-1] = f"{kept[-1].rstrip()} {overflow.strip()}".strip()
            paragraphs = kept

        per_paragraph_target = max(18, math.ceil(min_words / max(min_paragraphs, 1)))
        while len(paragraphs) < min_paragraphs:
            paragraphs.append(
                self._make_paragraph(
                    subject=title,
                    context=context,
                    min_words=per_paragraph_target,
                    max_words=max(per_paragraph_target + 20, per_paragraph_target),
                )
            )

        content = "\n\n".join(paragraphs).strip()
        current_words = self._word_count(content)
        if current_words < min_words:
            missing = min_words - current_words
            content = f"{content}\n\n{self._make_paragraph(title, context, min_words=missing, max_words=missing + 25)}".strip()
            paragraphs = self._split_paragraphs(content)
            if len(paragraphs) > max_paragraphs:
                kept = paragraphs[:max_paragraphs]
                overflow = " ".join(paragraphs[max_paragraphs:])
                if overflow.strip():
                    kept[-1] = f"{kept[-1].rstrip()} {overflow.strip()}".strip()
                content = "\n\n".join(kept).strip()

        content = self._truncate_to_words(content, max_words)
        paragraphs = self._split_paragraphs(content)
        if len(paragraphs) > max_paragraphs:
            kept = paragraphs[:max_paragraphs]
            overflow = " ".join(paragraphs[max_paragraphs:])
            if overflow.strip():
                kept[-1] = f"{kept[-1].rstrip()} {overflow.strip()}".strip()
            content = "\n\n".join(kept).strip()

        return content

    @staticmethod
    def _extract_markdown_links(text: str) -> List[str]:
        return [match.group(1).strip() for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text or "") if match.group(1).strip()]

    @staticmethod
    def _is_internal_url(url: str, internal_domains: List[str]) -> bool:
        raw = str(url or "").strip()
        if not raw:
            return False
        if raw.startswith("/"):
            return True
        parsed = urlparse(raw)
        domain = parsed.netloc.lower()
        if not domain:
            return raw.startswith("#")
        for candidate in internal_domains:
            normalized = candidate.lower().strip()
            if not normalized:
                continue
            if domain == normalized or domain.endswith(f".{normalized}"):
                return True
        return False

    @staticmethod
    def _slugify(value: str) -> str:
        text = re.sub(r"[^\w\s-]", "", str(value or "").lower(), flags=re.UNICODE).strip()
        return re.sub(r"[\s_-]+", "-", text).strip("-")

    def _infer_internal_site_base(self, book_data: Dict[str, Any]) -> str:
        metadata = book_data.get("metadata", {}) if isinstance(book_data.get("metadata"), dict) else {}
        consolidated = (
            book_data.get("consolidated_bibliographic", {})
            if isinstance(book_data.get("consolidated_bibliographic"), dict)
            else {}
        )
        candidates = [
            metadata.get("wordpress_url"),
            metadata.get("site_url"),
            consolidated.get("wordpress_url"),
            consolidated.get("site_url"),
        ]
        for candidate in candidates:
            value = str(candidate or "").strip().rstrip("/")
            if value.startswith("http://") or value.startswith("https://"):
                return value
        return "https://analisederequisitos.com.br"

    def _collect_link_candidates(
        self,
        book_data: Dict[str, Any],
        topics: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, str]]]:
        site_base = self._infer_internal_site_base(book_data)
        internal_candidates: List[Dict[str, str]] = []
        external_candidates: List[Dict[str, str]] = []

        topic_names = [str(topic.get("name") or "").strip() for topic in topics if isinstance(topic, dict)]
        for topic in topic_names:
            if not topic:
                continue
            slug = self._slugify(topic)
            if not slug:
                continue
            internal_candidates.append({"label": topic, "url": f"{site_base}/{slug}"})

        web_research = book_data.get("web_research", {}) if isinstance(book_data.get("web_research"), dict) else {}
        for web_topic in web_research.get("topics", []) if isinstance(web_research.get("topics"), list) else []:
            label = str(web_topic or "").strip()
            if not label:
                continue
            slug = self._slugify(label)
            if not slug:
                continue
            internal_candidates.append({"label": label, "url": f"{site_base}/{slug}"})

        summaries = book_data.get("summaries", []) if isinstance(book_data.get("summaries"), list) else []
        for summary in summaries:
            if not isinstance(summary, dict):
                continue
            source_url = str(summary.get("source_url") or "").strip()
            if source_url:
                source_domain = str(summary.get("source_domain") or "").strip() or urlparse(source_url).netloc
                label = source_domain or "Reference"
                external_candidates.append({"label": label, "url": source_url})

        for url_key, label in [
            ("amazon_url", "Amazon"),
            ("goodreads_url", "Goodreads"),
            ("author_site", "Author Site"),
        ]:
            raw_url = str(book_data.get(url_key) or "").strip()
            if raw_url:
                external_candidates.append({"label": label, "url": raw_url})

        for link in book_data.get("other_links", []) if isinstance(book_data.get("other_links"), list) else []:
            raw_link = str(link or "").strip()
            if raw_link:
                external_candidates.append({"label": urlparse(raw_link).netloc or "External", "url": raw_link})

        title = str(book_data.get("title") or "").strip()
        author = str(book_data.get("author") or "").strip()
        if title:
            external_candidates.append(
                {
                    "label": "Wikipedia",
                    "url": f"https://pt.wikipedia.org/wiki/{quote_plus(title)}",
                }
            )
        if author:
            external_candidates.append(
                {
                    "label": "Author profile",
                    "url": f"https://www.google.com/search?q={quote_plus(author)}",
                }
            )

        def _dedupe(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
            seen = set()
            unique: List[Dict[str, str]] = []
            for item in items:
                url = str(item.get("url") or "").strip()
                if not url or url in seen:
                    continue
                seen.add(url)
                label = str(item.get("label") or "").strip() or url
                unique.append({"label": label, "url": url})
            return unique

        return {
            "internal": _dedupe(internal_candidates),
            "external": _dedupe(external_candidates),
            "site_base": site_base,
        }

    @staticmethod
    def _distribute_counts(total: int, buckets: int) -> List[int]:
        if total <= 0 or buckets <= 0:
            return [0] * max(buckets, 0)
        base = total // buckets
        remainder = total % buckets
        return [base + (1 if index < remainder else 0) for index in range(buckets)]

    def _build_rendered_toc(
        self,
        content_schema: Dict[str, Any],
        topics: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        topic_names = [str(item.get("name") or "").strip() for item in (topics or []) if str(item.get("name") or "").strip()]
        if not topic_names:
            topic_names = [f"Tópico {i}" for i in range(1, 7)]

        subtopic_names: List[str] = []
        for topic in topics or []:
            if not isinstance(topic, dict):
                continue
            for subtopic in topic.get("subtopics", []) if isinstance(topic.get("subtopics"), list) else []:
                label = str(subtopic or "").strip()
                if label:
                    subtopic_names.append(label)
        if not subtopic_names:
            subtopic_names = [f"Subtema {i}" for i in range(1, 21)]

        rendered_items: List[Dict[str, Any]] = []
        for index, item in enumerate(self._normalize_schema_toc(content_schema), start=1):
            level = item.get("level", "h2")
            rendered_title = self._render_title_template(
                template=item.get("title_template", ""),
                level=level,
                topic_names=topic_names,
                subtopic_names=subtopic_names,
                fallback_index=index,
            )
            rendered_items.append(
                {
                    **item,
                    "rendered_title": rendered_title,
                    "optional": self._is_optional_toc_item(item),
                }
            )

        return rendered_items

    @staticmethod
    def _build_title_pattern(title_template: str) -> re.Pattern[str]:
        normalized = re.sub(r"\((?:optional|opcional)\)", "", str(title_template or ""), flags=re.I).strip()
        if not normalized:
            return re.compile(r".+", flags=re.I)
        escaped = re.escape(normalized)
        escaped = re.sub(r"\\\[[^\]]+\\\]", r".+", escaped)
        escaped = escaped.replace(r"\ ", r"\s+")
        return re.compile(rf"^{escaped}$", flags=re.I)

    async def _load_schema_prompts(self, content_schema: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        toc_items = self._normalize_schema_toc(content_schema)
        prompt_ids: List[str] = []
        for item in toc_items:
            prompt_id = str(item.get("prompt_id") or "").strip()
            if prompt_id:
                prompt_ids.append(prompt_id)
        if not prompt_ids:
            return {}

        object_ids: List[ObjectId] = []
        for prompt_id in prompt_ids:
            try:
                object_id = ObjectId(prompt_id)
                object_ids.append(object_id)
            except Exception:
                continue

        if not object_ids:
            return {}

        db = await get_database()
        prompts_collection = db["prompts"]
        docs = await prompts_collection.find({"_id": {"$in": object_ids}}).to_list(length=None)

        result: Dict[str, Dict[str, Any]] = {}
        for doc in docs:
            key = str(doc.get("_id"))
            if key:
                result[key] = doc
        return result

    def _resolve_llm_parameters(
        self,
        llm_config: Dict[str, Any],
        prompt_doc: Optional[Dict[str, Any]],
        default_temperature: float = 0.7,
        default_max_tokens: int = 1200,
    ) -> Dict[str, Any]:
        model_id = str(llm_config.get("model_id") or (prompt_doc or {}).get("model_id") or DEFAULT_MODEL_ID)
        try:
            temperature = float(
                llm_config.get("temperature")
                if llm_config.get("temperature") is not None
                else (prompt_doc or {}).get("temperature", default_temperature)
            )
        except (TypeError, ValueError):
            temperature = default_temperature

        try:
            max_tokens = int(
                llm_config.get("max_tokens")
                if llm_config.get("max_tokens") is not None
                else (prompt_doc or {}).get("max_tokens", default_max_tokens)
            )
        except (TypeError, ValueError):
            max_tokens = default_max_tokens

        provider = str(llm_config.get("provider") or "").strip().lower() or None
        api_key = str(llm_config.get("api_key") or "").strip() or None
        allow_fallback = bool(llm_config.get("allow_fallback", True))
        return {
            "model_id": model_id,
            "temperature": temperature,
            "max_tokens": max(100, max_tokens),
            "provider": provider,
            "api_key": api_key,
            "allow_fallback": allow_fallback,
        }

    def _build_section_user_prompt(
        self,
        prompt_template: str,
        book_data: Dict[str, Any],
        context: str,
        section_item: Dict[str, Any],
        source_lines: List[str],
        min_words: int,
        max_words: int,
        min_paragraphs: int,
        max_paragraphs: int,
        internal_links_target: int,
        external_links_target: int,
    ) -> str:
        section_title = str(section_item.get("rendered_title") or "")
        section_level = str(section_item.get("level") or "h2").upper()
        source_block = "\n".join(source_lines) if source_lines else "- nenhum"
        content_mode = str(section_item.get("content_mode") or "dynamic")
        specific_hint = str(section_item.get("specific_content_hint") or "").strip()

        prompt = str(prompt_template or "").strip()
        if not prompt:
            prompt = (
                "Escreva APENAS o conteúdo do corpo de uma seção em markdown.\n"
                "Não inclua marcadores de título (sem #, ##, ###).\n"
                "Use as referências e restrições fornecidas."
            )

        prompt = prompt.replace("{{title}}", str(book_data.get("title") or ""))
        prompt = prompt.replace("{{author}}", str(book_data.get("author") or ""))
        prompt = prompt.replace("{{context}}", context or "")
        prompt = prompt.replace("{{data}}", json.dumps(book_data, ensure_ascii=False, default=str))
        prompt = prompt.replace("{{section_title}}", section_title)
        prompt = prompt.replace("{{section_level}}", section_level)
        prompt = prompt.replace("{{source_data}}", source_block)
        prompt = prompt.replace("{{specific_content_hint}}", specific_hint)

        constraints = [
            "Restrições da seção:",
            f"- nível: {section_level}",
            f"- título da seção: {section_title}",
            f"- modo de conteúdo: {content_mode}",
            f"- palavras mínimas: {min_words}",
            f"- palavras máximas: {max_words}",
            f"- parágrafos mínimos: {min_paragraphs}",
            f"- parágrafos máximos: {max_paragraphs}",
            f"- links internos nesta seção: {internal_links_target}",
            f"- links externos nesta seção: {external_links_target}",
            "- idioma obrigatório: Português (pt-BR).",
            "- estilo: didático, analítico, objetivo e prático para leitores técnicos.",
            "- evite texto genérico e evite afirmações sem evidência.",
            "- retorne somente o corpo da seção em markdown, sem blocos de código.",
            "- preserve consistência factual com os dados de origem.",
            "",
            "Dados de origem desta seção:",
            source_block,
        ]
        if specific_hint:
            constraints.extend(["", f"Orientação específica: {specific_hint}"])

        return f"{prompt}\n\n" + "\n".join(constraints)

    async def _generate_schema_section(
        self,
        book_data: Dict[str, Any],
        context: str,
        section_item: Dict[str, Any],
        source_lines: List[str],
        prompt_doc: Optional[Dict[str, Any]],
        llm_config: Dict[str, Any],
        min_words: int,
        max_words: int,
        min_paragraphs: int,
        max_paragraphs: int,
        internal_links_target: int,
        external_links_target: int,
    ) -> str:
        default_prompt = (
            "Escreva o corpo de uma seção para artigo de book review em português (pt-BR).\n"
            "Use linguagem concisa, factual e estruturada."
        )
        system_prompt = str((prompt_doc or {}).get("system_prompt") or default_prompt)
        user_template = str((prompt_doc or {}).get("user_prompt") or "")
        user_prompt = self._build_section_user_prompt(
            prompt_template=user_template,
            book_data=book_data,
            context=context,
            section_item=section_item,
            source_lines=source_lines,
            min_words=min_words,
            max_words=max_words,
            min_paragraphs=min_paragraphs,
            max_paragraphs=max_paragraphs,
            internal_links_target=internal_links_target,
            external_links_target=external_links_target,
        )
        user_prompt = build_user_prompt_with_output_format(user_prompt, prompt_doc)

        llm_params = self._resolve_llm_parameters(llm_config=llm_config, prompt_doc=prompt_doc)
        section_text = ""
        try:
            section_text = await self._llm_generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_id=llm_params["model_id"],
                temperature=llm_params["temperature"],
                max_tokens=llm_params["max_tokens"],
                provider=llm_params["provider"],
                api_key=llm_params["api_key"],
                allow_fallback=llm_params["allow_fallback"],
            )
        except Exception:
            section_text = ""

        section_text = self._strip_section_heading(section_text, str(section_item.get("rendered_title") or ""))
        if not section_text:
            section_text = self._make_paragraph(
                subject=str(section_item.get("rendered_title") or "Section"),
                context=context,
                min_words=min_words,
                max_words=max_words,
            )

        section_text = self._enforce_section_constraints(
            section_text=section_text,
            title=str(section_item.get("rendered_title") or "Section"),
            context=context,
            min_words=min_words,
            max_words=max_words,
            min_paragraphs=min_paragraphs,
            max_paragraphs=max_paragraphs,
        )

        return section_text.strip()

    async def _build_schema_article(
        self,
        book_data: Dict[str, Any],
        topics: List[Dict[str, Any]],
        context: str,
        content_schema: Dict[str, Any],
        default_prompt_doc: Optional[Dict[str, Any]],
        llm_config: Dict[str, Any],
    ) -> str:
        toc_items = self._build_rendered_toc(content_schema=content_schema, topics=topics)
        if not toc_items:
            return self._build_schema_template_article(
                book_data=book_data,
                context=context,
                content_schema=content_schema,
                topics=topics,
            )

        schema_prompts = await self._load_schema_prompts(content_schema)
        link_candidates = self._collect_link_candidates(book_data=book_data, topics=topics)
        internal_links_target = max(0, self._to_non_negative_int(content_schema.get("internal_links_count"), 0))
        external_links_target = max(0, self._to_non_negative_int(content_schema.get("external_links_count"), 0))

        if len(link_candidates["internal"]) < internal_links_target:
            site_base = str(link_candidates.get("site_base") or "https://analisederequisitos.com.br").rstrip("/")
            start = len(link_candidates["internal"]) + 1
            for idx in range(start, internal_links_target + 1):
                link_candidates["internal"].append(
                    {
                        "label": f"Internal Reference {idx}",
                        "url": f"{site_base}/topico-{idx}",
                    }
                )

        if len(link_candidates["external"]) < external_links_target:
            title_query = quote_plus(str(book_data.get("title") or "book review"))
            start = len(link_candidates["external"]) + 1
            for idx in range(start, external_links_target + 1):
                link_candidates["external"].append(
                    {
                        "label": f"External Reference {idx}",
                        "url": f"https://www.google.com/search?q={title_query}+reference+{idx}",
                    }
                )

        kept_items: List[Dict[str, Any]] = []
        for item in toc_items:
            source_lines = self._schema_reference_lines(item=item, book_data=book_data)
            is_optional = bool(item.get("optional"))
            should_keep = True
            if is_optional and not source_lines and not str(item.get("specific_content_hint") or "").strip():
                should_keep = False

            if should_keep:
                kept_items.append({**item, "_source_lines": source_lines})

        if not kept_items:
            fallback_item = toc_items[0]
            kept_items = [
                {
                    **fallback_item,
                    "_source_lines": self._schema_reference_lines(item=fallback_item, book_data=book_data),
                }
            ]

        internal_distribution = self._distribute_counts(internal_links_target, len(kept_items))
        external_distribution = self._distribute_counts(external_links_target, len(kept_items))

        h1_title = str(book_data.get("title") or "Resenha de Livro").strip() or "Resenha de Livro"
        h1 = f"# {h1_title}"
        if len(h1_title) > 60:
            h1 = f"# {h1_title[:57].rstrip()}..."

        article_sections: List[str] = [h1, ""]
        internal_cursor = 0
        external_cursor = 0

        for index, item in enumerate(kept_items):
            level = item.get("level", "h2")
            heading = "##" if level == "h2" else "###"
            section_title = str(item.get("rendered_title") or f"Section {index + 1}")
            min_words, max_words = self._section_word_bounds(item, level)
            min_paragraphs, max_paragraphs = self._section_paragraph_bounds(item, level)
            source_lines = item.get("_source_lines", []) if isinstance(item.get("_source_lines"), list) else []

            prompt_doc = None
            prompt_id = str(item.get("prompt_id") or "").strip()
            if prompt_id:
                prompt_doc = schema_prompts.get(prompt_id)
            if not prompt_doc:
                prompt_doc = default_prompt_doc

            section_body = await self._generate_schema_section(
                book_data=book_data,
                context=context,
                section_item=item,
                source_lines=source_lines,
                prompt_doc=prompt_doc,
                llm_config=llm_config,
                min_words=min_words,
                max_words=max_words,
                min_paragraphs=min_paragraphs,
                max_paragraphs=max_paragraphs,
                internal_links_target=internal_distribution[index],
                external_links_target=external_distribution[index],
            )

            internal_links = link_candidates["internal"][internal_cursor:internal_cursor + internal_distribution[index]]
            external_links = link_candidates["external"][external_cursor:external_cursor + external_distribution[index]]
            internal_cursor += internal_distribution[index]
            external_cursor += external_distribution[index]

            if internal_links or external_links:
                links_lines = ["", "Links recomendados:"]
                if internal_links:
                    internal_parts = [f"[{item_link['label']}]({item_link['url']})" for item_link in internal_links]
                    links_lines.append(f"- Internos: {', '.join(internal_parts)}")
                if external_links:
                    external_parts = [f"[{item_link['label']}]({item_link['url']})" for item_link in external_links]
                    links_lines.append(f"- Externos: {', '.join(external_parts)}")
                section_body = f"{section_body.rstrip()}\n" + "\n".join(links_lines)

            article_sections.append(f"{heading} {section_title}")
            article_sections.append(section_body.strip())
            article_sections.append("")

        article = "\n".join(article_sections).strip() + "\n"

        min_total = content_schema.get("min_total_words")
        max_total = content_schema.get("max_total_words")
        article_word_count = self._word_count(article)

        if isinstance(min_total, int) and min_total > 0 and article_word_count < min_total:
            missing_words = min_total - article_word_count
            extension = self._make_paragraph(
                subject=str(book_data.get("title") or "Resenha de Livro"),
                context=context,
                min_words=missing_words,
                max_words=missing_words + 40,
            )
            article = article.rstrip() + "\n\n" + extension + "\n"

        if isinstance(max_total, int) and max_total > 0 and self._word_count(article) > max_total:
            article_lines = article.splitlines()
            for idx in range(len(article_lines) - 1, -1, -1):
                line = article_lines[idx].strip()
                if line and not line.startswith("#"):
                    article_lines[idx] = self._truncate_to_words(line, max(12, len(line.split()) - 20))
                    candidate = "\n".join(article_lines).strip() + "\n"
                    if self._word_count(candidate) <= max_total:
                        article = candidate
                        break

        return article

    def _build_schema_instruction_block(self, content_schema: Dict[str, Any]) -> str:
        toc_items = self._normalize_schema_toc(content_schema)
        lines = [
            "Restrições do content schema:",
            "- Idioma obrigatório: Português (pt-BR).",
            "- Estilo: analítico, didático, objetivo e aplicável ao dia a dia profissional.",
        ]

        min_total = content_schema.get("min_total_words")
        max_total = content_schema.get("max_total_words")
        if min_total is not None or max_total is not None:
            lines.append(f"- Meta de palavras totais: min={min_total}, max={max_total}")

        internal_links = content_schema.get("internal_links_count")
        external_links = content_schema.get("external_links_count")
        lines.append(f"- Meta de links internos: {internal_links if internal_links is not None else 0}")
        lines.append(f"- Meta de links externos: {external_links if external_links is not None else 0}")

        lines.append("- Template de TOC:")
        for idx, item in enumerate(toc_items, start=1):
            min_words = item.get("min_words")
            max_words = item.get("max_words")
            min_paragraphs = item.get("min_paragraphs")
            max_paragraphs = item.get("max_paragraphs")
            lines.append(
                f"  {idx}. {item.get('level', 'h2').upper()} | "
                f"titulo='{item.get('title_template')}' | "
                f"modo={item.get('content_mode')} | "
                f"min_words={min_words} | max_words={max_words} | "
                f"min_paragraphs={min_paragraphs} | max_paragraphs={max_paragraphs}"
            )
            if item.get("prompt_id"):
                lines.append(f"     prompt_id={item.get('prompt_id')}")
            if item.get("source_fields"):
                lines.append(f"     source_fields={item.get('source_fields')}")
            if item.get("specific_content_hint"):
                lines.append(f"     specific_hint={item.get('specific_content_hint')}")

        return "\n".join(lines)

    def _build_schema_template_article(
        self,
        book_data: Dict[str, Any],
        context: str,
        content_schema: Dict[str, Any],
        topics: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        title = (book_data.get("title") or "Resenha de Livro").strip()
        author = (book_data.get("author") or "Autor desconhecido").strip()
        metadata = book_data.get("metadata", {}) if isinstance(book_data.get("metadata"), dict) else {}

        topic_names = [str(item.get("name") or "").strip() for item in (topics or []) if str(item.get("name") or "").strip()]
        if not topic_names:
            topic_names = [f"Tópico {i}" for i in range(1, 6)]

        subtopic_names: List[str] = []
        for topic in topics or []:
            if not isinstance(topic, dict):
                continue
            for sub in topic.get("subtopics", []) if isinstance(topic.get("subtopics"), list) else []:
                text = str(sub or "").strip()
                if text:
                    subtopic_names.append(text)
        if not subtopic_names:
            subtopic_names = [f"Subtema {i}" for i in range(1, 12)]

        h1 = f"# {title}"
        if len(h1.replace("# ", "")) > 60:
            h1 = f"# {title[:57].rstrip()}..."

        sections: List[str] = [h1, ""]
        toc_items = self._normalize_schema_toc(content_schema)
        if not toc_items:
            return self._build_template_article(book_data, topics or self._fallback_topics(book_data), context)

        for idx, item in enumerate(toc_items, start=1):
            level = item.get("level", "h2")
            heading = "##" if level == "h2" else "###"
            rendered_title = self._render_title_template(
                template=item.get("title_template", ""),
                level=level,
                topic_names=topic_names,
                subtopic_names=subtopic_names,
                fallback_index=idx,
            )

            min_words, max_words = self._section_word_bounds(item, level)
            sections.append(f"{heading} {rendered_title}")
            sections.append(self._make_paragraph(rendered_title, context, min_words=min_words, max_words=max_words))

            source_lines = self._schema_reference_lines(item, book_data)
            if source_lines:
                sections.extend(source_lines)

            if str(item.get("content_mode", "")).lower() == "specific" and item.get("specific_content_hint"):
                sections.append(f"- **Orientação específica**: {item.get('specific_content_hint')}")

            if "detalhes" in rendered_title.lower() or "book details" in rendered_title.lower():
                sections.append(f"- **Título:** {title}")
                sections.append(f"- **Autor:** {author}")
                if metadata.get("isbn_13"):
                    sections.append(f"- **ISBN-13:** {metadata.get('isbn_13')}")
                if metadata.get("publisher"):
                    sections.append(f"- **Editora:** {metadata.get('publisher')}")
                if metadata.get("publication_date"):
                    sections.append(f"- **Data de publicação:** {metadata.get('publication_date')}")
                if metadata.get("asin"):
                    sections.append(f"- **ASIN:** {metadata.get('asin')}")
                if metadata.get("amazon_url"):
                    sections.append(f"- **Amazon:** {metadata.get('amazon_url')}")

            sections.append("")

        return "\n".join(sections).strip() + "\n"

    async def structure_article(
        self,
        book_data: Dict[str, Any],
        topics: List[Dict[str, Any]],
        context: str,
        content_schema: Optional[Dict[str, Any]] = None,
        prompt_doc: Optional[Dict[str, Any]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate article markdown. Uses LLM when available, otherwise template."""
        config = llm_config or {}
        article_prompt = prompt_doc
        if not article_prompt:
            db = await get_database()
            prompts_collection = db["prompts"]
            article_prompt = await prompts_collection.find_one({"purpose": "article", "active": True}, sort=[("updated_at", -1)])
            if not article_prompt:
                article_prompt = await prompts_collection.find_one({"name": "SEO-Optimized Article Writer"})

        if content_schema:
            try:
                schema_article = await self._build_schema_article(
                    book_data=book_data,
                    topics=topics,
                    context=context,
                    content_schema=content_schema,
                    default_prompt_doc=article_prompt,
                    llm_config=config,
                )
                if schema_article.strip():
                    return schema_article
            except Exception:
                pass

        if article_prompt:
            topic1 = topics[0]["name"] if len(topics) > 0 else "Conceitos Principais"
            topic2 = topics[1]["name"] if len(topics) > 1 else "Técnicas-Chave"
            topic3 = topics[2]["name"] if len(topics) > 2 else "Aplicações Práticas"

            user_prompt = article_prompt.get("user_prompt", "")
            user_prompt = user_prompt.replace("{{title}}", book_data.get("title", ""))
            user_prompt = user_prompt.replace("{{author}}", book_data.get("author", ""))
            user_prompt = user_prompt.replace("{{topic1}}", topic1)
            user_prompt = user_prompt.replace("{{topic2}}", topic2)
            user_prompt = user_prompt.replace("{{topic3}}", topic3)
            user_prompt = user_prompt.replace("{{context}}", context or "")
            user_prompt = user_prompt.replace("{{data}}", json.dumps(book_data, ensure_ascii=False, default=str))

            if content_schema:
                user_prompt += "\n\n" + self._build_schema_instruction_block(content_schema)
                user_prompt += "\n\nAplique o content schema estritamente no markdown gerado."

            if book_data.get("summaries"):
                user_prompt += "\n\nAdditional summaries data:\n"
                user_prompt += json.dumps(book_data.get("summaries"), ensure_ascii=False, default=str)

            user_prompt = build_user_prompt_with_output_format(user_prompt, article_prompt)

            model_id = str(config.get("model_id") or article_prompt.get("model_id", BOOK_REVIEW_ARTICLE_MODEL_ID))
            try:
                temperature = float(config.get("temperature") if config.get("temperature") is not None else article_prompt.get("temperature", 0.7))
            except (TypeError, ValueError):
                temperature = 0.7
            try:
                max_tokens = int(config.get("max_tokens") if config.get("max_tokens") is not None else article_prompt.get("max_tokens", 2500))
            except (TypeError, ValueError):
                max_tokens = 2500

            provider = str(config.get("provider") or "").strip().lower() or None
            api_key = str(config.get("api_key") or "").strip() or None
            allow_fallback = bool(config.get("allow_fallback", True))

            try:
                llm_article = await self._llm_generate(
                    system_prompt=article_prompt.get("system_prompt", ""),
                    user_prompt=user_prompt,
                    model_id=model_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    provider=provider,
                    api_key=api_key,
                    allow_fallback=allow_fallback,
                )
                if llm_article.strip():
                    return llm_article
            except Exception:
                pass

        if content_schema:
            return self._build_schema_template_article(
                book_data=book_data,
                context=context,
                content_schema=content_schema,
                topics=topics,
            )

        return self._build_template_article(book_data, topics, context)

    def _make_paragraph(self, subject: str, context: str, min_words: int = 58, max_words: int = 72) -> str:
        seeds = [
            f"{subject} é apresentado de forma prática e estruturada, ajudando o leitor a conectar conceito e execução.",
            "A explicação destaca trade-offs, restrições reais e decisões que surgem em projetos do dia a dia.",
            "Os exemplos são convertidos em orientação objetiva, mantendo profundidade técnica sem perder clareza.",
            "Esta seção também explica por que o tema importa, quais riscos são reduzidos e quais resultados são mensuráveis.",
            "Com isso, o conteúdo aumenta entendimento e apoia decisões de implementação mais consistentes ao longo do tempo.",
        ]

        if context:
            seeds.append(
                f"Com base no contexto disponível, {subject.lower()} é conectado à narrativa do livro com terminologia consistente e foco aplicável."
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
        title = (book_data.get("title") or "Resenha de Livro").strip()
        author = (book_data.get("author") or "Autor desconhecido").strip()

        topic_names = [t.get("name", f"Tópico {idx + 1}") for idx, t in enumerate(topics[:3])]
        while len(topic_names) < 3:
            topic_names.append(f"Tópico {len(topic_names) + 1}")

        topic_subtopics = [
            topics[i].get("subtopics", ["Visão geral", "Métodos", "Aplicação"]) if i < len(topics) else ["Visão geral", "Métodos", "Aplicação"]
            for i in range(3)
        ]

        h1 = f"# {title}"
        if len(h1.replace("# ", "")) > 60:
            h1 = f"# {title[:57].rstrip()}..."

        sections: List[str] = [h1, ""]

        sections.append("## Introdução ao Tema do Livro")
        sections.append(self._make_paragraph("Introdução ao tema do livro", context))
        sections.append("")

        sections.append("## Contexto e Motivação")
        sections.append(self._make_paragraph("Contexto e motivação", context))
        sections.append("")

        sections.append("## Impacto e Aplicabilidade")
        sections.append(self._make_paragraph("Impacto e aplicabilidade", context))
        sections.append("")

        sections.append(f"## {topic_names[0]}")
        sections.append(self._make_paragraph(topic_names[0], context))
        sections.append("")
        for idx, sub in enumerate(topic_subtopics[0][:3]):
            sections.append(f"### {sub or f'Subtema {idx + 1}'}")
            sections.append(self._make_paragraph(f"{topic_names[0]} - {sub}", context))
            sections.append("")

        sections.append(f"## {topic_names[1]}")
        sections.append(self._make_paragraph(topic_names[1], context))
        sections.append("")

        sections.append(f"## {topic_names[2]}")
        sections.append(self._make_paragraph(topic_names[2], context))
        sections.append("")

        sections.append("## Detalhes do Livro")
        sections.append(self._make_paragraph("Detalhes bibliográficos do livro", context, min_words=52, max_words=65))
        sections.append(f"- **Título:** {title}")
        sections.append(f"- **Autor:** {author}")
        sections.append("")

        sections.append("## Sobre o Autor")
        sections.append(self._make_paragraph("Contexto sobre o autor", context, min_words=52, max_words=65))
        sections.append("")

        return "\n".join(sections).strip() + "\n"

    def _extract_heading_sections(self, article_content: str) -> List[Dict[str, Any]]:
        lines = article_content.splitlines()
        headings: List[Dict[str, Any]] = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("### "):
                headings.append({"level": "h3", "title": stripped[4:].strip(), "line": idx})
            elif stripped.startswith("## "):
                headings.append({"level": "h2", "title": stripped[3:].strip(), "line": idx})

        for idx, item in enumerate(headings):
            start = item["line"] + 1
            end = headings[idx + 1]["line"] if idx + 1 < len(headings) else len(lines)
            body = "\n".join(lines[start:end]).strip()
            item["content"] = body
            item["word_count"] = len(body.split()) if body else 0

        return headings

    def _validate_article_with_schema(self, article_content: str, content_schema: Dict[str, Any]) -> Dict[str, Any]:
        detailed_report = {
            "global_rules": [],
            "sections": [],
            "summary": {},
        }

        validation_result = {
            "is_valid": True,
            "errors": [],
            "word_count": len(article_content.split()),
            "section_counts": {},
            "paragraph_stats": {},
            "h2_with_h3_count": 0,
            "schema_sections": [],
            "link_counts": {"total": 0, "internal": 0, "external": 0},
            "detailed_report": detailed_report,
        }

        def add_global_rule(
            rule_id: str,
            passed: bool,
            expected: Any = None,
            actual: Any = None,
            message: Optional[str] = None,
        ) -> None:
            detailed_report["global_rules"].append(
                {
                    "rule_id": rule_id,
                    "passed": bool(passed),
                    "expected": expected,
                    "actual": actual,
                    "message": message,
                }
            )
            if not passed and message:
                validation_result["errors"].append(message)

        lines = article_content.splitlines()
        h1_count = sum(1 for line in lines if line.startswith("# "))
        h2_count = sum(1 for line in lines if line.startswith("## "))
        h3_count = sum(1 for line in lines if line.startswith("### "))
        validation_result["section_counts"] = {"h1": h1_count, "h2": h2_count, "h3": h3_count}

        add_global_rule(
            rule_id="global.h1.exactly_one",
            passed=(h1_count == 1),
            expected=1,
            actual=h1_count,
            message=f"Expected 1 H1 heading, found {h1_count}" if h1_count != 1 else None,
        )

        min_total = content_schema.get("min_total_words")
        max_total = content_schema.get("max_total_words")
        if isinstance(min_total, int) and min_total > 0:
            add_global_rule(
                rule_id="global.total_words.min",
                passed=validation_result["word_count"] >= min_total,
                expected=min_total,
                actual=validation_result["word_count"],
                message=(
                    f"Word count too low: {validation_result['word_count']} (minimum {min_total})"
                    if validation_result["word_count"] < min_total
                    else None
                ),
            )
        if isinstance(max_total, int) and max_total > 0:
            add_global_rule(
                rule_id="global.total_words.max",
                passed=validation_result["word_count"] <= max_total,
                expected=max_total,
                actual=validation_result["word_count"],
                message=(
                    f"Word count too high: {validation_result['word_count']} (maximum {max_total})"
                    if validation_result["word_count"] > max_total
                    else None
                ),
            )

        toc_items = self._normalize_schema_toc(content_schema)
        headings = self._extract_heading_sections(article_content)
        pointer = 0
        required_h2 = 0
        required_h3 = 0
        matched_required_h2 = 0
        matched_required_h3 = 0
        ordered_match_ok = True

        for schema_index, item in enumerate(toc_items):
            expected_level = item.get("level", "h2")
            is_optional = self._is_optional_toc_item(item)
            if not is_optional:
                if expected_level == "h2":
                    required_h2 += 1
                elif expected_level == "h3":
                    required_h3 += 1

            section_report = {
                "schema_index": schema_index,
                "level": expected_level,
                "title_template": item.get("title_template"),
                "optional": is_optional,
                "matched": False,
                "actual_title": None,
                "actual_heading_index": None,
                "rules": [],
            }

            def add_section_rule(
                rule_id: str,
                passed: bool,
                expected: Any = None,
                actual: Any = None,
                message: Optional[str] = None,
            ) -> None:
                section_report["rules"].append(
                    {
                        "rule_id": rule_id,
                        "passed": bool(passed),
                        "expected": expected,
                        "actual": actual,
                        "message": message,
                    }
                )
                if not passed and message:
                    validation_result["errors"].append(message)

            title_pattern = self._build_title_pattern(item.get("title_template", ""))
            matched_idx = None
            for idx in range(pointer, len(headings)):
                candidate = headings[idx]
                if candidate.get("level") != expected_level:
                    continue
                if title_pattern.match(str(candidate.get("title") or "").strip()):
                    matched_idx = idx
                    break

            if matched_idx is None:
                add_section_rule(
                    rule_id="section.presence",
                    passed=is_optional,
                    expected="present" if not is_optional else "present_or_missing",
                    actual="missing",
                    message=(
                        f"Missing required {expected_level.upper()} section matching template '{item.get('title_template')}'"
                        if not is_optional
                        else None
                    ),
                )
                validation_result["schema_sections"].append(
                    {
                        "level": expected_level,
                        "title_template": item.get("title_template"),
                        "matched": False,
                        "optional": is_optional,
                        "rules": section_report["rules"],
                    }
                )
                detailed_report["sections"].append(section_report)
                continue

            matched = headings[matched_idx]
            if matched_idx < pointer:
                ordered_match_ok = False
            pointer = matched_idx + 1
            section_report["matched"] = True
            section_report["actual_title"] = matched.get("title")
            section_report["actual_heading_index"] = matched_idx

            if not is_optional:
                if expected_level == "h2":
                    matched_required_h2 += 1
                elif expected_level == "h3":
                    matched_required_h3 += 1

            add_section_rule(
                rule_id="section.presence",
                passed=True,
                expected="present",
                actual="present",
                message=None,
            )
            add_section_rule(
                rule_id="section.level",
                passed=str(matched.get("level")) == expected_level,
                expected=expected_level,
                actual=str(matched.get("level")),
                message=(
                    f"Section '{matched.get('title')}' has level {matched.get('level')}; expected {expected_level}"
                    if str(matched.get("level")) != expected_level
                    else None
                ),
            )
            add_section_rule(
                rule_id="section.title_template_match",
                passed=bool(title_pattern.match(str(matched.get("title") or "").strip())),
                expected=str(item.get("title_template") or ""),
                actual=str(matched.get("title") or ""),
                message=(
                    f"Section title '{matched.get('title')}' does not match template '{item.get('title_template')}'"
                    if not title_pattern.match(str(matched.get("title") or "").strip())
                    else None
                ),
            )

            section_record = {
                "level": expected_level,
                "title_template": item.get("title_template"),
                "title": matched.get("title"),
                "matched": True,
                "optional": is_optional,
                "word_count": 0,
                "paragraph_count": 0,
                "rules": section_report["rules"],
            }

            matched_content = str(matched.get("content") or "")
            matched_content_lines = [line for line in matched_content.splitlines()]
            constraint_content_lines: List[str] = []
            for line in matched_content_lines:
                lowered_line = line.strip().lower()
                if lowered_line.startswith("links recomendados:"):
                    continue
                if lowered_line.startswith("- internos:"):
                    continue
                if lowered_line.startswith("- externos:"):
                    continue
                constraint_content_lines.append(line)
            constraint_content = "\n".join(constraint_content_lines).strip()
            section_word_count = self._word_count(constraint_content)
            section_record["word_count"] = section_word_count

            min_words = item.get("min_words")
            if isinstance(min_words, int) and min_words > 0 and section_word_count < min_words:
                add_section_rule(
                    rule_id="section.words.min",
                    passed=False,
                    expected=min_words,
                    actual=section_word_count,
                    message=f"Section '{matched.get('title')}' has {section_word_count} words; expected at least {min_words}",
                )
            elif isinstance(min_words, int) and min_words > 0:
                add_section_rule(
                    rule_id="section.words.min",
                    passed=True,
                    expected=min_words,
                    actual=section_word_count,
                    message=None,
                )

            max_words = item.get("max_words")
            if isinstance(max_words, int) and max_words > 0 and section_word_count > max_words:
                add_section_rule(
                    rule_id="section.words.max",
                    passed=False,
                    expected=max_words,
                    actual=section_word_count,
                    message=f"Section '{matched.get('title')}' has {section_word_count} words; expected at most {max_words}",
                )
            elif isinstance(max_words, int) and max_words > 0:
                add_section_rule(
                    rule_id="section.words.max",
                    passed=True,
                    expected=max_words,
                    actual=section_word_count,
                    message=None,
                )

            section_paragraphs = self._split_paragraphs(constraint_content)
            section_record["paragraph_count"] = len(section_paragraphs)
            min_paragraphs = item.get("min_paragraphs")
            if isinstance(min_paragraphs, int) and min_paragraphs > 0 and len(section_paragraphs) < min_paragraphs:
                add_section_rule(
                    rule_id="section.paragraphs.min",
                    passed=False,
                    expected=min_paragraphs,
                    actual=len(section_paragraphs),
                    message=f"Section '{matched.get('title')}' has {len(section_paragraphs)} paragraphs; expected at least {min_paragraphs}",
                )
            elif isinstance(min_paragraphs, int) and min_paragraphs > 0:
                add_section_rule(
                    rule_id="section.paragraphs.min",
                    passed=True,
                    expected=min_paragraphs,
                    actual=len(section_paragraphs),
                    message=None,
                )

            max_paragraphs = item.get("max_paragraphs")
            if isinstance(max_paragraphs, int) and max_paragraphs > 0 and len(section_paragraphs) > max_paragraphs:
                add_section_rule(
                    rule_id="section.paragraphs.max",
                    passed=False,
                    expected=max_paragraphs,
                    actual=len(section_paragraphs),
                    message=f"Section '{matched.get('title')}' has {len(section_paragraphs)} paragraphs; expected at most {max_paragraphs}",
                )
            elif isinstance(max_paragraphs, int) and max_paragraphs > 0:
                add_section_rule(
                    rule_id="section.paragraphs.max",
                    passed=True,
                    expected=max_paragraphs,
                    actual=len(section_paragraphs),
                    message=None,
                )

            validation_result["schema_sections"].append(section_record)
            detailed_report["sections"].append(section_report)

        add_global_rule(
            rule_id="global.toc.required_h2_count",
            passed=(matched_required_h2 >= required_h2),
            expected=required_h2,
            actual=matched_required_h2,
            message=(
                f"Expected {required_h2} required H2 sections, found {matched_required_h2}"
                if matched_required_h2 < required_h2
                else None
            ),
        )
        add_global_rule(
            rule_id="global.toc.required_h3_count",
            passed=(matched_required_h3 >= required_h3),
            expected=required_h3,
            actual=matched_required_h3,
            message=(
                f"Expected {required_h3} required H3 sections, found {matched_required_h3}"
                if matched_required_h3 < required_h3
                else None
            ),
        )
        add_global_rule(
            rule_id="global.toc.order",
            passed=ordered_match_ok,
            expected="schema order preserved",
            actual="schema order violated" if not ordered_match_ok else "schema order preserved",
            message="TOC order mismatch detected against schema." if not ordered_match_ok else None,
        )

        raw_blocks = [block.strip() for block in re.split(r"\n\s*\n", article_content) if block.strip()]
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

        h2_with_h3 = 0
        current_h2 = None
        h3_in_current = 0
        for line in lines:
            if line.startswith("## "):
                if current_h2 and h3_in_current > 0:
                    h2_with_h3 += 1
                current_h2 = line
                h3_in_current = 0
            elif line.startswith("### "):
                h3_in_current += 1
        if current_h2 and h3_in_current > 0:
            h2_with_h3 += 1
        validation_result["h2_with_h3_count"] = h2_with_h3

        labeled_internal_links: List[str] = []
        labeled_external_links: List[str] = []
        for line in lines:
            stripped = line.strip()
            lowered = stripped.lower()
            if lowered.startswith("- internos:"):
                labeled_internal_links.extend(self._extract_markdown_links(stripped))
            elif lowered.startswith("- externos:"):
                labeled_external_links.extend(self._extract_markdown_links(stripped))

        if labeled_internal_links or labeled_external_links:
            internal_links = labeled_internal_links
            external_links = labeled_external_links
            links = internal_links + external_links
        else:
            links = self._extract_markdown_links(article_content)
            internal_domains = ["analisederequisitos.com.br"]
            internal_links = [url for url in links if self._is_internal_url(url, internal_domains)]
            external_links = [url for url in links if url not in internal_links]

        validation_result["link_counts"] = {
            "total": len(links),
            "internal": len(internal_links),
            "external": len(external_links),
        }

        expected_internal = self._to_non_negative_int(content_schema.get("internal_links_count"), 0)
        expected_external = self._to_non_negative_int(content_schema.get("external_links_count"), 0)

        add_global_rule(
            rule_id="global.links.internal_count",
            passed=(len(internal_links) == expected_internal),
            expected=expected_internal,
            actual=len(internal_links),
            message=(
                f"Internal links count mismatch: found {len(internal_links)}, expected {expected_internal}"
                if len(internal_links) != expected_internal
                else None
            ),
        )
        add_global_rule(
            rule_id="global.links.external_count",
            passed=(len(external_links) == expected_external),
            expected=expected_external,
            actual=len(external_links),
            message=(
                f"External links count mismatch: found {len(external_links)}, expected {expected_external}"
                if len(external_links) != expected_external
                else None
            ),
        )

        detailed_report["summary"] = {
            "global_rules_total": len(detailed_report["global_rules"]),
            "global_rules_passed": len([rule for rule in detailed_report["global_rules"] if rule.get("passed")]),
            "sections_total": len(detailed_report["sections"]),
            "sections_matched": len([section for section in detailed_report["sections"] if section.get("matched")]),
            "section_rules_total": sum(len(section.get("rules", [])) for section in detailed_report["sections"]),
            "section_rules_passed": sum(
                len([rule for rule in section.get("rules", []) if rule.get("passed")])
                for section in detailed_report["sections"]
            ),
            "errors_total": len(validation_result["errors"]),
        }

        validation_result["is_valid"] = len(validation_result["errors"]) == 0
        return validation_result

    async def validate_article(
        self,
        article_content: str,
        strict: bool = False,
        content_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if content_schema:
            return self._validate_article_with_schema(article_content, content_schema)

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

    async def generate_valid_article(
        self,
        book_data: Dict[str, Any],
        context: str,
        max_retries: int = 3,
        content_schema: Optional[Dict[str, Any]] = None,
        prompt_doc: Optional[Dict[str, Any]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate and validate article with retries."""
        for attempt in range(max_retries):
            topics = await self.extract_topics(book_data, llm_config=llm_config)
            article_content = await self.structure_article(
                book_data=book_data,
                topics=topics,
                context=context,
                content_schema=content_schema,
                prompt_doc=prompt_doc,
                llm_config=llm_config,
            )
            validation = await self.validate_article(
                article_content,
                strict=True,
                content_schema=content_schema,
            )

            if validation["is_valid"]:
                return article_content

        raise ValueError(f"Failed to generate valid article after {max_retries} attempts")
