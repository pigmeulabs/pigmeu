"""
Task management API endpoints.

This module provides endpoints for viewing and managing submission tasks.
Users can list their submissions and view detailed progress information.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional, List
from src.models.schemas import SubmissionResponse
from src.models.enums import SubmissionStatus
from src.db.repositories import SubmissionRepository, BookRepository
from src.api.dependencies import get_submission_repo, get_book_repo
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "",
    response_model=dict,
    summary="List all submissions",
    description="Get paginated list of all book review submissions.",
)
async def list_tasks(
    skip: int = Query(0, ge=0, description="Skip first N tasks"),
    limit: int = Query(20, ge=1, le=100, description="Max tasks to return"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    repo: SubmissionRepository = Depends(get_submission_repo),
):
    """List all submission tasks with pagination and filtering.
    
    This endpoint:
    1. Returns paginated list of submissions
    2. Optionally filters by status (pending_scrape, scraped, etc.)
    3. Returns total count for pagination UI
    
    Args:
        skip: Number of tasks to skip (default: 0)
        limit: Max tasks to return (default: 20, max: 100)
        status: Filter by status (optional)
        repo: SubmissionRepository (injected)
    
    Returns:
        Dict with tasks list and pagination info
    
    Example:
        GET /tasks?skip=0&limit=20
        GET /tasks?status=pending_scrape&limit=10
    """
    
    try:
        logger.info(f"Listing tasks: skip={skip}, limit={limit}, status={status}")
        
        # Fetch tasks
        submissions, total = await repo.list_all(
            skip=skip,
            limit=limit,
            status=status_filter,
        )
        
        # Convert to response models
        tasks = [
            SubmissionResponse(
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
            for doc in submissions
        ]
        
        logger.info(f"✓ Returned {len(tasks)} tasks (total: {total})")
        
        return {
            "tasks": tasks,
            "total": total,
            "skip": skip,
            "limit": limit,
            "count": len(tasks),
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing tasks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tasks. Please try again.",
        )


@router.get(
    "/health",
    tags=["Health"],
    summary="Check tasks endpoint health",
)
async def tasks_health():
    """Health check for tasks endpoint.
    
    Returns:
        Status message
    """
    return {"status": "ok", "endpoint": "tasks"}


@router.get(
    "/{submission_id}",
    response_model=dict,
    summary="Get submission details",
    description="Get detailed information about a specific submission including extracted data.",
)
async def get_task(
    submission_id: str,
    repo: SubmissionRepository = Depends(get_submission_repo),
    book_repo: BookRepository = Depends(get_book_repo),
):
    """Get detailed information about a specific submission.
    
    This endpoint returns:
    1. Submission metadata (title, author, links)
    2. Extraction status and progress
    3. Extracted book metadata (if available)
    4. Current processing stage
    
    Args:
        submission_id: Submission ObjectId as string
        repo: SubmissionRepository (injected)
        book_repo: BookRepository (injected)
    
    Returns:
        Dict with submission details and extracted data
    
    Raises:
        HTTPException 404: If submission not found
        HTTPException 500: If database error occurs
    
    Example:
        GET /tasks/507f1f77bcf86cd799439011
    """
    
    try:
        logger.info(f"Getting task details: {submission_id}")
        
        # Fetch submission
        submission = await repo.get_by_id(submission_id)
        
        if not submission:
            logger.warning(f"Submission not found: {submission_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission not found: {submission_id}",
            )
        
        # Build response
        response = {
            "submission": SubmissionResponse(
                id=str(submission["_id"]),
                title=submission["title"],
                author_name=submission["author_name"],
                amazon_url=submission["amazon_url"],
                goodreads_url=submission.get("goodreads_url"),
                author_site=submission.get("author_site"),
                other_links=submission.get("other_links", []),
                status=SubmissionStatus(submission["status"]),
                created_at=submission["created_at"],
                updated_at=submission["updated_at"],
            ),
            "book": None,
            "progress": {
                "current_stage": submission["status"],
                "steps": [
                    {
                        "stage": "pending_scrape",
                        "label": "Scraping metadata...",
                        "completed": submission["status"] in [
                            "scraped",
                            "pending_context",
                            "context_generated",
                            "pending_article",
                            "article_generated",
                            "ready_for_review",
                            "approved",
                            "published",
                        ],
                    },
                    {
                        "stage": "pending_context",
                        "label": "Generating context...",
                        "completed": submission["status"] in [
                            "context_generated",
                            "pending_article",
                            "article_generated",
                            "ready_for_review",
                            "approved",
                            "published",
                        ],
                    },
                    {
                        "stage": "pending_article",
                        "label": "Creating article...",
                        "completed": submission["status"] in [
                            "article_generated",
                            "ready_for_review",
                            "approved",
                            "published",
                        ],
                    },
                    {
                        "stage": "ready_for_review",
                        "label": "Ready for review",
                        "completed": submission["status"] in [
                            "approved",
                            "published",
                        ],
                    },
                ],
            },
        }
        
        # Try to fetch associated book
        book = await book_repo.get_by_submission(submission_id)
        if book:
            response["book"] = {
                "id": str(book["_id"]),
                "extracted": book.get("extracted", {}),
                "last_updated": book["last_updated"],
            }
        
        logger.info(f"✓ Returned task details: {submission_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task. Please try again.",
        )



@router.patch("/{submission_id}", response_model=dict, summary="Update submission or book fields")
async def update_task(
    submission_id: str,
    payload: dict,
    repo: SubmissionRepository = Depends(get_submission_repo),
    book_repo: BookRepository = Depends(get_book_repo),
):
    """Update submission metadata or book extracted fields.

    Payload example:
    { "submission": {"title": "..."}, "book": {"extracted": {...}} }
    """
    try:
        updated = False
        if "submission" in payload:
            updated = await repo.update_fields(submission_id, payload["submission"]) or updated

        if "book" in payload and payload["book"]:
            # use create_or_update to upsert book extracted data
            extracted = payload["book"].get("extracted") or {}
            await book_repo.create_or_update(submission_id=submission_id, extracted=extracted)
            updated = True

        if not updated:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid fields to update")

        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating task: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update task")


@router.post("/{submission_id}/generate_context", response_model=dict, summary="Trigger context generation")
async def trigger_context_generation(
    submission_id: str,
):
    """Enqueue background context generation task for this submission."""
    try:
        # import Celery task lazily
        from src.workers.scraper_tasks import generate_context_task

        generate_context_task.delay(submission_id=submission_id)
        return {"status": "enqueued"}
    except Exception as e:
        logger.error(f"❌ Error enqueuing context generation: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to enqueue context generation")


@router.post("/{submission_id}/generate_article", response_model=dict, summary="Trigger article generation")
async def trigger_article_generation(
    submission_id: str,
):
    """Enqueue background article generation task for this submission."""
    try:
        from src.workers.scraper_tasks import generate_article_task

        generate_article_task.delay(submission_id=submission_id)
        return {"status": "enqueued"}
    except Exception as e:
        logger.error(f"❌ Error enqueuing article generation: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to enqueue article generation")


