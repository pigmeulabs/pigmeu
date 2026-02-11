"""
LLM Client module for interacting with language models.
"""

from typing import Optional
from src.config import settings
import openai
import asyncio


class LLMClient:
    """Client for interacting with language models."""

    def __init__(self):
        self.client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Generate text using the LLM.
        
        Args:
            system_prompt: System prompt for the model
            user_prompt: User prompt for the model
            model_id: Model identifier
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments for the API
            
        Returns:
            Generated text content
        """
        try:
            response = await self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Error generating text with LLM: {e}")
            raise

    async def generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """
        Generate text with retry logic.
        
        Args:
            system_prompt: System prompt for the model
            user_prompt: User prompt for the model
            max_retries: Maximum number of retries
            **kwargs: Additional arguments for generate method
            
        Returns:
            Generated text content
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.generate(system_prompt, user_prompt, **kwargs)
            except Exception as e:
                last_error = e
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Wait before retry
        
        raise Exception(f"Failed after {max_retries} attempts: {last_error}")