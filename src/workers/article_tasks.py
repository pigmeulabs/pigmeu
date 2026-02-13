"""Article generation tasks using ArticleStructurer."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from celery import shared_task

from src.db.connection import get_db
from src.db.repositories import (
    SubmissionRepository,
    BookRepository,
    KnowledgeBaseRepository,
    SummaryRepository,
    ArticleRepository,
    ContentSchemaRepository,
    PromptRepository,
    CredentialRepository,
    PipelineConfigRepository,
)
from src.models.enums import SubmissionStatus
from src.workers.article_structurer import ArticleStructurer
from src.workers.ai_defaults import (
    BOOK_REVIEW_ARTICLE_MODEL_ID,
    BOOK_REVIEW_ARTICLE_PROVIDER,
    DEFAULT_PROVIDER,
    infer_provider_from_model,
)

logger = logging.getLogger(__name__)
BOOK_REVIEW_PIPELINE_ID = "book_review_v2"
ARTICLE_GENERATION_STEP_ID = "article_generation"


def _safe_delay_seconds(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _infer_provider(model_id: str) -> str:
    return infer_provider_from_model(model_id=model_id, fallback=DEFAULT_PROVIDER)


async def _resolve_article_generation_config(
    pipeline_repo: PipelineConfigRepository,
    prompt_repo: PromptRepository,
    credential_repo: CredentialRepository,
    pipeline_id: str,
) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "pipeline_id": str(pipeline_id or BOOK_REVIEW_PIPELINE_ID),
        "step_id": ARTICLE_GENERATION_STEP_ID,
        "delay_seconds": 0,
        "provider": BOOK_REVIEW_ARTICLE_PROVIDER,
        "model_id": BOOK_REVIEW_ARTICLE_MODEL_ID,
        "temperature": 0.7,
        "max_tokens": 2500,
        "prompt_id": None,
        "credential_id": None,
        "prompt_doc": None,
        "api_key": None,
        "allow_fallback": True,
    }

    pipeline_doc = await pipeline_repo.get_by_pipeline_id(config["pipeline_id"])
    raw_steps = pipeline_doc.get("steps", []) if pipeline_doc and isinstance(pipeline_doc.get("steps"), list) else []
    step_doc = next((step for step in raw_steps if str(step.get("id")) == ARTICLE_GENERATION_STEP_ID), None) or {}
    ai_doc = step_doc.get("ai", {}) if isinstance(step_doc.get("ai"), dict) else {}

    config["delay_seconds"] = _safe_delay_seconds(step_doc.get("delay_seconds"))
    config["provider"] = str(ai_doc.get("provider") or config["provider"]).strip().lower() or config["provider"]
    config["prompt_id"] = str(ai_doc.get("prompt_id")) if ai_doc.get("prompt_id") else None
    config["credential_id"] = str(ai_doc.get("credential_id")) if ai_doc.get("credential_id") else None

    prompt_doc: Optional[Dict[str, Any]] = None
    if config["prompt_id"]:
        prompt_doc = await prompt_repo.get_by_id(config["prompt_id"])

    if not prompt_doc:
        default_prompt_purpose = str(ai_doc.get("default_prompt_purpose") or "").strip()
        if default_prompt_purpose:
            prompt_doc = await prompt_repo.get_active_by_purpose(default_prompt_purpose)

    if not prompt_doc:
        prompt_doc = await prompt_repo.get_active_by_purpose("article")
    if not prompt_doc:
        prompt_doc = await prompt_repo.get_by_name("SEO-Optimized Article Writer")

    config["prompt_doc"] = prompt_doc
    if prompt_doc:
        config["prompt_id"] = str(prompt_doc.get("_id"))

    model_from_step = ai_doc.get("model_id")
    model_from_prompt = prompt_doc.get("model_id") if prompt_doc else None
    model_id = str(model_from_step or model_from_prompt or config["model_id"]).strip()
    config["model_id"] = model_id or config["model_id"]
    if not ai_doc.get("provider"):
        config["provider"] = _infer_provider(config["model_id"])

    temp_value = ai_doc.get("temperature")
    if temp_value is None and prompt_doc:
        temp_value = prompt_doc.get("temperature")
    config["temperature"] = _safe_float(temp_value, config["temperature"])

    max_tokens_value = ai_doc.get("max_tokens")
    if max_tokens_value is None and prompt_doc:
        max_tokens_value = prompt_doc.get("max_tokens")
    config["max_tokens"] = max(1, _safe_int(max_tokens_value, config["max_tokens"]))

    credential_doc: Optional[Dict[str, Any]] = None
    if config["credential_id"]:
        credential_doc = await credential_repo.get_by_id(config["credential_id"])
        if credential_doc and not credential_doc.get("active", True):
            credential_doc = None

    if not credential_doc:
        preferred_name = str(ai_doc.get("default_credential_name") or "").strip()
        if preferred_name:
            credential_doc = await credential_repo.get_active_by_name(preferred_name, service=config["provider"])
            if not credential_doc:
                credential_doc = await credential_repo.get_active(config["provider"])

    if credential_doc:
        config["credential_id"] = str(credential_doc.get("_id"))
        provider = str(credential_doc.get("service") or "").strip().lower()
        if provider:
            config["provider"] = provider
        key = str(credential_doc.get("key") or "").strip()
        config["api_key"] = key or None
        config["allow_fallback"] = not bool(config["api_key"] and config["provider"])
        try:
            await credential_repo.touch_last_used(credential_doc.get("_id"))
        except Exception:
            logger.warning("Failed to touch last_used for credential %s", credential_doc.get("_id"))

    return config


@shared_task(bind=True)
def generate_article_task(self, submission_id: str, skip_config_delay: bool = False) -> dict:
    """Generate a full review article for a submission."""

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _run():
            db = await get_db()
            submission_repo = SubmissionRepository(db)
            book_repo = BookRepository(db)
            kb_repo = KnowledgeBaseRepository(db)
            summary_repo = SummaryRepository(db)
            article_repo = ArticleRepository(db)
            content_schema_repo = ContentSchemaRepository(db)
            prompt_repo = PromptRepository(db)
            credential_repo = CredentialRepository(db)
            pipeline_repo = PipelineConfigRepository(db)

            submission = await submission_repo.get_by_id(submission_id)
            if not submission:
                return {"status": "error", "error": "submission_not_found"}
            pipeline_id = str(submission.get("pipeline_id") or BOOK_REVIEW_PIPELINE_ID)

            book = await book_repo.get_by_submission(submission_id)
            if not book:
                return {"status": "error", "error": "book_not_found"}

            kb = await kb_repo.get_by_book(str(book.get("_id")))
            summaries = await summary_repo.get_by_book(str(book.get("_id")))

            selected_schema = None
            schema_id = str(submission.get("content_schema_id") or "").strip()
            if schema_id:
                selected_schema = await content_schema_repo.get_by_id(schema_id)

            if not selected_schema:
                active_schemas = await content_schema_repo.list_all(active=True, target_type="book_review")
                selected_schema = active_schemas[0] if active_schemas else None

            if selected_schema and not schema_id:
                await submission_repo.update_fields(
                    submission_id,
                    {"content_schema_id": str(selected_schema.get("_id"))},
                )

            article_step_config = await _resolve_article_generation_config(
                pipeline_repo=pipeline_repo,
                prompt_repo=prompt_repo,
                credential_repo=credential_repo,
                pipeline_id=pipeline_id,
            )
            configured_delay = _safe_delay_seconds(article_step_config.get("delay_seconds"))
            if configured_delay > 0 and not skip_config_delay:
                await submission_repo.update_status(
                    submission_id,
                    SubmissionStatus.PENDING_ARTICLE,
                    {"current_step": "pending_article"},
                )
                generate_article_task.apply_async(
                    kwargs={"submission_id": submission_id, "skip_config_delay": True},
                    countdown=configured_delay,
                )
                return {
                    "status": "queued",
                    "submission_id": submission_id,
                    "step": ARTICLE_GENERATION_STEP_ID,
                    "delay_seconds": configured_delay,
                }

            extracted = book.get("extracted", {}) or {}
            consolidated = extracted.get("consolidated_bibliographic", {}) if isinstance(extracted, dict) else {}
            web_research = extracted.get("web_research", {}) if isinstance(extracted, dict) else {}

            context_blocks = []
            if kb and kb.get("markdown_content"):
                context_blocks.append(str(kb.get("markdown_content")))

            if submission.get("textual_information"):
                context_blocks.append(
                    "## User notes\n"
                    f"{submission.get('textual_information')}"
                )

            if summaries:
                lines = ["## Additional links summaries"]
                for item in summaries:
                    source_url = str(item.get("source_url") or "").strip()
                    summary_text = str(item.get("summary_text") or "").strip()
                    if source_url or summary_text:
                        lines.append(f"- {source_url}: {summary_text}")
                if len(lines) > 1:
                    context_blocks.append("\n".join(lines))

            if isinstance(web_research, dict) and web_research.get("research_markdown"):
                context_blocks.append(
                    "## Web research\n"
                    f"{str(web_research.get('research_markdown'))}"
                )

            context = "\n\n".join([block for block in context_blocks if str(block).strip()])

            await submission_repo.update_status(
                submission_id,
                SubmissionStatus.PENDING_ARTICLE,
                {"current_step": "article_generation"},
            )

            structurer = ArticleStructurer()
            book_data = {
                "title": submission.get("title") or "Book Review",
                "author": submission.get("author_name") or "",
                "metadata": extracted,
                "consolidated_bibliographic": consolidated,
                "web_research": web_research,
                "user_notes": submission.get("textual_information"),
                "other_links": submission.get("other_links", []),
                "summaries": [
                    {
                        "source_url": item.get("source_url"),
                        "source_domain": item.get("source_domain"),
                        "summary_text": item.get("summary_text"),
                        "topics": item.get("topics", []),
                        "key_points": item.get("key_points", []),
                    }
                    for item in summaries
                ],
            }

            try:
                article_content = await structurer.generate_valid_article(
                    book_data=book_data,
                    context=context,
                    content_schema=selected_schema,
                    prompt_doc=article_step_config.get("prompt_doc"),
                    llm_config={
                        "provider": article_step_config.get("provider"),
                        "api_key": article_step_config.get("api_key"),
                        "model_id": article_step_config.get("model_id"),
                        "temperature": article_step_config.get("temperature"),
                        "max_tokens": article_step_config.get("max_tokens"),
                        "allow_fallback": article_step_config.get("allow_fallback", True),
                    },
                    max_retries=3,
                )
            except Exception:
                # Deterministic fallback keeps pipeline moving even when strict validation fails.
                fallback_topics = structurer._fallback_topics(book_data)
                if selected_schema:
                    article_content = structurer._build_schema_template_article(
                        book_data=book_data,
                        context=context,
                        content_schema=selected_schema,
                        topics=fallback_topics,
                    )
                else:
                    article_content = structurer._build_template_article(book_data, fallback_topics, context)

            lines = article_content.splitlines()
            gen_title = next(
                (line.replace("# ", "").strip() for line in lines if line.startswith("# ")),
                f"{book_data['title']} Review",
            )

            validation = await structurer.validate_article(
                article_content,
                strict=True,
                content_schema=selected_schema,
            )
            if selected_schema:
                validation["schema"] = {
                    "id": str(selected_schema.get("_id")),
                    "name": selected_schema.get("name"),
                }
            validation["pipeline_step"] = {
                "pipeline_id": pipeline_id,
                "step_id": ARTICLE_GENERATION_STEP_ID,
                "delay_seconds": configured_delay,
                "provider": article_step_config.get("provider"),
                "model_id": article_step_config.get("model_id"),
                "temperature": article_step_config.get("temperature"),
                "max_tokens": article_step_config.get("max_tokens"),
                "prompt_id": article_step_config.get("prompt_id"),
                "credential_id": article_step_config.get("credential_id"),
            }

            article_id = await article_repo.create(
                book_id=str(book.get("_id")),
                submission_id=submission_id,
                title=gen_title,
                content=article_content,
                word_count=len(article_content.split()),
                status="draft" if submission.get("user_approval_required") else "in_review",
                validation_report=validation,
            )

            await submission_repo.update_status(
                submission_id,
                SubmissionStatus.ARTICLE_GENERATED,
                {
                    "current_step": "article_generated",
                    "article_id": article_id,
                },
            )

            if not submission.get("user_approval_required"):
                await submission_repo.update_status(
                    submission_id,
                    SubmissionStatus.READY_FOR_REVIEW,
                    {"current_step": "ready_for_review"},
                )

            logger.info("Article generated successfully: %s", article_id)
            return {
                "status": "ok",
                "article_id": article_id,
                "step": ARTICLE_GENERATION_STEP_ID,
                "pipeline_config_applied": {
                    "pipeline_id": pipeline_id,
                    "delay_seconds": configured_delay,
                    "provider": article_step_config.get("provider"),
                    "model_id": article_step_config.get("model_id"),
                    "temperature": article_step_config.get("temperature"),
                    "max_tokens": article_step_config.get("max_tokens"),
                    "prompt_id": article_step_config.get("prompt_id"),
                    "credential_id": article_step_config.get("credential_id"),
                },
            }

        return loop.run_until_complete(_run())
    except Exception as e:
        logger.error("Error generating article: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}
