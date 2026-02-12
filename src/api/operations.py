"""Operational endpoints (stats/health aliases)."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_submission_repo
from src.db.repositories import SubmissionRepository

router = APIRouter(tags=["Operations"])


@router.get("/stats")
async def stats(repo: SubmissionRepository = Depends(get_submission_repo)):
    return await repo.stats()
