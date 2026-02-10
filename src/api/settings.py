"""
Settings API: manage credentials and prompt templates.

Endpoints:
- GET /settings/credentials
- POST /settings/credentials
- GET /settings/prompts
- POST /settings/prompts
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.api.dependencies import get_credential_repo, get_prompt_repo
from src.models.schemas import CredentialCreate, PromptCreate, PromptResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/credentials", response_model=List[dict])
async def list_credentials(repo = Depends(get_credential_repo)):
    try:
        items = await repo.list_all()
        # Mask keys for safety in responses
        for i in items:
            if i.get("key"):
                i["key"] = i["key"][:4] + "..." + i["key"][-4:]
        return items
    except Exception as e:
        logger.error(f"Error listing credentials: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/credentials", status_code=status.HTTP_201_CREATED)
async def create_credential(payload: CredentialCreate, repo = Depends(get_credential_repo)):
    try:
        cid = await repo.create(service=payload.service.value, key=payload.key, encrypted=payload.encrypted)
        return {"id": cid, "service": payload.service.value}
    except Exception as e:
        logger.error(f"Error creating credential: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/prompts", response_model=List[PromptResponse])
async def list_prompts(repo = Depends(get_prompt_repo)):
    try:
        items = await repo.list_all()
        results = []
        for d in items:
            results.append(PromptResponse(
                id=str(d.get("_id")),
                name=d.get("name"),
                purpose=d.get("purpose"),
                system_prompt=d.get("system_prompt"),
                user_prompt=d.get("user_prompt"),
                model_id=d.get("model_id"),
                temperature=d.get("temperature", 0.7),
                max_tokens=d.get("max_tokens", 2000),
                schema_example=d.get("schema_example"),
                created_at=d.get("created_at"),
            ))
        return results
    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str, repo = Depends(get_prompt_repo)):
    try:
        doc = await repo.get_by_id(prompt_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return PromptResponse(
            id=str(doc.get("_id")),
            name=doc.get("name"),
            purpose=doc.get("purpose"),
            system_prompt=doc.get("system_prompt"),
            user_prompt=doc.get("user_prompt"),
            model_id=doc.get("model_id"),
            temperature=doc.get("temperature", 0.7),
            max_tokens=doc.get("max_tokens", 2000),
            schema_example=doc.get("schema_example"),
            created_at=doc.get("created_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prompt: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/prompts", status_code=status.HTTP_201_CREATED, response_model=PromptResponse)
async def create_prompt(payload: PromptCreate, repo = Depends(get_prompt_repo)):
    try:
        pid = await repo.create(payload.dict())
        doc = await repo.get_by_id(pid)
        return PromptResponse(
            id=str(doc.get("_id")),
            name=doc.get("name"),
            purpose=doc.get("purpose"),
            system_prompt=doc.get("system_prompt"),
            user_prompt=doc.get("user_prompt"),
            model_id=doc.get("model_id"),
            temperature=doc.get("temperature", 0.7),
            max_tokens=doc.get("max_tokens", 2000),
            schema_example=doc.get("schema_example"),
            created_at=doc.get("created_at"),
        )
    except Exception as e:
        logger.error(f"Error creating prompt: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete("/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(prompt_id: str, repo = Depends(get_prompt_repo)):
    try:
        ok = await repo.delete(prompt_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting prompt: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete("/credentials/{cred_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(cred_id: str, repo = Depends(get_credential_repo)):
    try:
        ok = await repo.delete(cred_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting credential: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
