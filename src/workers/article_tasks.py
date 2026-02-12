"""Article generation tasks using ArticleStructurer."""

from __future__ import annotations

import asyncio
import logging

from celery import shared_task

from src.db.connection import get_db
from src.db.repositories import (
    SubmissionRepository,
    BookRepository,
    KnowledgeBaseRepository,
    ArticleRepository,
)
from src.models.enums import SubmissionStatus
from src.workers.article_structurer import ArticleStructurer

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_article_task(self, submission_id: str) -> dict:
    """Generate a full review article for a submission."""

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _run():
            db = await get_db()
            submission_repo = SubmissionRepository(db)
            book_repo = BookRepository(db)
            kb_repo = KnowledgeBaseRepository(db)
            article_repo = ArticleRepository(db)

            submission = await submission_repo.get_by_id(submission_id)
            if not submission:
                return {"status": "error", "error": "submission_not_found"}

            book = await book_repo.get_by_submission(submission_id)
            if not book:
                return {"status": "error", "error": "book_not_found"}

            kb = await kb_repo.get_by_book(str(book.get("_id")))
            context = kb.get("markdown_content", "") if kb else ""

            await submission_repo.update_status(
                submission_id,
                SubmissionStatus.PENDING_ARTICLE,
                {"current_step": "article_generation"},
            )

            structurer = ArticleStructurer()
            book_data = {
                "title": submission.get("title") or "Book Review",
                "author": submission.get("author_name") or "",
                "metadata": book.get("extracted", {}),
            }

            try:
                article_content = await structurer.generate_valid_article(
                    book_data=book_data,
                    context=context,
                    max_retries=3,
                )
            except Exception:
                # Deterministic fallback keeps pipeline moving even when strict validation fails.
                fallback_topics = structurer._fallback_topics(book_data)
                article_content = structurer._build_template_article(book_data, fallback_topics, context)

            lines = article_content.splitlines()
            gen_title = next(
                (line.replace("# ", "").strip() for line in lines if line.startswith("# ")),
                f"{book_data['title']} Review",
            )

            validation = await structurer.validate_article(article_content, strict=True)

            article_id = await article_repo.create(
                book_id=str(book.get("_id")),
                submission_id=submission_id,
                title=gen_title,
                content=article_content,
                word_count=len(article_content.split()),
                status="draft" if submission.get("user_approval_required") else "in_review",
                validation_report=validation,
            )

            await submission_repo.update_status(
                submission_id,
                SubmissionStatus.ARTICLE_GENERATED,
                {
                    "current_step": "article_generated",
                    "article_id": article_id,
                },
            )

            if not submission.get("user_approval_required"):
                await submission_repo.update_status(
                    submission_id,
                    SubmissionStatus.READY_FOR_REVIEW,
                    {"current_step": "ready_for_review"},
                )

            logger.info("Article generated successfully: %s", article_id)
            return {"status": "ok", "article_id": article_id}

        return loop.run_until_complete(_run())
    except Exception as e:
        logger.error("Error generating article: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}
