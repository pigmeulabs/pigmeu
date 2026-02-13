"""
Settings API: manage credentials and prompt templates.

Endpoints:
- GET/POST/PATCH/DELETE /settings/credentials
- GET/POST/PATCH/DELETE /settings/prompts
- GET/PATCH /settings/pipelines
"""

import logging
from copy import deepcopy
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body

from src.api.dependencies import get_credential_repo, get_prompt_repo, get_pipeline_repo
from src.models.schemas import (
    CredentialCreate,
    CredentialUpdate,
    PromptCreate,
    PromptUpdate,
    PromptResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


BOOK_REVIEW_PIPELINE_ID = "book_review_v2"

BOOK_REVIEW_PIPELINE_TEMPLATE: Dict[str, Any] = {
    "name": "Book Review",
    "slug": "book-review",
    "description": "Pipeline para extracao de dados, consolidacao de contexto e geracao de conteudo de Book Review.",
    "usage_type": "content_copilot",
    "version": "2.0",
    "steps": [
        {
            "id": "amazon_scrape",
            "name": "Amazon link scrape",
            "description": "Extrai metadados bibliograficos da pagina do livro na Amazon.",
            "type": "scraping",
            "uses_ai": False,
            "delay_seconds": 0,
        },
        {
            "id": "additional_links_scrape",
            "name": "Additional links scrape",
            "description": "Processa links adicionais e extrai dados bibliograficos via IA.",
            "type": "scraping+llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": "mistral",
                "model_id": "mistral-large-latest",
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "Mistral A",
                "default_prompt_purpose": "book_review_link_bibliography_extract",
            },
        },
        {
            "id": "summarize_additional_links",
            "name": "Summarize additional links",
            "description": "Gera resumo dos links adicionais com foco em livro e autor.",
            "type": "llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": "groq",
                "model_id": "llama-3.3-70b-versatile",
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "GROC A",
                "default_prompt_purpose": "book_review_link_summary",
            },
        },
        {
            "id": "consolidate_book_data",
            "name": "Consolidate book data",
            "description": "Consolida dados bibliograficos sem duplicidade.",
            "type": "data-processing",
            "uses_ai": False,
            "delay_seconds": 0,
        },
        {
            "id": "internet_research",
            "name": "Internet research",
            "description": "Pesquisa web sobre livro/autor e sintetiza assuntos e temas.",
            "type": "search+llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": "groq",
                "model_id": "llama-3.3-70b-versatile",
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "GROC A",
                "default_prompt_purpose": "book_review_web_research",
            },
        },
        {
            "id": "context_generation",
            "name": "Generate context",
            "description": "Gera base de conhecimento consolidada para suportar a escrita.",
            "type": "llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": "openai",
                "model_id": "gpt-4o-mini",
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": None,
                "default_prompt_purpose": "context",
            },
        },
        {
            "id": "article_generation",
            "name": "Generate article",
            "description": "Gera artigo final em markdown a partir do contexto produzido.",
            "type": "llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": "openai",
                "model_id": "gpt-4o-mini",
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": None,
                "default_prompt_purpose": "article",
            },
        },
        {
            "id": "ready_for_review",
            "name": "Ready for review",
            "description": "Etapa final de aprovacao para revisao/publicacao.",
            "type": "workflow",
            "uses_ai": False,
            "delay_seconds": 0,
        },
    ],
}


def _pipeline_card_response(doc: Dict[str, Any]) -> Dict[str, Any]:
    steps = doc.get("steps", []) if isinstance(doc.get("steps"), list) else []
    ai_steps = [step for step in steps if bool(step.get("uses_ai"))]
    return {
        "id": doc.get("pipeline_id"),
        "name": doc.get("name"),
        "slug": doc.get("slug"),
        "description": doc.get("description"),
        "usage_type": doc.get("usage_type"),
        "version": doc.get("version"),
        "steps_count": len(steps),
        "ai_steps_count": len(ai_steps),
    }


def _credential_option(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id")),
        "name": doc.get("name"),
        "service": doc.get("service"),
        "active": bool(doc.get("active", True)),
    }


