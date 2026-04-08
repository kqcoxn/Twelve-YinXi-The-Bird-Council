import asyncio
from typing import Optional, AsyncGenerator
from openai import AsyncOpenAI
from litellm import acompletion
from ..core.config import settings


class TokenUsage:
    """Track token usage for LLM calls."""

    def __init__(self):
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.total_tokens: int = 0

    def add_from_response(self, usage) -> None:
        """Add token usage from LLM response."""
        if usage:
            self.input_tokens += getattr(usage, "prompt_tokens", 0)
            self.output_tokens += getattr(usage, "completion_tokens", 0)
            self.total_tokens += getattr(usage, "total_tokens", 0)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


class LLMClient:
    """LLM client with retry logic and mock mode support."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.FAST_MODEL_API_KEY
        self.endpoint = endpoint or settings.FAST_MODEL_ENDPOINT
        self.model = model or settings.FAST_MODEL_NAME
        self.client = (
            AsyncOpenAI(api_key=self.api_key, base_url=self.endpoint)
            if self.api_key
            else None
        )
        self.is_mock = settings.MOCK_LLM or not self.api_key

    async def call_fast(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> tuple[str, TokenUsage]:
        """Call fast model. Returns (text, token_usage)."""
        if self.is_mock:
            text = await self._mock_generate(user_prompt, system_prompt)
            return text, TokenUsage()

        return await self._generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=settings.FAST_MODEL_NAME,
        )

    async def call_strong(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> tuple[str, TokenUsage]:
        """Call strong model. Returns (text, token_usage)."""
        if self.is_mock:
            text = await self._mock_generate(user_prompt, system_prompt)
            return text, TokenUsage()

        return await self._generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=settings.STRONG_MODEL_NAME,
        )

    async def stream_fast(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[str, None]:
        """Stream from fast model with token-by-token response."""
        if self.is_mock:
            for chunk in self._mock_stream(user_prompt, system_prompt):
                yield chunk
                await asyncio.sleep(0.05)  # Simulate typing delay
            return

        async for chunk in self._stream_generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=settings.FAST_MODEL_NAME,
        ):
            yield chunk

    async def stream_strong(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """Stream from strong model with token-by-token response."""
        if self.is_mock:
            for chunk in self._mock_stream(user_prompt, system_prompt):
                yield chunk
                await asyncio.sleep(0.05)
            return

        async for chunk in self._stream_generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=settings.STRONG_MODEL_NAME,
        ):
            yield chunk

    async def _generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        model: str,
        max_retries: int = 3,
    ) -> tuple[str, TokenUsage]:
        """Generate text with retry logic. Returns (text, token_usage)."""
        for attempt in range(max_retries):
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

                response = await acompletion(
                    model=f"{settings.FAST_MODEL_PROVIDER}/{model}",
                    messages=messages,
                    api_key=self.api_key,
                    api_base=self.endpoint,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                usage = TokenUsage()
                usage.add_from_response(getattr(response, "usage", None))
                return response.choices[0].message.content, usage

            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2.0**attempt
                print(
                    f"[WARN] LLM call failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                print(f"[RETRY] Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

        raise Exception("LLM call failed after all retries")

    async def _stream_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        model: str,
        max_retries: int = 3,
    ) -> AsyncGenerator[str, None]:
        """Stream generate text with retry logic."""
        for attempt in range(max_retries):
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

                response = await acompletion(
                    model=f"{settings.FAST_MODEL_PROVIDER}/{model}",
                    messages=messages,
                    api_key=self.api_key,
                    api_base=self.endpoint,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )

                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return

            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2.0**attempt
                print(
                    f"[WARN] Streaming LLM call failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                print(f"[RETRY] Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

        raise Exception("Streaming LLM call failed after all retries")

    async def _mock_generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Mock response for development/testing."""
        await asyncio.sleep(0.3)  # Simulate latency

        # Return a simple mock response
        return "我已经思考了你的议题。这是一个复杂的问题,需要综合考虑多方面因素。"

    def _mock_stream(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> list[str]:
        """Mock streaming response for development/testing."""
        full_response = (
            "我已经思考了你的议题。这是一个复杂的问题，需要综合考虑多方面因素。"
        )
        # Split into character chunks for realistic streaming effect
        return list(full_response)


# Pre-configured clients
fast_client = LLMClient()
strong_client = LLMClient()


async def call_llm_with_retry(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_retries: int = 3,
    model: str = "fast",
    **kwargs,
) -> str:
    """Convenience function for LLM calls with retry."""
    client = fast_client if model == "fast" else strong_client
    if client.is_mock:
        return await client._mock_generate(prompt, system_prompt)
    return await client._generate(
        system_prompt=system_prompt or "",
        user_prompt=prompt,
        temperature=0.7,
        max_tokens=1000,
        model=(
            settings.FAST_MODEL_NAME if model == "fast" else settings.STRONG_MODEL_NAME
        ),
        max_retries=max_retries,
    )
