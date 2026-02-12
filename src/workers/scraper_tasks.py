"""Celery task definitions for scraping and context pipeline."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from celery import shared_task, Task

from src.db.connection import get_db
from src.db.repositories import (
    SubmissionRepository,
    BookRepository,
    KnowledgeBaseRepository,
    SummaryRepository,
    PromptRepository,
)
from src.models.enums import SubmissionStatus
from src.scrapers.amazon import AmazonScraper
from src.scrapers.goodreads import GoodreadsScraper
from src.workers.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ScraperTask(Task):
    """Base Celery task class with retry behavior."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


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

        if not extracted:
            extracted = {
                "title": submission.get("title"),
                "authors": [submission.get("author_name")],
                "amazon_url": amazon_url,
                "scrape_fallback": True,
            }

        book_id = await book_repo.create_or_update(submission_id=submission_id, extracted=extracted)

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.SCRAPING_GOODREADS,
            {
                "current_step": "goodreads_scrape",
                "book_id": book_id,
            },
        )

        scrape_goodreads_task.delay(
            submission_id=submission_id,
            title=extracted.get("title") or submission.get("title"),
            author=submission.get("author_name"),
        )

        return {"status": "ok", "book_id": book_id}

    return asyncio.run(_run())


@shared_task(base=ScraperTask, bind=True)
def scrape_goodreads_task(self, submission_id: str, title: str, author: str | None = None) -> Dict[str, Any]:
    """Enrich book metadata with Goodreads data (best-effort)."""

    async def _run() -> Dict[str, Any]:
        db = await get_db()
        submission_repo = SubmissionRepository(db)
        book_repo = BookRepository(db)

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.SCRAPING_GOODREADS,
            {
                "current_step": "goodreads_scrape",
                "started_at": datetime.utcnow(),
            },
        )

        goodreads_data: Dict[str, Any] = {"goodreads_found": False}
        scraper = GoodreadsScraper()

        try:
            await scraper.initialize()
            results = await scraper.search(title=title, author=author)
            if results:
                best = results[0]
                detail = None
                if best.get("goodreads_url"):
                    detail = await scraper.get_book_details(best.get("goodreads_url"))
                if detail:
                    best.update(detail)
                goodreads_data = {"goodreads_found": True, **best}
        except Exception as exc:
            logger.warning("Goodreads scrape failed for %s: %s", submission_id, exc)
        finally:
            try:
                await scraper.cleanup()
            except Exception:
                pass

        await book_repo.create_or_update(
            submission_id=submission_id,
            extracted={"goodreads_data": goodreads_data, "goodreads_updated_at": datetime.utcnow()},
        )

        await submission_repo.update_status(
            submission_id,
            SubmissionStatus.CONTEXT_GENERATION,
            {"current_step": "context_generation"},
        )

        try:
            from src.workers.link_tasks import find_and_summarize_links

            find_and_summarize_links.delay(
                submission_id=submission_id,
                book_title=title,
                author=author or "",
            )
        except Exception as exc:
            logger.warning("Unable to enqueue link summarization for %s: %s", submission_id, exc)

        return {"status": "ok", "goodreads_found": goodreads_data.get("goodreads_found", False)}

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
        extracted = book.get("extracted", {})

        llm_markdown = None
        if prompt:
            user_prompt = prompt.get("user_prompt", "")
            user_prompt = user_prompt.replace("{{title}}", str(book_title or ""))
            user_prompt = user_prompt.replace("{{author}}", str(author_name or ""))
            user_prompt = user_prompt.replace("{{data}}", str(extracted))

            if summaries:
                user_prompt += "\n\nExternal summaries:\n"
                for item in summaries:
                    user_prompt += f"- {item.get('source_url')}: {item.get('summary_text')}\n"

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
                "## Extracted Metadata",
            ]
            for key, value in extracted.items():
                lines.append(f"- **{key}**: {value}")

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
            goodreads = extracted.get("goodreads_data")
            if isinstance(goodreads, dict) and goodreads.get("title"):
                topics_index.append(str(goodreads.get("title")))

        await kb_repo.create_or_update(
            book_id=str(book.get("_id")),
            markdown_content=llm_markdown,
            topics_index=topics_index,
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
