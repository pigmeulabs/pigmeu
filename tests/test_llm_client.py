"""Tests for src/workers/llm_client.py."""

import pytest
from unittest.mock import AsyncMock, patch
from src.workers.llm_client import LLMClient
from src.config import settings

@pytest.fixture
def mock_llm_client():
    """Fixture for LLMClient with mocked AsyncOpenAI."""
    with patch("src.workers.llm_client.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        yield LLMClient(), mock_client

@pytest.mark.asyncio
async def test_generate_success(mock_llm_client):
    """Test successful LLM response generation."""
    llm_client, mock_client = mock_llm_client
    mock_response = AsyncMock()
    mock_response.choices[0].message.content = "Test response"
    mock_client.chat.completions.create.return_value = mock_response

    response = await llm_client.generate(
        system_prompt="System prompt",
        user_prompt="User prompt",
        model_id="mixtral-8x7b-32768",
    )

    assert response == "Test response"
    mock_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_fallback(mock_llm_client):
    """Test fallback to another provider when primary fails."""
    llm_client, mock_client = mock_llm_client
    # Simulate primary provider (Groq) as None
    llm_client._clients["groq"] = None
    mock_response = AsyncMock()
    mock_response.choices[0].message.content = "Fallback response"
    mock_client.chat.completions.create.return_value = mock_response

    response = await llm_client.generate(
        system_prompt="System prompt",
        user_prompt="User prompt",
        model_id="mixtral-8x7b-32768",
        provider="groq",  # Force fallback
    )

    assert response == "Fallback response"

@pytest.mark.asyncio
async def test_generate_with_retry_success(mock_llm_client):
    """Test successful retry after initial failure."""
    llm_client, mock_client = mock_llm_client
    mock_response = AsyncMock()
    mock_response.choices[0].message.content = "Success after retry"
    mock_client.chat.completions.create.side_effect = [
        RuntimeError("First attempt failed"),
        mock_response,
    ]

    response = await llm_client.generate_with_retry(
        system_prompt="System prompt",
        user_prompt="User prompt",
        max_retries=2,
    )

    assert response == "Success after retry"
    assert mock_client.chat.completions.create.call_count == 2

@pytest.mark.asyncio
async def test_generate_with_retry_failure(mock_llm_client):
    """Test failure after max retries."""
    llm_client, mock_client = mock_llm_client
    mock_client.chat.completions.create.side_effect = RuntimeError("Failed")

    with pytest.raises(RuntimeError, match="Failed after 3 attempts"):
        await llm_client.generate_with_retry(
            system_prompt="System prompt",
            user_prompt="User prompt",
            max_retries=3,
        )