def _prompt_option(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id")),
        "name": doc.get("name"),
        "purpose": doc.get("purpose"),
        "model_id": doc.get("model_id"),
        "active": bool(doc.get("active", True)),
    }


def _safe_delay_seconds(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


async def _ensure_book_review_pipeline(pipeline_repo) -> Dict[str, Any]:
    doc = await pipeline_repo.get_by_pipeline_id(BOOK_REVIEW_PIPELINE_ID)
    if doc:
        return doc

    await pipeline_repo.create_or_update(
        BOOK_REVIEW_PIPELINE_ID,
        deepcopy(BOOK_REVIEW_PIPELINE_TEMPLATE),
    )
    created = await pipeline_repo.get_by_pipeline_id(BOOK_REVIEW_PIPELINE_ID)
    return created if created else {"pipeline_id": BOOK_REVIEW_PIPELINE_ID, **deepcopy(BOOK_REVIEW_PIPELINE_TEMPLATE)}


async def _build_pipeline_detail_response(
    pipeline_doc: Dict[str, Any],
    credential_repo,
    prompt_repo,
) -> Dict[str, Any]:
    credentials = await credential_repo.list_all()
    prompts = await prompt_repo.list_all(limit=300)

    credential_options = [_credential_option(item) for item in credentials]
    prompt_options = [_prompt_option(item) for item in prompts]
    cred_by_id = {item["id"]: item for item in credential_options}
    prompt_by_id = {item["id"]: item for item in prompt_options}

    steps: List[Dict[str, Any]] = []
    raw_steps = pipeline_doc.get("steps", []) if isinstance(pipeline_doc.get("steps"), list) else []
    for item in raw_steps:
        step = {
            "id": item.get("id"),
            "name": item.get("name"),
            "description": item.get("description"),
            "type": item.get("type"),
            "uses_ai": bool(item.get("uses_ai")),
            "delay_seconds": _safe_delay_seconds(item.get("delay_seconds", 0)),
        }

        if step["uses_ai"]:
            ai = item.get("ai", {}) if isinstance(item.get("ai"), dict) else {}
            selected_credential = cred_by_id.get(str(ai.get("credential_id") or ""))
            selected_prompt = prompt_by_id.get(str(ai.get("prompt_id") or ""))
            step["ai"] = {
                "provider": ai.get("provider"),
                "model_id": ai.get("model_id"),
                "credential_id": str(ai.get("credential_id")) if ai.get("credential_id") else None,
                "credential_name": selected_credential.get("name") if selected_credential else None,
                "credential_service": selected_credential.get("service") if selected_credential else None,
                "prompt_id": str(ai.get("prompt_id")) if ai.get("prompt_id") else None,
                "prompt_name": selected_prompt.get("name") if selected_prompt else None,
                "prompt_purpose": selected_prompt.get("purpose") if selected_prompt else ai.get("default_prompt_purpose"),
                "default_credential_name": ai.get("default_credential_name"),
                "default_prompt_purpose": ai.get("default_prompt_purpose"),
            }

        steps.append(step)

    return {
        "id": pipeline_doc.get("pipeline_id"),
        "name": pipeline_doc.get("name"),
        "slug": pipeline_doc.get("slug"),
        "description": pipeline_doc.get("description"),
        "usage_type": pipeline_doc.get("usage_type"),
        "version": pipeline_doc.get("version"),
        "steps": steps,
        "available_credentials": credential_options,
        "available_prompts": prompt_options,
    }


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


@router.get("/pipelines", response_model=List[dict])
async def list_pipelines(pipeline_repo=Depends(get_pipeline_repo)):
    try:
        await _ensure_book_review_pipeline(pipeline_repo)
        items = await pipeline_repo.list_all()
        return [_pipeline_card_response(item) for item in items]
    except Exception as e:
        logger.error("Error listing pipelines: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list pipelines")


@router.get("/pipelines/{pipeline_id}", response_model=dict)
async def get_pipeline_detail(
    pipeline_id: str,
    pipeline_repo=Depends(get_pipeline_repo),
    credential_repo=Depends(get_credential_repo),
    prompt_repo=Depends(get_prompt_repo),
):
    if pipeline_id != BOOK_REVIEW_PIPELINE_ID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")

    try:
        pipeline_doc = await _ensure_book_review_pipeline(pipeline_repo)
        return await _build_pipeline_detail_response(
            pipeline_doc=pipeline_doc,
            credential_repo=credential_repo,
            prompt_repo=prompt_repo,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error loading pipeline detail: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load pipeline detail")


@router.patch("/pipelines/{pipeline_id}/steps/{step_id}", response_model=dict)
async def update_pipeline_step_ai(
    pipeline_id: str,
    step_id: str,
    payload: Dict[str, Any] = Body(...),
    pipeline_repo=Depends(get_pipeline_repo),
    credential_repo=Depends(get_credential_repo),
    prompt_repo=Depends(get_prompt_repo),
):
    if pipeline_id != BOOK_REVIEW_PIPELINE_ID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")

    update_credential = "credential_id" in payload
    update_prompt = "prompt_id" in payload
    update_delay = "delay_seconds" in payload
    if not update_credential and not update_prompt and not update_delay:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="credential_id, prompt_id or delay_seconds is required",
        )

    pipeline_doc = await _ensure_book_review_pipeline(pipeline_repo)
    steps = pipeline_doc.get("steps", []) if isinstance(pipeline_doc.get("steps"), list) else []
    step = next((item for item in steps if item.get("id") == step_id), None)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline step not found")

    uses_ai = bool(step.get("uses_ai"))
    if (update_credential or update_prompt) and not uses_ai:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="This step does not use AI settings")

    ai = step.get("ai", {}) if isinstance(step.get("ai"), dict) else {}

    if update_credential:
        credential_id = payload.get("credential_id")
        if credential_id in ("", None):
            ai["credential_id"] = None
        else:
            credential = await credential_repo.get_by_id(str(credential_id))
            if not credential:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
            ai["credential_id"] = str(credential.get("_id"))

    if update_prompt:
        prompt_id = payload.get("prompt_id")
        if prompt_id in ("", None):
            ai["prompt_id"] = None
        else:
            prompt = await prompt_repo.get_by_id(str(prompt_id))
            if not prompt:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
            ai["prompt_id"] = str(prompt.get("_id"))

    if uses_ai:
        step["ai"] = ai

    if update_delay:
        raw_delay = payload.get("delay_seconds")
        if raw_delay in (None, ""):
            delay_seconds = 0
        else:
            try:
                delay_seconds = int(raw_delay)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="delay_seconds must be an integer >= 0",
                )
            if delay_seconds < 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="delay_seconds must be >= 0",
                )
            if delay_seconds > 86400:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="delay_seconds must be <= 86400",
                )

        step["delay_seconds"] = delay_seconds

    pipeline_doc["steps"] = steps

    save_payload = {
        "name": pipeline_doc.get("name"),
        "slug": pipeline_doc.get("slug"),
        "description": pipeline_doc.get("description"),
        "usage_type": pipeline_doc.get("usage_type"),
        "version": pipeline_doc.get("version"),
        "steps": steps,
    }
    await pipeline_repo.create_or_update(pipeline_id, save_payload)
    updated_doc = await pipeline_repo.get_by_pipeline_id(pipeline_id)
    if not updated_doc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update pipeline step")

    details = await _build_pipeline_detail_response(
        pipeline_doc=updated_doc,
        credential_repo=credential_repo,
        prompt_repo=prompt_repo,
    )
    updated_step = next((item for item in details.get("steps", []) if item.get("id") == step_id), None)
    return {
        "status": "ok",
        "pipeline_id": pipeline_id,
        "step": updated_step,
    }


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
                expected_output_format=d.get("expected_output_format"),
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
            expected_output_format=doc.get("expected_output_format"),
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
            expected_output_format=doc.get("expected_output_format"),
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
        expected_output_format=doc.get("expected_output_format"),
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
