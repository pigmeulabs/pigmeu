"""Celery task definitions for scraping and context pipeline."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Iterable

from celery import shared_task, Task

from src.db.connection import get_db
from src.db.repositories import (
    SubmissionRepository,
    BookRepository,
    KnowledgeBaseRepository,
    SummaryRepository,
    PromptRepository,
    CredentialRepository,
    PipelineConfigRepository,
)
from src.models.enums import SubmissionStatus
from src.scrapers.amazon import AmazonScraper
from src.scrapers.link_finder import LinkFinder
from src.workers.llm_client import LLMClient
from src.workers.prompt_builder import build_user_prompt_with_output_format

logger = logging.getLogger(__name__)
BOOK_REVIEW_PIPELINE_ID = "book_review_v2"

LINK_BIBLIO_PROMPT = {
    "name": "Book Review - Additional Link Bibliographic Extractor",
    "purpose": "book_review_link_bibliography_extract",
    "short_description": "Extrai metadados bibliograficos de conteudo de links adicionais.",
    "model_id": "mistral-large-latest",
    "temperature": 0.1,
    "max_tokens": 900,
    "system_prompt": (
        "You are a bibliographic extraction engine optimized for API usage. "
        "Extract only factual information about a book and its author from the provided text. "
        "Do not invent data. Respond in Portuguese (pt-BR). "
        "Return strict JSON only."
    ),
    "user_prompt": (
        "Task: extract bibliographic metadata from the source content.\n"
        "Book title (reference): {{title}}\n"
        "Author (reference): {{author}}\n\n"
        "Source content:\n{{content}}\n\n"
        "Rules:\n"
        "- Use only information present in the source.\n"
        "- Keep numeric values as numbers when possible.\n"
        "- If a field is unknown, use null.\n"
        "- Respond in Portuguese (pt-BR), except URLs/identifiers.\n"
        "- Return only the JSON object."
    ),
    "expected_output_format": (
        "{\n"
        '  "title": "string|null",\n'
        '  "title_original": "string|null",\n'
        '  "authors": ["string"],\n'
        '  "language": "string|null",\n'
        '  "original_language": "string|null",\n'
        '  "edition": "string|null",\n'
        '  "average_rating": "number|null",\n'
        '  "pages": "number|null",\n'
        '  "publisher": "string|null",\n'
        '  "publication_date": "string|null",\n'
        '  "asin": "string|null",\n'
        '  "isbn_10": "string|null",\n'
        '  "isbn_13": "string|null",\n'
        '  "price_book": "number|string|null",\n'
        '  "price_ebook": "number|string|null",\n'
        '  "cover_image_url": "string|null"\n'
        "}"
    ),
    "schema_example": (
        "{\n"
        '  "title": "Scrum e Kanban",\n'
        '  "title_original": "Scrum and Kanban",\n'
        '  "authors": ["Chico Alff"],\n'
        '  "language": "Português",\n'
        '  "original_language": "Inglês",\n'
        '  "edition": "2ª edição",\n'
        '  "average_rating": 4.6,\n'
        '  "pages": 312,\n'
        '  "publisher": "Editora Exemplo",\n'
        '  "publication_date": "2024-06-18",\n'
        '  "asin": "B0ABC12345",\n'
        '  "isbn_10": "1234567890",\n'
        '  "isbn_13": "9781234567897",\n'
        '  "price_book": 89.9,\n'
        '  "price_ebook": 39.9,\n'
        '  "cover_image_url": "https://exemplo.com/capa.jpg"\n'
        "}"
    ),
}

LINK_SUMMARY_PROMPT = {
    "name": "Book Review - Additional Link Summary",
    "purpose": "book_review_link_summary",
    "short_description": "Resume links adicionais com foco em livro e autor.",
    "model_id": "llama-3.3-70b-versatile",
    "temperature": 0.3,
    "max_tokens": 900,
    "system_prompt": (
        "You summarize web content for editorial book research. "
        "Focus strictly on insights about the book and author. "
        "Respond in Portuguese (pt-BR). Return strict JSON only."
    ),
    "user_prompt": (
        "Task: produce a concise summary from this source.\n"
        "Book title: {{title}}\n"
        "Author: {{author}}\n"
        "Source URL: {{url}}\n\n"
        "Source content:\n{{content}}\n\n"
        "Rules:\n"
        "- Focus only on relevant information about the book and author.\n"
        "- Keep summary objective and factual.\n"
        "- Respond in Portuguese (pt-BR).\n"
        "- Return only the JSON object."
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
        '  "summary": "O conteúdo destaca os principais conceitos do livro e relaciona os argumentos com a trajetória do autor.",\n'
        '  "topics": ["gestão ágil", "kanban", "melhoria contínua"],\n'
        '  "key_points": ["Explica fundamentos práticos", "Compara abordagens", "Apresenta exemplos reais"],\n'
        '  "credibility": "media"\n'
        "}"
    ),
}

WEB_RESEARCH_PROMPT = {
    "name": "Book Review - Web Research",
    "purpose": "book_review_web_research",
    "short_description": "Pesquisa web sobre temas e contexto do livro/autor.",
    "model_id": "llama-3.3-70b-versatile",
    "temperature": 0.25,
    "max_tokens": 1100,
    "system_prompt": (
        "You are a literary research analyst. "
        "Synthesize topics, themes, and context about the book and author from web source excerpts. "
        "Respond in Portuguese (pt-BR). Return strict JSON only."
    ),
    "user_prompt": (
        "Task: consolidate web research notes.\n"
        "Book title: {{title}}\n"
        "Author: {{author}}\n\n"
        "Sources:\n{{sources}}\n\n"
        "Rules:\n"
        "- Prioritize themes, contexts, and discussion points useful for editorial analysis.\n"
        "- Keep statements grounded in provided sources.\n"
        "- Respond in Portuguese (pt-BR).\n"
        "- Return only the JSON object."
    ),
    "expected_output_format": (
        "{\n"
        '  "research_markdown": "string (markdown)",\n'
        '  "topics": ["string"],\n'
        '  "key_insights": ["string"]\n'
        "}"
    ),
    "schema_example": (
        "{\n"
        '  "research_markdown": "## Pesquisa Web\\n\\n### Temas recorrentes\\n- Tema 1\\n- Tema 2",\n'
        '  "topics": ["tema 1", "tema 2", "tema 3"],\n'
        '  "key_insights": ["Insight objetivo 1", "Insight objetivo 2"]\n'
        "}"
    ),
}


class ScraperTask(Task):
    """Base Celery task class with retry behavior."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


