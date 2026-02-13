"""Central defaults for AI providers and models used by Pigmeu."""

from __future__ import annotations

from typing import Optional

PROVIDER_GROQ = "groq"
PROVIDER_MISTRAL = "mistral"

MODEL_GROQ_LLAMA_3_3_70B = "llama-3.3-70b-versatile"
MODEL_MISTRAL_LARGE_LATEST = "mistral-large-latest"

DEFAULT_PROVIDER = PROVIDER_GROQ
DEFAULT_MODEL_ID = MODEL_GROQ_LLAMA_3_3_70B

BOOK_REVIEW_CONTEXT_PROVIDER = PROVIDER_GROQ
BOOK_REVIEW_CONTEXT_MODEL_ID = MODEL_GROQ_LLAMA_3_3_70B

BOOK_REVIEW_ARTICLE_PROVIDER = PROVIDER_MISTRAL
BOOK_REVIEW_ARTICLE_MODEL_ID = MODEL_MISTRAL_LARGE_LATEST


def normalize_provider(provider: Optional[str]) -> Optional[str]:
    raw = str(provider or "").strip().lower()
    if not raw:
        return None

    aliases = {
        "groq": PROVIDER_GROQ,
        "llama": PROVIDER_GROQ,
        "mistral": PROVIDER_MISTRAL,
        "mixtral": PROVIDER_MISTRAL,
    }
    return aliases.get(raw, raw)


def infer_provider_from_model(model_id: str, fallback: str = DEFAULT_PROVIDER) -> str:
    model = str(model_id or "").strip().lower()
    if "mistral" in model or "mixtral" in model:
        return PROVIDER_MISTRAL
    if "llama" in model or "groq" in model:
        return PROVIDER_GROQ
    return fallback
