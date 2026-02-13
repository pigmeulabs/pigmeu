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
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from bson import ObjectId

from src.api.dependencies import (
    get_submission_repo,
    get_book_repo,
    get_summary_repo,
    get_knowledge_base_repo,
    get_article_repo,
)
from src.db.repositories import (
    SubmissionRepository,
    BookRepository,
    SummaryRepository,
    KnowledgeBaseRepository,
    ArticleRepository,
)
from src.models.enums import SubmissionStatus
from src.workers.worker import start_pipeline

router = APIRouter(prefix="/tasks", tags=["Tasks"])
logger = logging.getLogger(__name__)


def _normalize_retry_stage(stage: str) -> Optional[str]:
    normalized = str(stage or "").strip().lower()
    mapping = {
        "amazon_scrape": "amazon_scrape",
        "pending_scrape": "amazon_scrape",
        "additional_links_scrape": "additional_links_scrape",
        "summarize_additional_links": "summarize_additional_links",
        "consolidate_book_data": "consolidate_book_data",
        "internet_research": "internet_research",
        "context_generation": "context_generation",
        "pending_context": "context_generation",
        "article_generation": "article_generation",
        "pending_article": "article_generation",
        "ready_for_review": "article_generation",
    }
    return mapping.get(normalized)


async def _delete_articles_and_drafts(
    article_repo: ArticleRepository,
    submission_object_id=None,
    book_object_id=None,
) -> None:
    filters = []
    if submission_object_id is not None:
        filters.append({"submission_id": submission_object_id})
    if book_object_id is not None:
        filters.append({"book_id": book_object_id})
    if not filters:
        return

    query = {"$or": filters} if len(filters) > 1 else filters[0]
    docs = await article_repo.collection.find(query, {"_id": 1}).to_list(length=None)
    article_ids = [item.get("_id") for item in docs if item.get("_id") is not None]
    if article_ids:
        await article_repo.drafts_collection.delete_many({"article_id": {"$in": article_ids}})
    await article_repo.collection.delete_many(query)


async def _clear_book_extracted_keys(book_repo: BookRepository, book_doc: Dict[str, Any], keys: list[str]) -> None:
    extracted = dict(book_doc.get("extracted") or {})
    changed = False
    for key in keys:
        if key in extracted:
            extracted.pop(key, None)
            changed = True

    if changed:
        await book_repo.collection.update_one(
            {"_id": book_doc.get("_id")},
            {
                "$set": {
                    "extracted": extracted,
                    "last_updated": datetime.utcnow(),
                }
            },
        )


