"""
Task management API endpoints.

These routes provide:
- Listing submissions with pagination/filter
- Fetching detailed task status
- Triggering context/article generation
- Retry and operational endpoints
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
from src.workers.worker import start_pipeline

router = APIRouter(prefix="/tasks", tags=["Tasks"])
logger = logging.getLogger(__name__)


def _build_progress(current_status: str) -> Dict[str, Any]:
    steps_def = [
        (SubmissionStatus.PENDING_SCRAPE.value, "Scraping metadata..."),
        (SubmissionStatus.PENDING_CONTEXT.value, "Generating context..."),
        (SubmissionStatus.PENDING_ARTICLE.value, "Creating article..."),
        (SubmissionStatus.READY_FOR_REVIEW.value, "Ready for review"),
    ]

    stage_alias = {
        SubmissionStatus.SCRAPING_AMAZON.value: SubmissionStatus.PENDING_SCRAPE.value,
        SubmissionStatus.SCRAPING_GOODREADS.value: SubmissionStatus.PENDING_SCRAPE.value,
        SubmissionStatus.SCRAPED.value: SubmissionStatus.PENDING_CONTEXT.value,
        SubmissionStatus.CONTEXT_GENERATION.value: SubmissionStatus.PENDING_CONTEXT.value,
        SubmissionStatus.CONTEXT_GENERATED.value: SubmissionStatus.PENDING_ARTICLE.value,
        SubmissionStatus.ARTICLE_GENERATED.value: SubmissionStatus.READY_FOR_REVIEW.value,
        SubmissionStatus.APPROVED.value: SubmissionStatus.READY_FOR_REVIEW.value,
        SubmissionStatus.PUBLISHED.value: SubmissionStatus.READY_FOR_REVIEW.value,
    }

    normalized_status = stage_alias.get(current_status, current_status)

    try:
        current_idx = next(i for i, (stage, _) in enumerate(steps_def) if stage == normalized_status)
    except StopIteration:
        current_idx = -1

    steps = [
        {"stage": stage, "label": label, "completed": idx <= current_idx}
        for idx, (stage, label) in enumerate(steps_def)
    ]
    return {"current_stage": current_status, "steps": steps}


def _serialize_submission(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id")),
        "title": doc.get("title"),
        "author_name": doc.get("author_name"),
        "amazon_url": doc.get("amazon_url"),
        "goodreads_url": doc.get("goodreads_url"),
        "author_site": doc.get("author_site"),
        "other_links": doc.get("other_links", []),
        "textual_information": doc.get("textual_information"),
        "run_immediately": doc.get("run_immediately", True),
        "schedule_execution": doc.get("schedule_execution"),
        "main_category": doc.get("main_category"),
        "article_status": doc.get("article_status"),
        "user_approval_required": doc.get("user_approval_required", False),
        "status": doc.get("status"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "current_step": doc.get("current_step"),
        "attempts": doc.get("attempts", {}),
        "errors": doc.get("errors", []),
    }


@router.get("/health", tags=["Health"])
async def tasks_health():
    return {"status": "ok", "endpoint": "tasks"}


@router.get("/stats", summary="Get aggregated task stats")
async def stats(repo: SubmissionRepository = Depends(get_submission_repo)):
    return await repo.stats()


@router.get("", summary="List all submission tasks")
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by submission status"),
    search: Optional[str] = Query(None, description="Search by title or author"),
    repo: SubmissionRepository = Depends(get_submission_repo),
):
    submissions, total = await repo.list_all(skip=skip, limit=limit, status=status, search=search)
    tasks = [_serialize_submission(doc) for doc in submissions]

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
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Submission not found: {submission_id}")

    book = await book_repo.get_by_submission(submission_id)
    kb = await kb_repo.get_by_book(str(book["_id"])) if book else None
    article = await article_repo.get_by_book(str(book["_id"])) if book else None
    draft = await article_repo.get_draft(str(article["_id"])) if article else None

    book_data = None
    if book:
        book_data = {
            "id": str(book.get("_id")),
            "submission_id": str(book.get("submission_id")),
            "extracted": book.get("extracted", {}),
            "last_updated": book.get("last_updated"),
        }

    article_data = None
    if article:
        article_data = {
            "id": str(article.get("_id")),
            "book_id": str(article.get("book_id")),
            "submission_id": str(article.get("submission_id")) if article.get("submission_id") else None,
            "title": article.get("title"),
            "content": article.get("content"),
            "word_count": article.get("word_count"),
            "status": article.get("status"),
            "wordpress_post_id": article.get("wordpress_post_id"),
            "wordpress_url": article.get("wordpress_url"),
            "created_at": article.get("created_at"),
            "updated_at": article.get("updated_at"),
        }

    return {
        "submission": _serialize_submission(submission),
        "book": book_data,
        "knowledge_base": kb if kb else None,
        "article": article_data,
        "draft": draft,
        "progress": _build_progress(submission.get("status")),
    }


@router.post("/{submission_id}/generate_context", status_code=status.HTTP_202_ACCEPTED, summary="Enqueue context generation")
async def trigger_context_generation(
    submission_id: str,
    repo: SubmissionRepository = Depends(get_submission_repo),
):
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    try:
        from src.workers.scraper_tasks import generate_context_task

        generate_context_task.delay(submission_id=submission_id)
        await repo.update_status(submission_id, SubmissionStatus.CONTEXT_GENERATION)
    except Exception as e:
        logger.error("Failed to enqueue context generation: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue context generation")

    return {"status": "queued", "task": "generate_context", "submission_id": submission_id}


@router.post("/{submission_id}/generate_article", status_code=status.HTTP_202_ACCEPTED, summary="Enqueue article generation")
async def trigger_article_generation(
    submission_id: str,
    repo: SubmissionRepository = Depends(get_submission_repo),
):
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    try:
        from src.workers.article_tasks import generate_article_task

        generate_article_task.delay(submission_id=submission_id)
        await repo.update_status(submission_id, SubmissionStatus.PENDING_ARTICLE)
    except Exception as e:
        logger.error("Failed to enqueue article generation: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue article generation")

    return {"status": "queued", "task": "generate_article", "submission_id": submission_id}


@router.post("/{submission_id}/retry", status_code=status.HTTP_202_ACCEPTED, summary="Retry failed submission")
async def retry_task(submission_id: str, repo: SubmissionRepository = Depends(get_submission_repo)):
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    await repo.update_status(
        submission_id,
        SubmissionStatus.PENDING_SCRAPE,
        {
            "current_step": "retry_pending",
            "errors": [],
        },
    )

    try:
        start_pipeline.delay(submission_id=submission_id, amazon_url=submission.get("amazon_url"))
    except Exception as e:
        logger.error("Failed to enqueue retry pipeline: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue retry")

    return {"status": "queued", "task": "retry", "submission_id": submission_id}


@router.post("/{submission_id}/draft_article", status_code=status.HTTP_200_OK, summary="Save article draft")
async def save_draft_article(
    submission_id: str,
    payload: Dict[str, Any] = Body(...),
    repo: SubmissionRepository = Depends(get_submission_repo),
    book_repo: BookRepository = Depends(get_book_repo),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    book = await book_repo.get_by_submission(submission_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found for submission")

    article = await article_repo.get_by_book(str(book.get("_id")))
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found for submission")

    content = payload.get("content")
    if not isinstance(content, str) or not content.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="content is required")

    draft_id = await article_repo.save_draft(str(article.get("_id")), content)
    await article_repo.update(str(article.get("_id")), {"status": "draft"})

    return {
        "status": "saved",
        "draft_id": draft_id,
        "article_id": str(article.get("_id")),
        "submission_id": submission_id,
    }


@router.post("/{submission_id}/publish_article", status_code=status.HTTP_202_ACCEPTED, summary="Publish article to WordPress")
async def publish_article(
    submission_id: str,
    repo: SubmissionRepository = Depends(get_submission_repo),
    book_repo: BookRepository = Depends(get_book_repo),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if submission.get("user_approval_required") and submission.get("status") not in {
        SubmissionStatus.APPROVED.value,
        SubmissionStatus.READY_FOR_REVIEW.value,
    }:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Submission requires approval before publishing")

    book = await book_repo.get_by_submission(submission_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found for submission")

    article = await article_repo.get_by_book(str(book.get("_id")))
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found for submission")

    try:
        from src.workers.publishing_tasks import publish_article_task

        celery_task = publish_article_task.delay(article_id=str(article.get("_id")), submission_id=submission_id)
    except Exception as e:
        logger.error("Failed to enqueue publication: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue publication")

    return {
        "status": "queued",
        "celery_task_id": celery_task.id,
        "article_id": str(article.get("_id")),
        "submission_id": submission_id,
    }


@router.patch("/{submission_id}", status_code=status.HTTP_200_OK, summary="Update submission or book data")
async def update_task(
    submission_id: str,
    payload: Dict[str, Any] = Body(...),
    repo: SubmissionRepository = Depends(get_submission_repo),
    book_repo: BookRepository = Depends(get_book_repo),
):
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if payload.get("submission"):
        await repo.update_fields(submission_id, payload["submission"])

    if payload.get("book") and isinstance(payload["book"], dict):
        extracted = payload["book"].get("extracted")
        if extracted is not None:
            await book_repo.create_or_update(submission_id=submission_id, extracted=extracted)

    updated = await repo.get_by_id(submission_id)
    book = await book_repo.get_by_submission(submission_id)

    return {
        "submission": _serialize_submission(updated),
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