async def _get_step_delay_seconds(step_id: str) -> int:
    """Resolve configured delay (in seconds) for a pipeline step."""
    try:
        db = await get_db()
        pipeline_repo = PipelineConfigRepository(db)
        pipeline_doc = await pipeline_repo.get_by_pipeline_id(BOOK_REVIEW_PIPELINE_ID)
        if not pipeline_doc:
            return 0

        raw_steps = pipeline_doc.get("steps", []) if isinstance(pipeline_doc.get("steps"), list) else []
        step_doc = next((item for item in raw_steps if item.get("id") == step_id), None)
        if not step_doc:
            return 0

        raw_delay = step_doc.get("delay_seconds", 0)
        delay_seconds = int(raw_delay or 0)
        return max(0, delay_seconds)
    except Exception as exc:
        logger.warning("Failed to resolve pipeline step delay for '%s': %s", step_id, exc)
        return 0


def _enqueue_task(task_callable, delay_seconds: int, **kwargs) -> None:
    """Queue a celery task optionally using countdown delay."""
    safe_delay = max(0, int(delay_seconds or 0))
    if safe_delay > 0:
        task_callable.apply_async(kwargs=kwargs, countdown=safe_delay)
        return
    task_callable.delay(**kwargs)


def _dedupe_list(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(text)
    return result


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _safe_json_parse(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}

    cleaned = _strip_markdown_fences(raw)
    for candidate in (cleaned,):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and start < end:
        snippet = cleaned[start : end + 1]
        try:
            parsed = json.loads(snippet)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    return {}


def _normalize_bibliographic_candidate(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    def pick(*keys: str) -> Optional[Any]:
        for key in keys:
            value = data.get(key)
            if value is not None and str(value).strip() != "":
                return value
        return None

    authors_raw = pick("authors", "author", "book_authors") or []
    if isinstance(authors_raw, str):
        authors = [item.strip() for item in re.split(r",|;| and ", authors_raw) if item.strip()]
    elif isinstance(authors_raw, list):
        authors = [str(item).strip() for item in authors_raw if str(item).strip()]
    else:
        authors = []

    normalized = {
        "title": pick("title"),
        "title_original": pick("title_original", "original_title"),
        "authors": _dedupe_list(authors),
        "language": pick("language"),
        "original_language": pick("original_language", "language_original"),
        "edition": pick("edition"),
        "average_rating": pick("average_rating", "rating"),
        "pages": pick("pages", "page_count"),
        "publisher": pick("publisher"),
        "publication_date": pick("publication_date", "published_at"),
        "asin": pick("asin"),
        "isbn_10": pick("isbn_10"),
        "isbn_13": pick("isbn_13", "isbn"),
        "price_book": pick("price_book", "book_price", "price"),
        "price_ebook": pick("price_ebook", "ebook_price"),
        "cover_image_url": pick("cover_image_url", "cover_url", "image_url"),
    }
    return {key: value for key, value in normalized.items() if value not in (None, "", [])}


def _extract_topics(summary: str, limit: int = 8) -> List[str]:
    words = [w.strip(".,:;!?()[]{}\"'") for w in summary.split()]
    words = [w for w in words if len(w) > 4 and w.isalpha()]
    freq: Dict[str, int] = {}
    for word in words:
        key = word.lower()
        freq[key] = freq.get(key, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)
    return [word for word, _ in ranked[:limit]]


def _normalize_amazon_for_consolidation(extracted: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(extracted, dict):
        return {}

    authors = extracted.get("authors") or []
    if isinstance(authors, str):
        authors = [authors]

    normalized = {
        "title": extracted.get("title"),
        "authors": _dedupe_list([str(item) for item in authors]),
        "language": extracted.get("language"),
        "average_rating": extracted.get("rating") or extracted.get("amazon_rating"),
        "pages": extracted.get("pages"),
        "publisher": extracted.get("publisher"),
        "publication_date": extracted.get("publication_date") or extracted.get("pub_date"),
        "asin": extracted.get("asin"),
        "isbn_13": extracted.get("isbn"),
        "price_book": extracted.get("price") or extracted.get("price_physical"),
        "price_ebook": extracted.get("price_ebook"),
        "theme": extracted.get("theme"),
        "cover_image_url": extracted.get("cover_image_url"),
    }
    return {key: value for key, value in normalized.items() if value not in (None, "", [])}


def _consolidate_bibliographic(amazon_data: Dict[str, Any], link_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    consolidated = _normalize_amazon_for_consolidation(amazon_data)
    consolidated.setdefault("authors", [])

    scalar_fields = [
        "title",
        "title_original",
        "language",
        "original_language",
        "edition",
        "average_rating",
        "pages",
        "publisher",
        "publication_date",
        "asin",
        "isbn_10",
        "isbn_13",
        "price_book",
        "price_ebook",
        "cover_image_url",
        "theme",
    ]

    for candidate in link_candidates:
        normalized = _normalize_bibliographic_candidate(candidate)
        if not normalized:
            continue

        consolidated["authors"] = _dedupe_list(consolidated.get("authors", []) + normalized.get("authors", []))
        for field in scalar_fields:
            if not consolidated.get(field) and normalized.get(field):
                consolidated[field] = normalized[field]

    consolidated["consolidated_at"] = datetime.utcnow().isoformat()
    consolidated["sources_count"] = len(link_candidates)
    return consolidated


async def _ensure_prompt(prompt_repo: PromptRepository, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    existing = await prompt_repo.get_by_name(prompt_data["name"])
    payload = {
        "name": prompt_data["name"],
        "purpose": prompt_data["purpose"],
        "short_description": prompt_data["short_description"],
        "system_prompt": prompt_data["system_prompt"],
        "user_prompt": prompt_data["user_prompt"],
        "expected_output_format": prompt_data.get("expected_output_format") or prompt_data.get("schema_example"),
        "model_id": prompt_data["model_id"],
        "temperature": prompt_data["temperature"],
        "max_tokens": prompt_data["max_tokens"],
        "active": True,
    }

    if existing:
        # Preserve user-managed prompts; do not overwrite defaults automatically.
        return existing

    prompt_id = await prompt_repo.create(payload)
    created = await prompt_repo.get_by_id(prompt_id)
    return created or payload


async def _resolve_credential_key(
    credential_repo: CredentialRepository,
    preferred_name: str,
    service: str,
) -> Optional[str]:
    credential = await credential_repo.get_active_by_name(preferred_name, service=service)
    if not credential:
        credential = await credential_repo.get_active(service=service)
        if credential:
            logger.warning(
                "Preferred credential '%s' not found for service '%s'. Falling back to '%s'.",
                preferred_name,
                service,
                credential.get("name"),
            )

    if not credential or not credential.get("key"):
        return None

    await credential_repo.touch_last_used(credential.get("_id"))
    return str(credential.get("key"))


async def _run_link_bibliographic_extraction(
    llm: LLMClient,
    prompt_doc: Dict[str, Any],
    content: str,
    title: str,
    author: str,
    api_key: Optional[str],
) -> Dict[str, Any]:
    if not content.strip():
        return {}

    if not api_key:
        return {}

    user_prompt = str(prompt_doc.get("user_prompt", ""))
    user_prompt = user_prompt.replace("{{title}}", str(title or ""))
    user_prompt = user_prompt.replace("{{author}}", str(author or ""))
    user_prompt = user_prompt.replace("{{content}}", content[:4500])
    user_prompt = build_user_prompt_with_output_format(user_prompt, prompt_doc)

    response = await llm.generate_with_retry(
        system_prompt=str(prompt_doc.get("system_prompt", "")),
        user_prompt=user_prompt,
        model_id=str(prompt_doc.get("model_id", "mistral-large-latest")),
        temperature=float(prompt_doc.get("temperature", 0.1)),
        max_tokens=int(prompt_doc.get("max_tokens", 900)),
        provider="mistral",
        api_key=api_key,
        allow_fallback=False,
    )
    return _normalize_bibliographic_candidate(_safe_json_parse(response))


async def _run_link_summary(
    llm: LLMClient,
    prompt_doc: Dict[str, Any],
    content: str,
    title: str,
    author: str,
    url: str,
    api_key: Optional[str],
) -> Dict[str, Any]:
    if not content.strip():
        return {
            "summary": "No relevant textual content extracted.",
            "topics": [],
            "key_points": [],
            "credibility": "low",
        }

    if api_key:
        user_prompt = str(prompt_doc.get("user_prompt", ""))
        user_prompt = user_prompt.replace("{{title}}", str(title or ""))
        user_prompt = user_prompt.replace("{{author}}", str(author or ""))
        user_prompt = user_prompt.replace("{{url}}", str(url or ""))
        user_prompt = user_prompt.replace("{{content}}", content[:4500])
        user_prompt = build_user_prompt_with_output_format(user_prompt, prompt_doc)

        response = await llm.generate_with_retry(
            system_prompt=str(prompt_doc.get("system_prompt", "")),
            user_prompt=user_prompt,
            model_id=str(prompt_doc.get("model_id", "llama-3.3-70b-versatile")),
            temperature=float(prompt_doc.get("temperature", 0.3)),
            max_tokens=int(prompt_doc.get("max_tokens", 900)),
            provider="groq",
            api_key=api_key,
            allow_fallback=False,
        )
        parsed = _safe_json_parse(response)
        summary_text = str(parsed.get("summary") or "").strip()
        topics = parsed.get("topics") if isinstance(parsed.get("topics"), list) else []
        key_points = parsed.get("key_points") if isinstance(parsed.get("key_points"), list) else []
        credibility = str(parsed.get("credibility") or "medium")
        if summary_text:
            return {
                "summary": summary_text,
                "topics": _dedupe_list([str(item) for item in topics]),
                "key_points": _dedupe_list([str(item) for item in key_points]),
                "credibility": credibility,
            }

    fallback_summary = content[:700]
    return {
        "summary": fallback_summary,
        "topics": _extract_topics(fallback_summary),
        "key_points": [],
        "credibility": "low" if not api_key else "medium",
    }


async def _run_web_research(
    llm: LLMClient,
    prompt_doc: Dict[str, Any],
    title: str,
    author: str,
    source_blobs: List[Dict[str, Any]],
    api_key: Optional[str],
) -> Dict[str, Any]:
    sources_text_lines = []
    for item in source_blobs:
        sources_text_lines.append(f"- URL: {item.get('url')}")
        if item.get("title"):
            sources_text_lines.append(f"  Titulo: {item.get('title')}")
        if item.get("snippet"):
            sources_text_lines.append(f"  Snippet: {item.get('snippet')}")
        if item.get("content_excerpt"):
            sources_text_lines.append(f"  Conteudo: {item.get('content_excerpt')}")
    sources_text = "\n".join(sources_text_lines).strip()

    if api_key and sources_text:
        user_prompt = str(prompt_doc.get("user_prompt", ""))
        user_prompt = user_prompt.replace("{{title}}", str(title or ""))
        user_prompt = user_prompt.replace("{{author}}", str(author or ""))
        user_prompt = user_prompt.replace("{{sources}}", sources_text[:16000])
        user_prompt = build_user_prompt_with_output_format(user_prompt, prompt_doc)

        response = await llm.generate_with_retry(
            system_prompt=str(prompt_doc.get("system_prompt", "")),
            user_prompt=user_prompt,
            model_id=str(prompt_doc.get("model_id", "llama-3.3-70b-versatile")),
            temperature=float(prompt_doc.get("temperature", 0.25)),
            max_tokens=int(prompt_doc.get("max_tokens", 1100)),
            provider="groq",
            api_key=api_key,
            allow_fallback=False,
        )

        parsed = _safe_json_parse(response)
        markdown = str(parsed.get("research_markdown") or "").strip()
        topics = parsed.get("topics") if isinstance(parsed.get("topics"), list) else []
        key_insights = parsed.get("key_insights") if isinstance(parsed.get("key_insights"), list) else []
        if markdown:
            return {
                "research_markdown": markdown,
                "topics": _dedupe_list([str(item) for item in topics]),
                "key_insights": _dedupe_list([str(item) for item in key_insights]),
            }

    topic_seed = []
    for item in source_blobs:
        topic_seed.extend(_extract_topics(str(item.get("snippet") or "")))
    dedup_topics = _dedupe_list(topic_seed)[:12]
    fallback_lines = [
        f"## Web Research - {title}",
        "",
        f"Author: {author}",
        "",
        "### Key Topics",
    ]
    for topic in dedup_topics:
        fallback_lines.append(f"- {topic}")
    if not dedup_topics:
        fallback_lines.append("- No clear topic extracted from sources.")

    return {
        "research_markdown": "\n".join(fallback_lines),
        "topics": dedup_topics,
        "key_insights": [],
    }


@shared_task(base=ScraperTask, bind=True)
def scrape_amazon_task(self, submission_id: str, amazon_url: str) -> Dict[str, Any]:
    """Scrape Amazon metadata and persist into books collection."""

    async def _run() -> Dict[str, Any]:
        db = await get_db()
        submission_repo = SubmissionRepository(db)
        book_repo = BookRepository(db)

        submission = await submission_repo.get_by_id(submission_id)
        if not submission:
            return {"status": "error", "error": "submission_not_found"}

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.SCRAPING_AMAZON,
            {
                "current_step": "amazon_scrape",
                "started_at": datetime.utcnow(),
                "pipeline_version": "book_review_v2",
            },
        )

        extracted: Dict[str, Any]
        scraper = AmazonScraper()
        try:
            await scraper.initialize()
            extracted = await scraper.scrape(amazon_url) or {}
        except Exception as exc:
            logger.warning("Amazon scrape failed for %s: %s", submission_id, exc)
            extracted = {}
        finally:
            try:
                await scraper.cleanup()
            except Exception:
                pass

        if not extracted or not extracted.get("title"):
            message = "Failed to extract Amazon product data. Check amazon_url validity or access restrictions."
            await submission_repo.update_status(
                submission_id,
                SubmissionStatus.SCRAPING_FAILED,
                {
                    "current_step": "amazon_scrape",
                    "errors": [message],
                    "pipeline_version": "book_review_v2",
                },
            )
            return {"status": "error", "error": "amazon_scrape_failed", "message": message}

        book_id = await book_repo.create_or_update(submission_id=submission_id, extracted=extracted)
        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.PENDING_CONTEXT,
            {
                "current_step": "additional_links_processing",
                "book_id": book_id,
                "pipeline_version": "book_review_v2",
            },
        )

        next_delay = await _get_step_delay_seconds("amazon_scrape")
        _enqueue_task(process_additional_links_task, next_delay, submission_id=submission_id)
        return {"status": "ok", "book_id": book_id}

    return asyncio.run(_run())


@shared_task(base=ScraperTask, bind=True)
def process_additional_links_task(self, submission_id: str) -> Dict[str, Any]:
    """Process additional links: bibliographic extraction (Mistral) + summary (Groq) for each link."""

    async def _run() -> Dict[str, Any]:
        db = await get_db()
        submission_repo = SubmissionRepository(db)
        book_repo = BookRepository(db)
        summary_repo = SummaryRepository(db)
        prompt_repo = PromptRepository(db)
        credential_repo = CredentialRepository(db)

        submission = await submission_repo.get_by_id(submission_id)
        if not submission:
            return {"status": "error", "error": "submission_not_found"}

        book = await book_repo.get_by_submission(submission_id)
        if not book:
            return {"status": "error", "error": "book_not_found"}

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.PENDING_CONTEXT,
            {
                "current_step": "additional_links_processing",
                "started_at": datetime.utcnow(),
            },
        )

        bibliographic_prompt = await _ensure_prompt(prompt_repo, LINK_BIBLIO_PROMPT)
        summary_prompt = await _ensure_prompt(prompt_repo, LINK_SUMMARY_PROMPT)

        mistral_api_key = await _resolve_credential_key(credential_repo, preferred_name="Mistral A", service="mistral")
        groq_api_key = await _resolve_credential_key(credential_repo, preferred_name="GROC A", service="groq")

        links = _dedupe_list(submission.get("other_links", []))
        if not links:
            await submission_repo.update_status(
                submission_id,
                SubmissionStatus.PENDING_CONTEXT,
                {
                    "current_step": "bibliographic_consolidation",
                    "links_total": 0,
                    "links_processed": 0,
                },
            )
            next_delay = await _get_step_delay_seconds("summarize_additional_links")
            _enqueue_task(consolidate_bibliographic_task, next_delay, submission_id=submission_id)
            return {"status": "ok", "links_total": 0, "links_processed": 0}

        finder = LinkFinder()
        llm = LLMClient()
        processed = 0
        link_candidates: List[Dict[str, Any]] = []

        for url in links:
            try:
                content = await finder.fetch_and_parse(url)
                bibliographic_data = await _run_link_bibliographic_extraction(
                    llm=llm,
                    prompt_doc=bibliographic_prompt,
                    content=content,
                    title=str(submission.get("title") or ""),
                    author=str(submission.get("author_name") or ""),
                    api_key=mistral_api_key,
                )

                summary_data = await _run_link_summary(
                    llm=llm,
                    prompt_doc=summary_prompt,
                    content=content,
                    title=str(submission.get("title") or ""),
                    author=str(submission.get("author_name") or ""),
                    url=url,
                    api_key=groq_api_key,
                )

                await summary_repo.create(
                    book_id=str(book.get("_id")),
                    source_url=url,
                    source_domain=finder.get_domain(url),
                    summary_text=summary_data.get("summary", ""),
                    topics=summary_data.get("topics", []),
                    key_points=summary_data.get("key_points", []),
                    credibility=summary_data.get("credibility"),
                    extra_fields={
                        "pipeline_stage": "additional_link_processing",
                        "bibliographic_data": bibliographic_data,
                        "content_excerpt": content[:1200],
                    },
                )
                if bibliographic_data:
                    link_candidates.append(bibliographic_data)
                processed += 1
            except Exception as exc:
                logger.warning("Failed to process additional link '%s' for %s: %s", url, submission_id, exc)

        await book_repo.create_or_update(
            submission_id=submission_id,
            extracted={
                "link_bibliographic_candidates": link_candidates,
                "additional_links_total": len(links),
                "additional_links_processed": processed,
                "additional_links_processed_at": datetime.utcnow(),
            },
        )

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.PENDING_CONTEXT,
            {
                "current_step": "bibliographic_consolidation",
                "links_total": len(links),
                "links_processed": processed,
            },
        )

        next_delay = await _get_step_delay_seconds("summarize_additional_links")
        _enqueue_task(consolidate_bibliographic_task, next_delay, submission_id=submission_id)
        return {"status": "ok", "links_total": len(links), "links_processed": processed}

    return asyncio.run(_run())


@shared_task(base=ScraperTask, bind=True)
def consolidate_bibliographic_task(self, submission_id: str) -> Dict[str, Any]:
    """Consolidate Amazon and additional-link bibliographic data, removing duplicates."""

    async def _run() -> Dict[str, Any]:
        db = await get_db()
        submission_repo = SubmissionRepository(db)
        book_repo = BookRepository(db)
        summary_repo = SummaryRepository(db)

        submission = await submission_repo.get_by_id(submission_id)
        if not submission:
            return {"status": "error", "error": "submission_not_found"}

        book = await book_repo.get_by_submission(submission_id)
        if not book:
            return {"status": "error", "error": "book_not_found"}

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.PENDING_CONTEXT,
            {"current_step": "bibliographic_consolidation"},
        )

        summaries = await summary_repo.get_by_book(str(book.get("_id")))
        candidates = [
            item.get("bibliographic_data")
            for item in summaries
            if isinstance(item.get("bibliographic_data"), dict) and item.get("bibliographic_data")
        ]

        extracted = book.get("extracted", {}) or {}
        consolidated = _consolidate_bibliographic(amazon_data=extracted, link_candidates=candidates)

        await book_repo.create_or_update(
            submission_id=submission_id,
            extracted={
                "consolidated_bibliographic": consolidated,
                "consolidated_sources_count": len(candidates),
                "consolidated_at": datetime.utcnow(),
            },
        )

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.PENDING_CONTEXT,
            {"current_step": "internet_research"},
        )

        next_delay = await _get_step_delay_seconds("consolidate_book_data")
        _enqueue_task(internet_research_task, next_delay, submission_id=submission_id)
        return {"status": "ok", "consolidated_sources_count": len(candidates)}

    return asyncio.run(_run())


