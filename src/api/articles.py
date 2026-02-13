"""Article editing endpoints."""

from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Body, status

from src.api.dependencies import get_article_repo, get_submission_repo
from src.db.repositories import ArticleRepository, SubmissionRepository
from src.models.enums import ArticleStatus

router = APIRouter(prefix="/articles", tags=["Articles"])

@router.patch("/{article_id}", status_code=status.HTTP_200_OK)
async def update_article(
    article_id: str,
    payload: Dict[str, Any] = Body(...),
    repo: ArticleRepository = Depends(get_article_repo),
):
    article = await repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    allowed_fields = {
        "title",
        "content",
        "status",
        "validation_report",
        "wordpress_post_id",
        "wordpress_url",
    }
    update_data = {k: v for k, v in payload.items() if k in allowed_fields}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid fields provided for update",
        )

    await repo.update(article_id, update_data)
    updated = await repo.get_by_id(article_id)

    return {
        "id": str(updated.get("_id")),
        "book_id": str(updated.get("book_id")),
        "submission_id": str(updated.get("submission_id")) if updated.get("submission_id") else None,
        "title": updated.get("title"),
        "content": updated.get("content"),
        "status": updated.get("status"),
        "word_count": updated.get("word_count"),
        "updated_at": updated.get("updated_at"),
    }

@router.post("/{article_id}/approve", status_code=status.HTTP_200_OK, summary="Approve an article")
async def approve_article(
    article_id: str,
    repo: ArticleRepository = Depends(get_article_repo),
    submission_repo: SubmissionRepository = Depends(get_submission_repo),
):
    """
    Approve an article for publication.

    This endpoint transitions an article from 'in_review' or 'draft' status to 'approved'.
    If the article is associated with a submission, it also updates the submission status.
    """
    article = await repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    current_status = article.get("status")
    if current_status not in [ArticleStatus.IN_REVIEW.value, ArticleStatus.DRAFT.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article must be in '{ArticleStatus.IN_REVIEW.value}' or '{ArticleStatus.DRAFT.value}' status to approve"
        )

    # Update article status to approved
    await repo.update(article_id, {
        "status": ArticleStatus.APPROVED.value,
        "approved_at": datetime.utcnow()
    })

    # Update submission status if applicable
    submission_id = article.get("submission_id")
    if submission_id:
        await submission_repo.update_status(
            submission_id,
            "approved",
            {"current_step": "approved"}
        )

    updated_article = await repo.get_by_id(article_id)
    return {
        "status": "approved",
        "article_id": article_id,
        "new_status": updated_article.get("status"),
        "approved_at": updated_article.get("approved_at"),
        "submission_id": str(submission_id) if submission_id else None
    }

@router.post("/{article_id}/reject", status_code=status.HTTP_200_OK, summary="Reject an article")
async def reject_article(
    article_id: str,
    payload: Dict[str, Any] = Body(...),
    repo: ArticleRepository = Depends(get_article_repo),
):
    """
    Reject an article and send it back for revision.

    This endpoint transitions an article from 'in_review' or 'approved' status back to 'draft'
    with optional feedback for the author.
    """
    article = await repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    feedback = payload.get("feedback", "")
    if feedback and not isinstance(feedback, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Feedback must be a string"
        )

    current_status = article.get("status")
    if current_status not in [ArticleStatus.IN_REVIEW.value, ArticleStatus.APPROVED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article must be in '{ArticleStatus.IN_REVIEW.value}' or '{ArticleStatus.APPROVED.value}' status to reject"
        )

    # Update article status back to draft with rejection feedback
    update_data = {
        "status": ArticleStatus.DRAFT.value,
        "rejection_feedback": feedback,
        "rejection_timestamp": datetime.utcnow()
    }

    await repo.update(article_id, update_data)

    updated_article = await repo.get_by_id(article_id)
    return {
        "status": "rejected",
        "article_id": article_id,
        "new_status": updated_article.get("status"),
        "feedback": feedback,
        "rejected_at": updated_article.get("rejection_timestamp")
    }