async def _cleanup_from_stage(
    stage: str,
    submission_doc: Dict[str, Any],
    book_doc: Optional[Dict[str, Any]],
    repo: SubmissionRepository,
    book_repo: BookRepository,
    summary_repo: SummaryRepository,
    kb_repo: KnowledgeBaseRepository,
    article_repo: ArticleRepository,
) -> None:
    submission_object_id = submission_doc.get("_id")
    book_object_id = book_doc.get("_id") if book_doc else None

    if stage == "amazon_scrape":
        if book_object_id is not None:
            await summary_repo.collection.delete_many({"book_id": book_object_id})
            await kb_repo.collection.delete_many(
                {"$or": [{"book_id": book_object_id}, {"submission_id": submission_object_id}]}
            )
            await _delete_articles_and_drafts(
                article_repo=article_repo,
                submission_object_id=submission_object_id,
                book_object_id=book_object_id,
            )
            await book_repo.collection.delete_one({"_id": book_object_id})
        else:
            await kb_repo.collection.delete_many({"submission_id": submission_object_id})
            await _delete_articles_and_drafts(
                article_repo=article_repo,
                submission_object_id=submission_object_id,
            )
        return

    if stage in {"additional_links_scrape", "summarize_additional_links"}:
        if book_object_id is not None:
            await summary_repo.collection.delete_many({"book_id": book_object_id})
            await kb_repo.collection.delete_many(
                {"$or": [{"book_id": book_object_id}, {"submission_id": submission_object_id}]}
            )
            await _delete_articles_and_drafts(
                article_repo=article_repo,
                submission_object_id=submission_object_id,
                book_object_id=book_object_id,
            )
            await _clear_book_extracted_keys(
                book_repo=book_repo,
                book_doc=book_doc,
                keys=[
                    "link_bibliographic_candidates",
                    "additional_links_total",
                    "additional_links_processed",
                    "additional_links_processed_at",
                    "consolidated_bibliographic",
                    "consolidated_sources_count",
                    "consolidated_at",
                    "web_research",
                ],
            )
        return

    if stage == "consolidate_book_data":
        if book_object_id is not None:
            await kb_repo.collection.delete_many(
                {"$or": [{"book_id": book_object_id}, {"submission_id": submission_object_id}]}
            )
            await _delete_articles_and_drafts(
                article_repo=article_repo,
                submission_object_id=submission_object_id,
                book_object_id=book_object_id,
            )
            await _clear_book_extracted_keys(
                book_repo=book_repo,
                book_doc=book_doc,
                keys=[
                    "consolidated_bibliographic",
                    "consolidated_sources_count",
                    "consolidated_at",
                    "web_research",
                ],
            )
        return

    if stage == "internet_research":
        if book_object_id is not None:
            await kb_repo.collection.delete_many(
                {"$or": [{"book_id": book_object_id}, {"submission_id": submission_object_id}]}
            )
            await _delete_articles_and_drafts(
                article_repo=article_repo,
                submission_object_id=submission_object_id,
                book_object_id=book_object_id,
            )
            await _clear_book_extracted_keys(
                book_repo=book_repo,
                book_doc=book_doc,
                keys=["web_research"],
            )
        return

    if stage == "context_generation":
        if book_object_id is not None:
            await kb_repo.collection.delete_many(
                {"$or": [{"book_id": book_object_id}, {"submission_id": submission_object_id}]}
            )
            await _delete_articles_and_drafts(
                article_repo=article_repo,
                submission_object_id=submission_object_id,
                book_object_id=book_object_id,
            )
        else:
            await kb_repo.collection.delete_many({"submission_id": submission_object_id})
            await _delete_articles_and_drafts(
                article_repo=article_repo,
                submission_object_id=submission_object_id,
            )
        return

    if stage == "article_generation":
        await _delete_articles_and_drafts(
            article_repo=article_repo,
            submission_object_id=submission_object_id,
            book_object_id=book_object_id,
        )
        return

    await repo.update_fields(
        str(submission_object_id),
        {"errors": []},
    )


async def _enqueue_stage_retry(submission_id: str, stage: str, amazon_url: str) -> None:
    if stage == "amazon_scrape":
        from src.workers.scraper_tasks import scrape_amazon_task

        scrape_amazon_task.delay(submission_id=submission_id, amazon_url=amazon_url)
        return

    if stage in {"additional_links_scrape", "summarize_additional_links"}:
        from src.workers.scraper_tasks import process_additional_links_task

        process_additional_links_task.delay(submission_id=submission_id)
        return

    if stage == "consolidate_book_data":
        from src.workers.scraper_tasks import consolidate_bibliographic_task

        consolidate_bibliographic_task.delay(submission_id=submission_id)
        return

    if stage == "internet_research":
        from src.workers.scraper_tasks import internet_research_task

        internet_research_task.delay(submission_id=submission_id)
        return

    if stage == "context_generation":
        from src.workers.scraper_tasks import generate_context_task

        generate_context_task.delay(submission_id=submission_id)
        return

    if stage == "article_generation":
        from src.workers.article_tasks import generate_article_task

        generate_article_task.delay(submission_id=submission_id)
        return

    raise ValueError(f"Unsupported stage for retry: {stage}")


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


