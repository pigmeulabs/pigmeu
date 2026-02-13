"""Utilities for composing final prompts sent to LLM providers."""

from __future__ import annotations

from typing import Any, Dict


def build_user_prompt_with_output_format(base_prompt: str, prompt_doc: Dict[str, Any] | None) -> str:
    """Append expected output format instructions when configured in the prompt document."""
    text = str(base_prompt or "").rstrip()
    doc = prompt_doc or {}
    output_format = str(doc.get("expected_output_format") or doc.get("schema_example") or "").strip()
    if not output_format:
        output_format = (
            "Language: Portuguese (pt-BR).\n"
            "Output: provide a single well-structured response following the task instructions.\n"
            "If JSON is requested, return only valid JSON."
        )

    suffix = (
        "Expected output format:\n"
        f"{output_format}\n\n"
        "Follow this format strictly and do not include extra commentary."
    )
    return f"{text}\n\n{suffix}" if text else suffix