@shared_task(base=ScraperTask, bind=True)
def internet_research_task(self, submission_id: str) -> Dict[str, Any]:
    """Research web sources about book and author using GROQ credential and persist results."""

    async def _run() -> Dict[str, Any]:
        db = await get_db()
        submission_repo = SubmissionRepository(db)
        book_repo = BookRepository(db)
        prompt_repo = PromptRepository(db)
        credential_repo = CredentialRepository(db)

        submission = await submission_repo.get_by_id(submission_id)
        if not submission:
            return {"status": "error", "error": "submission_not_found"}

        book = await book_repo.get_by_submission(submission_id)
        if not book:
            return {"status": "error", "error": "book_not_found"}

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.PENDING_CONTEXT,
            {"current_step": "internet_research"},
        )

        prompt_doc = await _ensure_prompt(prompt_repo, WEB_RESEARCH_PROMPT)
        groq_api_key = await _resolve_credential_key(credential_repo, preferred_name="GROC A", service="groq")

        title = str(submission.get("title") or "")
        author = str(submission.get("author_name") or "")

        finder = LinkFinder()
        links: List[Dict[str, Any]] = []
        try:
            links = await finder.search_book_links(title=title, author=author, count=4)
        except Exception as exc:
            logger.warning("Web search failed for %s: %s", submission_id, exc)

        source_blobs: List[Dict[str, Any]] = []
        for item in links[:4]:
            url = str(item.get("url") or "").strip()
            if not url:
                continue
            content_excerpt = ""
            try:
                content = await finder.fetch_and_parse(url)
                content_excerpt = content[:1400]
            except Exception:
                content_excerpt = ""

            source_blobs.append(
                {
                    "url": url,
                    "title": str(item.get("title") or ""),
                    "snippet": str(item.get("snippet") or ""),
                    "content_excerpt": content_excerpt,
                }
            )

        llm = LLMClient()
        research_data = await _run_web_research(
            llm=llm,
            prompt_doc=prompt_doc,
            title=title,
            author=author,
            source_blobs=source_blobs,
            api_key=groq_api_key,
        )

        await book_repo.create_or_update(
            submission_id=submission_id,
            extracted={
                "web_research": {
                    "research_markdown": research_data.get("research_markdown"),
                    "topics": research_data.get("topics", []),
                    "key_insights": research_data.get("key_insights", []),
                    "sources": source_blobs,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            },
        )

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.CONTEXT_GENERATION,
            {"current_step": "context_generation"},
        )
        next_delay = await _get_step_delay_seconds("internet_research")
        _enqueue_task(generate_context_task, next_delay, submission_id=submission_id)

        return {"status": "ok", "sources_count": len(source_blobs)}

    return asyncio.run(_run())


