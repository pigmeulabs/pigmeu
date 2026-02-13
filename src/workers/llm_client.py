"""LLM client with provider routing (Groq/Mistral)."""

from __future__ import annotations

import asyncio
from typing import Optional

from openai import AsyncOpenAI

from src.config import settings
from src.workers.ai_defaults import (
    DEFAULT_MODEL_ID,
    DEFAULT_PROVIDER,
    PROVIDER_GROQ,
    PROVIDER_MISTRAL,
    infer_provider_from_model,
    normalize_provider,
)


class LLMClient:
    """Client for interacting with language models."""

    def __init__(self):
        self._clients = {
            PROVIDER_GROQ: (
                AsyncOpenAI(api_key=settings.groq_api_key, base_url="https://api.groq.com/openai/v1")
                if settings.groq_api_key
                else None
            ),
            PROVIDER_MISTRAL: (
                AsyncOpenAI(api_key=settings.mistral_api_key, base_url="https://api.mistral.ai/v1")
                if settings.mistral_api_key
                else None
            ),
        }

    @staticmethod
    def _normalize_provider(provider: Optional[str]) -> Optional[str]:
        return normalize_provider(provider)

    @staticmethod
    def _provider_base_url(provider: str) -> Optional[str]:
        normalized = LLMClient._normalize_provider(provider) or ""
        if normalized == PROVIDER_GROQ:
            return "https://api.groq.com/openai/v1"
        if normalized == PROVIDER_MISTRAL:
            return "https://api.mistral.ai/v1"
        return None

    @classmethod
    def _build_client(cls, provider: str, api_key: str) -> AsyncOpenAI:
        normalized = cls._normalize_provider(provider) or DEFAULT_PROVIDER
        kwargs = {"api_key": api_key}
        base_url = cls._provider_base_url(normalized)
        if base_url:
            kwargs["base_url"] = base_url
        return AsyncOpenAI(**kwargs)

    @staticmethod
    def _select_provider(model_id: str, provider: Optional[str]) -> str:
        normalized = LLMClient._normalize_provider(provider)
        if normalized:
            return normalized
        return infer_provider_from_model(model_id=model_id, fallback=DEFAULT_PROVIDER)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: str = DEFAULT_MODEL_ID,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        allow_fallback: bool = True,
        **kwargs,
    ) -> str:
        selected_provider = self._select_provider(model_id=model_id, provider=provider)
        client = self._build_client(selected_provider, api_key) if api_key else self._clients.get(selected_provider)

        # Fallback between supported providers only (no OpenAI automatic fallback).
        if client is None and allow_fallback:
            fallback_order = (
                [PROVIDER_MISTRAL, PROVIDER_GROQ]
                if selected_provider == PROVIDER_MISTRAL
                else [PROVIDER_GROQ, PROVIDER_MISTRAL]
            )
            for fallback in fallback_order:
                if self._clients.get(fallback) is not None:
                    client = self._clients[fallback]
                    break

        if client is None:
            raise RuntimeError("No LLM provider configured")

        response = await client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        content = response.choices[0].message.content
        return content.strip() if isinstance(content, str) else ""

    async def generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
        **kwargs,
    ) -> str:
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                return await self.generate(system_prompt=system_prompt, user_prompt=user_prompt, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 + attempt)

        raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")
