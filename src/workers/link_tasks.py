"""Celery tasks for external link discovery and summarization."""

from __future__ import annotations

import asyncio
import logging

from celery import shared_task

from src.db.connection import get_db
from src.db.repositories import (
    SubmissionRepository,
    BookRepository,
    SummaryRepository,
    PromptRepository,
    KnowledgeBaseRepository,
)
from src.scrapers.link_finder import LinkFinder

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def find_and_summarize_links(self, submission_id: str, book_title: str, author: str):
    """Find and summarize 3 relevant external links for a submission."""

    async def _run():
        db = await get_db()
        submission_repo = SubmissionRepository(db)
        book_repo = BookRepository(db)
        summary_repo = SummaryRepository(db)
        prompt_repo = PromptRepository(db)
        kb_repo = KnowledgeBaseRepository(db)

        submission = await submission_repo.get_by_id(submission_id)
        if not submission:
            return {"status": "error", "error": "submission_not_found"}

        book = await book_repo.get_by_submission(submission_id)
        if not book:
            # Create minimal book entry if missing to keep flow resilient
            book_id = await book_repo.create_or_update(
                submission_id=submission_id,
                extracted={"title": book_title, "authors": [author], "link_task_seed": True},
            )
            book = await book_repo.get_by_id(book_id)

        finder = LinkFinder()
        links = await finder.search_book_links(title=book_title, author=author, count=3)

        prompt = (
            await prompt_repo.get_active_by_purpose("summarization")
            or await prompt_repo.get_active_by_purpose("link_summarization")
            or await prompt_repo.get_by_name("Link Summarizer")
        )

        saved = 0
        for item in links:
            url = item.get("url")
            if not url:
                continue

            try:
                content = await finder.fetch_and_parse(url)
                summary_data = await finder.summarize_page(content=content, title=book_title, prompt_doc=prompt)
                await summary_repo.create(
                    book_id=str(book.get("_id")),
                    source_url=url,
                    source_domain=finder.get_domain(url),
                    summary_text=summary_data.get("summary", ""),
                    topics=summary_data.get("topics", []),
                    key_points=summary_data.get("key_points", []),
                    credibility=summary_data.get("credibility"),
                )
                saved += 1
            except Exception as exc:
                logger.warning("Failed to summarize link %s: %s", url, exc)

        summaries = await summary_repo.get_by_book(str(book.get("_id")))
        if summaries:
            kb = await kb_repo.get_by_book(str(book.get("_id")))
            current_md = kb.get("markdown_content", "") if kb else ""
            section_lines = ["", "## External Sources", ""]
            for s in summaries[:6]:
                section_lines.append(f"- **{s.get('source_url')}**: {s.get('summary_text')}")
            merged_md = (current_md + "\n" + "\n".join(section_lines)).strip()

            topics = []
            for s in summaries:
                topics.extend(s.get("topics", []))
            dedup_topics = list(dict.fromkeys([t for t in topics if t]))[:20]

            await kb_repo.create_or_update(
                book_id=str(book.get("_id")),
                submission_id=submission_id,
                markdown_content=merged_md,
                topics_index=dedup_topics,
            )

        return {"status": "ok", "links_found": len(links), "summaries_saved": saved}

    return asyncio.run(_run())