@shared_task(bind=True)
def generate_context_task(self, submission_id: str) -> Dict[str, Any]:
    """Generate knowledge base markdown for a submission."""

    async def _run() -> Dict[str, Any]:
        db = await get_db()
        submission_repo = SubmissionRepository(db)
        book_repo = BookRepository(db)
        kb_repo = KnowledgeBaseRepository(db)
        summary_repo = SummaryRepository(db)
        prompt_repo = PromptRepository(db)

        submission = await submission_repo.get_by_id(submission_id)
        if not submission:
            return {"status": "error", "error": "submission_not_found"}

        book = await book_repo.get_by_submission(submission_id)
        if not book:
            return {"status": "error", "error": "book_not_found"}

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.CONTEXT_GENERATION,
            {"current_step": "context_generation"},
        )

        summaries = await summary_repo.get_by_book(str(book.get("_id")))
        prompt = (
            await prompt_repo.get_active_by_purpose("context")
            or await prompt_repo.get_by_name("Context Generator - Technical Books")
        )

        book_title = submission.get("title")
        author_name = submission.get("author_name")
        extracted = book.get("extracted", {}) or {}
        consolidated = extracted.get("consolidated_bibliographic", {}) if isinstance(extracted, dict) else {}
        web_research = extracted.get("web_research", {}) if isinstance(extracted, dict) else {}

        llm_markdown = None
        if prompt:
            user_prompt = prompt.get("user_prompt", "")
            user_prompt = user_prompt.replace("{{title}}", str(book_title or ""))
            user_prompt = user_prompt.replace("{{author}}", str(author_name or ""))
            user_prompt = user_prompt.replace("{{data}}", json.dumps(extracted, ensure_ascii=False, default=str))

            if consolidated:
                user_prompt += "\n\nConsolidated bibliographic data:\n"
                user_prompt += json.dumps(consolidated, ensure_ascii=False, default=str)

            if isinstance(web_research, dict) and web_research.get("research_markdown"):
                user_prompt += "\n\nWeb research notes:\n"
                user_prompt += str(web_research.get("research_markdown"))

            if summaries:
                user_prompt += "\n\nExternal summaries:\n"
                for item in summaries:
                    user_prompt += f"- {item.get('source_url')}: {item.get('summary_text')}\n"

            user_prompt = build_user_prompt_with_output_format(user_prompt, prompt)

            try:
                llm = LLMClient()
                llm_markdown = await llm.generate_with_retry(
                    system_prompt=prompt.get("system_prompt", ""),
                    user_prompt=user_prompt,
                    model_id=prompt.get("model_id", "gpt-4o-mini"),
                    temperature=prompt.get("temperature", 0.7),
                    max_tokens=prompt.get("max_tokens", 1200),
                )
            except Exception as exc:
                logger.warning("LLM context generation failed: %s", exc)

        if not llm_markdown:
            lines = [
                f"# Knowledge Base: {book_title}",
                "",
                f"**Author:** {author_name}",
                "",
                "## Extracted Metadata (Amazon + Consolidated)",
            ]
            for key, value in extracted.items():
                if key == "web_research":
                    continue
                lines.append(f"- **{key}**: {value}")

            if isinstance(web_research, dict) and web_research.get("research_markdown"):
                lines.append("")
                lines.append("## Web Research")
                lines.append(str(web_research.get("research_markdown")))

            if summaries:
                lines.append("")
                lines.append("## External Summaries")
                for item in summaries:
                    lines.append(f"- **{item.get('source_url')}**: {item.get('summary_text')}")

            llm_markdown = "\n".join(lines)

        topics_index = []
        if isinstance(extracted, dict):
            if extracted.get("theme"):
                topics_index.append(str(extracted.get("theme")))
            consolidated_data = extracted.get("consolidated_bibliographic")
            if isinstance(consolidated_data, dict):
                topics_index.extend([str(item) for item in consolidated_data.get("authors", []) if item])
            web = extracted.get("web_research")
            if isinstance(web, dict):
                topics_index.extend([str(item) for item in web.get("topics", []) if item])

        await kb_repo.create_or_update(
            book_id=str(book.get("_id")),
            markdown_content=llm_markdown,
            topics_index=_dedupe_list(topics_index)[:30],
            submission_id=submission_id,
        )

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.CONTEXT_GENERATED,
            {"current_step": "context_generated"},
        )

        return {"status": "ok"}

    return asyncio.run(_run())


@shared_task(bind=True)
def check_scraping_status(self, submission_id: str) -> Dict[str, Any]:
    """Check current scraping status for a submission."""

    async def _run() -> Dict[str, Any]:
        db = await get_db()
        submission_repo = SubmissionRepository(db)
        submission = await submission_repo.get_by_id(submission_id)
        if not submission:
            return {"status": "not_found"}

        return {
            "status": "ok",
            "submission_id": submission_id,
            "submission_status": submission.get("status"),
            "current_step": submission.get("current_step"),
            "updated_at": submission.get("updated_at"),
        }

    return asyncio.run(_run())


def start_scraping_pipeline(submission_id: str, amazon_url: str) -> None:
    """Start scraping pipeline by queueing Amazon task."""
    scrape_amazon_task.delay(submission_id=submission_id, amazon_url=amazon_url)
