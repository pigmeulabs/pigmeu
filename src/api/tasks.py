"""
Task management API endpoints.

These routes provide:
- Listing submissions with pagination
- Fetching detailed task status (submission, book data, progress)
- Triggering background context/article generation
- Updating submission/book fields (used by the web UI)
"""

import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status

from src.api.dependencies import (
    get_submission_repo,
    get_book_repo,
    get_knowledge_base_repo,
    get_article_repo,
)
from src.db.repositories import (
    SubmissionRepository,
    BookRepository,
    KnowledgeBaseRepository,
    ArticleRepository,
)
from src.models.enums import SubmissionStatus

router = APIRouter(prefix="/tasks", tags=["Tasks"])
logger = logging.getLogger(__name__)


def _build_progress(current_status: str) -> Dict[str, Any]:
    """Return a simple progress structure for the pipeline."""
    steps_def = [
        (SubmissionStatus.PENDING_SCRAPE.value, "Scraping metadata..."),
        (SubmissionStatus.PENDING_CONTEXT.value, "Generating context..."),
        (SubmissionStatus.PENDING_ARTICLE.value, "Creating article..."),
        (SubmissionStatus.READY_FOR_REVIEW.value, "Ready for review"),
    ]
    try:
        current_idx = next(
            i for i, (stage, _) in enumerate(steps_def) if stage == current_status
        )
    except StopIteration:
        current_idx = -1

    steps = [
        {"stage": stage, "label": label, "completed": idx <= current_idx}
        for idx, (stage, label) in enumerate(steps_def)
    ]
    return {"current_stage": current_status, "steps": steps}


@router.get("", summary="List all submission tasks")
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by submission status"),
    repo: SubmissionRepository = Depends(get_submission_repo),
):
    """List submissions with pagination."""
    submissions, total = await repo.list_all(skip=skip, limit=limit, status=status)
    tasks = []
    for doc in submissions:
        tasks.append(
            {
                "id": str(doc.get("_id")),
                "title": doc.get("title"),
                "author_name": doc.get("author_name"),
                "amazon_url": doc.get("amazon_url"),
                "status": doc.get("status"),
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
            }
        )

    return {
        "tasks": tasks,
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(tasks),
    }


@router.get("/{submission_id}", summary="Get task details")
async def get_task(
    submission_id: str,
    repo: SubmissionRepository = Depends(get_submission_repo),
    book_repo: BookRepository = Depends(get_book_repo),
    kb_repo: KnowledgeBaseRepository = Depends(get_knowledge_base_repo),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    """Fetch submission details, extracted book data and progress."""
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission not found: {submission_id}",
        )

    book = await book_repo.get_by_submission(submission_id)
    kb = await kb_repo.get_by_book(str(book["_id"])) if book else None
    article = await article_repo.get_by_book(str(book["_id"])) if book else None

    submission_data = {
        "id": str(submission.get("_id")),
        "title": submission.get("title"),
        "author_name": submission.get("author_name"),
        "amazon_url": submission.get("amazon_url"),
        "goodreads_url": submission.get("goodreads_url"),
        "author_site": submission.get("author_site"),
        "other_links": submission.get("other_links", []),
        "status": submission.get("status"),
        "created_at": submission.get("created_at"),
        "updated_at": submission.get("updated_at"),
    }

    book_data = None
    if book:
        book_data = {
            "id": str(book.get("_id")),
            "submission_id": str(book.get("submission_id")),
            "extracted": book.get("extracted", {}),
            "last_updated": book.get("last_updated"),
        }

    progress = _build_progress(submission.get("status"))

    return {
        "submission": submission_data,
        "book": book_data,
        "knowledge_base": kb if kb else None,
        "article": article if article else None,
        "progress": progress,
    }


@router.post(
    "/{submission_id}/generate_context",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue context generation",
)
async def trigger_context_generation(
    submission_id: str,
    repo: SubmissionRepository = Depends(get_submission_repo),
):
    """Trigger background context generation for a submission."""
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )

    try:
        from src.workers.scraper_tasks import generate_context_task

        generate_context_task.delay(submission_id=submission_id)
        await repo.update_fields(
            submission_id, {"status": SubmissionStatus.PENDING_CONTEXT.value}
        )
    except Exception as e:
        logger.error(f"Failed to enqueue context generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue context generation",
        )

    return {"status": "queued", "task": "generate_context", "submission_id": submission_id}


@router.post(
    "/{submission_id}/generate_article",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue article generation",
)
async def trigger_article_generation(
    submission_id: str,
    repo: SubmissionRepository = Depends(get_submission_repo),
):
    """Trigger background article generation for a submission."""
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )

    try:
        from src.workers.article_tasks import generate_article_task

        generate_article_task.delay(submission_id=submission_id)
        await repo.update_fields(
            submission_id, {"status": SubmissionStatus.PENDING_ARTICLE.value}
        )
    except Exception as e:
        logger.error(f"Failed to enqueue article generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue article generation",
        )

    return {"status": "queued", "task": "generate_article", "submission_id": submission_id}


@router.patch(
    "/{submission_id}",
    status_code=status.HTTP_200_OK,
    summary="Update submission or book data",
)
async def update_task(
    submission_id: str,
    payload: Dict[str, Any] = Body(...),
    repo: SubmissionRepository = Depends(get_submission_repo),
    book_repo: BookRepository = Depends(get_book_repo),
):
    """Update submission fields and/or book extracted data."""
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )

    if payload.get("submission"):
        await repo.update_fields(submission_id, payload["submission"])

    if payload.get("book") and isinstance(payload["book"], dict):
        extracted = payload["book"].get("extracted")
        if extracted is not None:
            await book_repo.create_or_update(
                submission_id=submission_id, extracted=extracted
            )

    updated = await repo.get_by_id(submission_id)
    book = await book_repo.get_by_submission(submission_id)

    return {
        "submission": {
            "id": str(updated.get("_id")),
            "title": updated.get("title"),
            "author_name": updated.get("author_name"),
            "amazon_url": updated.get("amazon_url"),
            "status": updated.get("status"),
            "created_at": updated.get("created_at"),
            "updated_at": updated.get("updated_at"),
        },
        "book": {
            "id": str(book.get("_id")),
            "submission_id": str(book.get("submission_id")),
            "extracted": book.get("extracted", {}),
            "last_updated": book.get("last_updated"),
        }
        if book
        else None,
        "progress": _build_progress(updated.get("status")),
    }


@router.get("/health", tags=["Health"])
async def tasks_health():
    """Health check for tasks endpoints."""
    return {"status": "ok", "endpoint": "tasks"}
