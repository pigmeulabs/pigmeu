"""
Book submission ingest API endpoints.

This module handles creation and management of book review submission tasks.
Users submit book information via POST /submit, which creates a task
that flows through the processing pipeline.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
from datetime import datetime
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
    """Submit a new book for review processing.
    
    This endpoint:
    1. Validates book information (title, author, URLs)
    2. Checks for duplicates (same Amazon URL)
    3. Creates submission document in database
    4. Returns submission with pending_scrape status
    
    The submission will be picked up by a worker for:
    - Scraping Amazon metadata
    - Extracting book information
    - Generating context from multiple sources
    - Creating article
    
    Args:
        submission: Submission data (title, author, links)
        repo: SubmissionRepository (injected)
    
    Returns:
        SubmissionResponse with submission_id and status
    
    Raises:
        HTTPException 400: If duplicate book found
        HTTPException 500: If database error occurs
    
    Example:
        POST /submit
        {
            "title": "Designing Data-Intensive Applications",
            "author_name": "Martin Kleppmann",
            "amazon_url": "https://amazon.com/...",
            "goodreads_url": "https://goodreads.com/...",
            "author_site": "https://martin.kleppmann.com"
        }
    """
    
    try:
        # Check for duplicate submissions (same Amazon URL)
        logger.info(f"Checking for duplicate submission: {submission.amazon_url}")
        duplicate_id = await repo.check_duplicate(str(submission.amazon_url))
        
        if duplicate_id:
            logger.warning(f"Duplicate submission found: {duplicate_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book already submitted: {duplicate_id}. Check status or contact support.",
            )
        
        # Create submission
        logger.info(f"Creating submission: {submission.title} by {submission.author_name}")
        submission_id = await repo.create(
            title=submission.title,
            author_name=submission.author_name,
            amazon_url=submission.amazon_url,
            goodreads_url=submission.goodreads_url,
            author_site=submission.author_site,
            other_links=submission.other_links,
        )
        
        logger.info(f"✓ Submission created: {submission_id}")
        
        # Fetch created document
        doc = await repo.get_by_id(submission_id)
        
        # Trigger background processing pipeline (Celery)
        try:
            logger.info(f"Enqueueing scraping pipeline for: {submission_id}")
            # Use Celery task to start the pipeline so the request returns quickly
            start_pipeline.delay(submission_id=submission_id, amazon_url=str(submission.amazon_url))
        except Exception:
            logger.exception("Failed to enqueue scraping pipeline")

        # Convert to response model
        return SubmissionResponse(
            id=str(doc["_id"]),
            title=doc["title"],
            author_name=doc["author_name"],
            amazon_url=doc["amazon_url"],
            goodreads_url=doc.get("goodreads_url"),
            author_site=doc.get("author_site"),
            other_links=doc.get("other_links", []),
            status=SubmissionStatus(doc["status"]),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Error creating submission: {str(e)}", exc_info=True)
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
    """Health check for submit endpoint.
    
    Returns:
        Status message
    """
    return {"status": "ok", "endpoint": "submit"}
