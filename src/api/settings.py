"""
Settings API: manage credentials and prompt templates.

Endpoints:
- GET/POST/PATCH/DELETE /settings/credentials
- GET/POST/PATCH/DELETE /settings/prompts
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.api.dependencies import get_credential_repo, get_prompt_repo
from src.models.schemas import (
    CredentialCreate,
    CredentialUpdate,
    PromptCreate,
    PromptUpdate,
    PromptResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


def _mask_credential(doc: dict) -> dict:
    item = {**doc}
    item["id"] = str(item.get("_id"))
    item.pop("_id", None)

    key = item.get("key")
    if isinstance(key, str) and len(key) > 8:
        item["key"] = key[:4] + "..." + key[-4:]
    elif isinstance(key, str):
        item["key"] = "****"

    return item


@router.get("/credentials", response_model=List[dict])
async def list_credentials(
    service: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    repo=Depends(get_credential_repo),
):
    try:
        if active is True:
            items = await repo.list_active(service=service)
        else:
            items = await repo.list_all()
            if service:
                items = [item for item in items if item.get("service") == service]
            if active is not None:
                items = [item for item in items if bool(item.get("active", True)) is active]

        return [_mask_credential(item) for item in items]
    except Exception as e:
        logger.error("Error listing credentials: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/credentials/{cred_id}", response_model=dict)
async def get_credential(cred_id: str, repo=Depends(get_credential_repo)):
    doc = await repo.get_by_id(cred_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
    return _mask_credential(doc)


@router.post("/credentials", status_code=status.HTTP_201_CREATED)
async def create_credential(payload: CredentialCreate, repo=Depends(get_credential_repo)):
    try:
        cid = await repo.create(
            service=payload.service.value,
            key=payload.key,
            encrypted=payload.encrypted,
            name=payload.name,
            username_email=payload.username_email,
            active=payload.active,
        )
        return {"id": cid, "service": payload.service.value}
    except Exception as e:
        logger.error("Error creating credential: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.patch("/credentials/{cred_id}", status_code=status.HTTP_200_OK)
async def update_credential(cred_id: str, payload: CredentialUpdate, repo=Depends(get_credential_repo)):
    existing = await repo.get_by_id(cred_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")

    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")

    ok = await repo.update(cred_id, update_data)
    if not ok:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update credential")

    updated = await repo.get_by_id(cred_id)
    return _mask_credential(updated)


@router.delete("/credentials/{cred_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(cred_id: str, repo=Depends(get_credential_repo)):
    try:
        ok = await repo.delete(cred_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting credential: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/prompts", response_model=List[PromptResponse])
async def list_prompts(
    active: Optional[bool] = Query(None),
    purpose: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    repo=Depends(get_prompt_repo),
):
    try:
        items = await repo.list_all(active=active, purpose=purpose, search=search)
        return [
            PromptResponse(
                id=str(d.get("_id")),
                name=d.get("name"),
                purpose=d.get("purpose"),
                short_description=d.get("short_description"),
                system_prompt=d.get("system_prompt"),
                user_prompt=d.get("user_prompt"),
                model_id=d.get("model_id"),
                temperature=d.get("temperature", 0.7),
                max_tokens=d.get("max_tokens", 2000),
                schema_example=d.get("schema_example"),
                active=d.get("active", True),
                created_at=d.get("created_at"),
                updated_at=d.get("updated_at"),
            )
            for d in items
        ]
    except Exception as e:
        logger.error("Error listing prompts: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str, repo=Depends(get_prompt_repo)):
    try:
        doc = await repo.get_by_id(prompt_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return PromptResponse(
            id=str(doc.get("_id")),
            name=doc.get("name"),
            purpose=doc.get("purpose"),
            short_description=doc.get("short_description"),
            system_prompt=doc.get("system_prompt"),
            user_prompt=doc.get("user_prompt"),
            model_id=doc.get("model_id"),
            temperature=doc.get("temperature", 0.7),
            max_tokens=doc.get("max_tokens", 2000),
            schema_example=doc.get("schema_example"),
            active=doc.get("active", True),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching prompt: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/prompts", status_code=status.HTTP_201_CREATED, response_model=PromptResponse)
async def create_prompt(payload: PromptCreate, repo=Depends(get_prompt_repo)):
    try:
        pid = await repo.create(payload.model_dump())
        doc = await repo.get_by_id(pid)
        return PromptResponse(
            id=str(doc.get("_id")),
            name=doc.get("name"),
            purpose=doc.get("purpose"),
            short_description=doc.get("short_description"),
            system_prompt=doc.get("system_prompt"),
            user_prompt=doc.get("user_prompt"),
            model_id=doc.get("model_id"),
            temperature=doc.get("temperature", 0.7),
            max_tokens=doc.get("max_tokens", 2000),
            schema_example=doc.get("schema_example"),
            active=doc.get("active", True),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        )
    except Exception as e:
        logger.error("Error creating prompt: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.patch("/prompts/{prompt_id}", response_model=PromptResponse)
async def update_prompt(prompt_id: str, payload: PromptUpdate, repo=Depends(get_prompt_repo)):
    existing = await repo.get_by_id(prompt_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")

    ok = await repo.update(prompt_id, update_data)
    if not ok:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update prompt")

    doc = await repo.get_by_id(prompt_id)
    return PromptResponse(
        id=str(doc.get("_id")),
        name=doc.get("name"),
        purpose=doc.get("purpose"),
        short_description=doc.get("short_description"),
        system_prompt=doc.get("system_prompt"),
        user_prompt=doc.get("user_prompt"),
        model_id=doc.get("model_id"),
        temperature=doc.get("temperature", 0.7),
        max_tokens=doc.get("max_tokens", 2000),
        schema_example=doc.get("schema_example"),
        active=doc.get("active", True),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


@router.delete("/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(prompt_id: str, repo=Depends(get_prompt_repo)):
    try:
        ok = await repo.delete(prompt_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting prompt: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