def _sanitize_for_response(value: Any) -> Any:
    """Recursively convert non-JSON-native values (e.g., ObjectId) for API responses."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, dict):
        return {key: _sanitize_for_response(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_response(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_for_response(item) for item in value)
    return value


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
    summary_repo: SummaryRepository = Depends(get_summary_repo),
    kb_repo: KnowledgeBaseRepository = Depends(get_knowledge_base_repo),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Submission not found: {submission_id}")

    book = await book_repo.get_by_submission(submission_id)
    summaries = await summary_repo.get_by_book(str(book["_id"])) if book else []
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

    summaries_data = [
        {
            "id": str(item.get("_id")),
            "source_url": item.get("source_url"),
            "source_domain": item.get("source_domain"),
            "summary_text": item.get("summary_text"),
            "topics": item.get("topics", []),
            "key_points": item.get("key_points", []),
            "credibility": item.get("credibility"),
            "bibliographic_data": item.get("bibliographic_data"),
            "created_at": item.get("created_at"),
        }
        for item in summaries
    ]

    response = {
        "submission": _serialize_submission(submission),
        "book": book_data,
        "summaries": summaries_data,
        "knowledge_base": kb if kb else None,
        "article": article_data,
        "draft": draft,
        "progress": _build_progress(submission.get("status")),
    }
    return _sanitize_for_response(response)


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


@router.post("/{submission_id}/retry_step", status_code=status.HTTP_202_ACCEPTED, summary="Retry from specific step")
async def retry_task_from_step(
    submission_id: str,
    payload: Dict[str, Any] = Body(...),
    repo: SubmissionRepository = Depends(get_submission_repo),
    book_repo: BookRepository = Depends(get_book_repo),
    summary_repo: SummaryRepository = Depends(get_summary_repo),
    kb_repo: KnowledgeBaseRepository = Depends(get_knowledge_base_repo),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    stage_raw = payload.get("stage")
    normalized_stage = _normalize_retry_stage(str(stage_raw or ""))
    if not normalized_stage:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid retry stage")

    book = await book_repo.get_by_submission(submission_id)
    if normalized_stage != "amazon_scrape" and not book:
        normalized_stage = "amazon_scrape"

    await _cleanup_from_stage(
        stage=normalized_stage,
        submission_doc=submission,
        book_doc=book,
        repo=repo,
        book_repo=book_repo,
        summary_repo=summary_repo,
        kb_repo=kb_repo,
        article_repo=article_repo,
    )

    status_map = {
        "amazon_scrape": SubmissionStatus.PENDING_SCRAPE,
        "additional_links_scrape": SubmissionStatus.PENDING_CONTEXT,
        "summarize_additional_links": SubmissionStatus.PENDING_CONTEXT,
        "consolidate_book_data": SubmissionStatus.PENDING_CONTEXT,
        "internet_research": SubmissionStatus.PENDING_CONTEXT,
        "context_generation": SubmissionStatus.CONTEXT_GENERATION,
        "article_generation": SubmissionStatus.PENDING_ARTICLE,
    }
    await repo.update_status(
        submission_id,
        status_map[normalized_stage],
        {
            "current_step": normalized_stage,
            "errors": [],
        },
    )

    amazon_url = str(submission.get("amazon_url") or "")
    if not amazon_url:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Submission amazon_url is required")

    try:
        await _enqueue_stage_retry(
            submission_id=submission_id,
            stage=normalized_stage,
            amazon_url=amazon_url,
        )
    except Exception as e:
        logger.error("Failed to enqueue retry from step '%s': %s", normalized_stage, e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue step retry")

    return {
        "status": "queued",
        "task": "retry_step",
        "submission_id": submission_id,
        "stage": normalized_stage,
    }


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete submission task")
async def delete_task(
    submission_id: str,
    repo: SubmissionRepository = Depends(get_submission_repo),
    book_repo: BookRepository = Depends(get_book_repo),
    summary_repo: SummaryRepository = Depends(get_summary_repo),
    kb_repo: KnowledgeBaseRepository = Depends(get_knowledge_base_repo),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    submission = await repo.get_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    submission_object_id = submission.get("_id")
    book = await book_repo.get_by_submission(submission_id)
    book_object_id = book.get("_id") if book else None

    article_ids = []
    if book_object_id:
        by_book = await article_repo.collection.find({"book_id": book_object_id}, {"_id": 1}).to_list(length=None)
        article_ids.extend([item.get("_id") for item in by_book if item.get("_id")])

    by_submission = await article_repo.collection.find(
        {"submission_id": submission_object_id},
        {"_id": 1},
    ).to_list(length=None)
    article_ids.extend([item.get("_id") for item in by_submission if item.get("_id")])

    dedup_article_ids = list({item for item in article_ids if item is not None})
    if dedup_article_ids:
        await article_repo.drafts_collection.delete_many({"article_id": {"$in": dedup_article_ids}})

    if book_object_id:
        await summary_repo.collection.delete_many({"book_id": book_object_id})
        await kb_repo.collection.delete_many(
            {
                "$or": [
                    {"book_id": book_object_id},
                    {"submission_id": submission_object_id},
                ]
            }
        )
        await article_repo.collection.delete_many(
            {
                "$or": [
                    {"book_id": book_object_id},
                    {"submission_id": submission_object_id},
                ]
            }
        )
        await book_repo.collection.delete_one({"_id": book_object_id})
    else:
        await kb_repo.collection.delete_many({"submission_id": submission_object_id})
        await article_repo.collection.delete_many({"submission_id": submission_object_id})

    deleted = await repo.delete(submission_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    return {}


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
