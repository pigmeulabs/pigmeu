"""Article editing endpoints."""

from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Body, status

from src.api.dependencies import get_article_repo
from src.db.repositories import ArticleRepository

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
