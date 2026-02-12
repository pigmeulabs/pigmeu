"""LLM client with provider routing (OpenAI/Groq/Mistral)."""

from __future__ import annotations

import asyncio
from typing import Optional

from openai import AsyncOpenAI

from src.config import settings


class LLMClient:
    """Client for interacting with language models."""

    def __init__(self):
        self._clients = {
            "openai": AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None,
            "groq": (
                AsyncOpenAI(api_key=settings.groq_api_key, base_url="https://api.groq.com/openai/v1")
                if settings.groq_api_key
                else None
            ),
            "mistral": (
                AsyncOpenAI(api_key=settings.mistral_api_key, base_url="https://api.mistral.ai/v1")
                if settings.mistral_api_key
                else None
            ),
        }

    @staticmethod
    def _select_provider(model_id: str, provider: Optional[str]) -> str:
        if provider:
            return provider

        model = (model_id or "").lower()
        if "mistral" in model or "mixtral" in model:
            return "mistral"
        if "llama" in model or "groq" in model:
            return "groq"
        return "openai"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        provider: Optional[str] = None,
        **kwargs,
    ) -> str:
        selected_provider = self._select_provider(model_id=model_id, provider=provider)
        client = self._clients.get(selected_provider)

        # fallback order if selected provider is not configured
        if client is None:
            for fallback in ("openai", "groq", "mistral"):
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
