#!/usr/bin/env python3
"""
Idempotent migration for AI model/provider standardization.

Targets:
- prompts collection
- pipeline_configs collection
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, Tuple

from src.db.connection import close_mongo_client, get_database
from src.workers.ai_defaults import (
    BOOK_REVIEW_ARTICLE_MODEL_ID,
    BOOK_REVIEW_ARTICLE_PROVIDER,
    BOOK_REVIEW_CONTEXT_MODEL_ID,
    BOOK_REVIEW_CONTEXT_PROVIDER,
    MODEL_GROQ_LLAMA_3_3_70B,
    MODEL_MISTRAL_LARGE_LATEST,
    PROVIDER_GROQ,
    PROVIDER_MISTRAL,
)


PROMPT_PURPOSE_RULES: Dict[str, Tuple[str, str]] = {
    "context": (BOOK_REVIEW_CONTEXT_PROVIDER, BOOK_REVIEW_CONTEXT_MODEL_ID),
    "article": (BOOK_REVIEW_ARTICLE_PROVIDER, BOOK_REVIEW_ARTICLE_MODEL_ID),
    "topic_extraction": (PROVIDER_MISTRAL, MODEL_MISTRAL_LARGE_LATEST),
    "book_review_link_bibliography_extract": (PROVIDER_MISTRAL, MODEL_MISTRAL_LARGE_LATEST),
    "book_review_link_summary": (PROVIDER_GROQ, MODEL_GROQ_LLAMA_3_3_70B),
    "book_review_web_research": (PROVIDER_GROQ, MODEL_GROQ_LLAMA_3_3_70B),
}

PIPELINE_STEP_RULES: Dict[str, Tuple[str, str]] = {
    "additional_links_scrape": (PROVIDER_MISTRAL, MODEL_MISTRAL_LARGE_LATEST),
    "summarize_additional_links": (PROVIDER_GROQ, MODEL_GROQ_LLAMA_3_3_70B),
    "internet_research": (PROVIDER_GROQ, MODEL_GROQ_LLAMA_3_3_70B),
    "context_generation": (BOOK_REVIEW_CONTEXT_PROVIDER, BOOK_REVIEW_CONTEXT_MODEL_ID),
    "article_generation": (BOOK_REVIEW_ARTICLE_PROVIDER, BOOK_REVIEW_ARTICLE_MODEL_ID),
    "links_scrape": (PROVIDER_GROQ, MODEL_GROQ_LLAMA_3_3_70B),
    "extract_facts": (PROVIDER_MISTRAL, MODEL_MISTRAL_LARGE_LATEST),
}

ALLOWED_PROVIDERS = {PROVIDER_GROQ, PROVIDER_MISTRAL}
ALLOWED_MODELS = {MODEL_GROQ_LLAMA_3_3_70B, MODEL_MISTRAL_LARGE_LATEST}


def _needs_legacy_normalization(provider: str, model_id: str) -> bool:
    normalized_provider = str(provider or "").strip().lower()
    normalized_model = str(model_id or "").strip().lower()
    if normalized_provider in {"openai", "claude"}:
        return True
    if normalized_model.startswith("gpt") or normalized_model.startswith("claude"):
        return True
    if normalized_provider not in ALLOWED_PROVIDERS:
        return True
    if model_id not in ALLOWED_MODELS:
        return True
    return False


def _resolve_prompt_target(prompt: Dict[str, Any]) -> Tuple[str, str]:
    purpose = str(prompt.get("purpose") or "").strip().lower()
    provider = str(prompt.get("provider") or "").strip().lower()
    model_id = str(prompt.get("model_id") or "").strip()

    if purpose in PROMPT_PURPOSE_RULES:
        return PROMPT_PURPOSE_RULES[purpose]

    if _needs_legacy_normalization(provider=provider, model_id=model_id):
        return PROVIDER_GROQ, MODEL_GROQ_LLAMA_3_3_70B

    return provider, model_id


async def migrate_prompts() -> Dict[str, int]:
    db = await get_database()
    prompts = db["prompts"]
    now = datetime.utcnow()

    scanned = 0
    updated = 0

    cursor = prompts.find({})
    async for doc in cursor:
        scanned += 1
        target_provider, target_model = _resolve_prompt_target(doc)

        current_provider = str(doc.get("provider") or "").strip().lower()
        current_model = str(doc.get("model_id") or "").strip()

        if current_provider == target_provider and current_model == target_model:
            continue

        await prompts.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "provider": target_provider,
                    "model_id": target_model,
                    "updated_at": now,
                }
            },
        )
        updated += 1

    return {"scanned": scanned, "updated": updated}


async def migrate_pipeline_configs() -> Dict[str, int]:
    db = await get_database()
    pipeline_configs = db["pipeline_configs"]
    now = datetime.utcnow()

    docs_scanned = 0
    docs_updated = 0
    steps_updated = 0

    cursor = pipeline_configs.find({})
    async for doc in cursor:
        docs_scanned += 1
        steps = doc.get("steps", [])
        if not isinstance(steps, list):
            continue

        changed = False
        normalized_steps = []

        for step in steps:
            if not isinstance(step, dict):
                normalized_steps.append(step)
                continue

            step_id = str(step.get("id") or "").strip()
            target = PIPELINE_STEP_RULES.get(step_id)
            if not target:
                normalized_steps.append(step)
                continue

            provider, model_id = target
            ai = step.get("ai", {}) if isinstance(step.get("ai"), dict) else {}
            current_provider = str(ai.get("provider") or "").strip().lower()
            current_model = str(ai.get("model_id") or "").strip()

            if current_provider != provider or current_model != model_id:
                ai["provider"] = provider
                ai["model_id"] = model_id
                step["ai"] = ai
                changed = True
                steps_updated += 1

            normalized_steps.append(step)

        if changed:
            await pipeline_configs.update_one(
                {"_id": doc["_id"]},
                {"$set": {"steps": normalized_steps, "updated_at": now}},
            )
            docs_updated += 1

    return {
        "docs_scanned": docs_scanned,
        "docs_updated": docs_updated,
        "steps_updated": steps_updated,
    }


async def main() -> None:
    prompts_result = await migrate_prompts()
    pipelines_result = await migrate_pipeline_configs()

    print("AI model/provider migration completed.")
    print(
        f"Prompts: scanned={prompts_result['scanned']} updated={prompts_result['updated']}"
    )
    print(
        "Pipeline configs: "
        f"scanned={pipelines_result['docs_scanned']} "
        f"updated={pipelines_result['docs_updated']} "
        f"steps_updated={pipelines_result['steps_updated']}"
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        asyncio.run(close_mongo_client())
