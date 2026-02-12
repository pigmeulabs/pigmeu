"""
Book submission ingest API endpoints.

This module handles creation and management of book review submission tasks.
Users submit book information via POST /submit, which creates a task
that flows through the processing pipeline.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from src.models.schemas import SubmissionCreate, SubmissionResponse
from src.models.enums import SubmissionStatus
from src.db.repositories import SubmissionRepository
from src.api.dependencies import get_submission_repo
import logging
from src.workers.worker import start_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submit", tags=["Submissions"])


@router.post(
    "",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new book for review",
    description="Create a new book submission task. System will extract metadata and generate review article.",
)
async def submit_book(
    submission: SubmissionCreate,
    repo: SubmissionRepository = Depends(get_submission_repo),
) -> SubmissionResponse:
    """Submit a new book for review processing."""

    try:
        logger.info("Checking for duplicate submission: %s", submission.amazon_url)
        duplicate_id = await repo.check_duplicate(str(submission.amazon_url))

        if duplicate_id:
            logger.warning("Duplicate submission found: %s", duplicate_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book already submitted: {duplicate_id}. Check status or contact support.",
            )

        logger.info("Creating submission: %s by %s", submission.title, submission.author_name)
        submission_id = await repo.create(
            title=submission.title,
            author_name=submission.author_name,
            amazon_url=submission.amazon_url,
            goodreads_url=submission.goodreads_url,
            author_site=submission.author_site,
            other_links=submission.other_links,
            textual_information=submission.textual_information,
            run_immediately=submission.run_immediately,
            schedule_execution=submission.schedule_execution,
            main_category=submission.main_category,
            article_status=submission.article_status,
            user_approval_required=submission.user_approval_required,
        )

        doc = await repo.get_by_id(submission_id)

        if submission.run_immediately:
            try:
                logger.info("Enqueueing scraping pipeline for: %s", submission_id)
                start_pipeline.delay(submission_id=submission_id, amazon_url=str(submission.amazon_url))
            except Exception:
                logger.exception("Failed to enqueue scraping pipeline")

        return SubmissionResponse(
            id=str(doc["_id"]),
            title=doc["title"],
            author_name=doc["author_name"],
            amazon_url=doc["amazon_url"],
            goodreads_url=doc.get("goodreads_url"),
            author_site=doc.get("author_site"),
            other_links=doc.get("other_links", []),
            textual_information=doc.get("textual_information"),
            run_immediately=doc.get("run_immediately", True),
            schedule_execution=doc.get("schedule_execution"),
            main_category=doc.get("main_category"),
            article_status=doc.get("article_status"),
            user_approval_required=doc.get("user_approval_required", False),
            status=SubmissionStatus(doc["status"]),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating submission: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create submission. Please try again.",
        )


@router.get(
    "/health",
    tags=["Health"],
    summary="Check submission endpoint health",
)
async def submit_health():
    return {"status": "ok", "endpoint": "submit"}
