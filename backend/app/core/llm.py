import asyncio
from typing import Optional
from openai import AsyncOpenAI
from litellm import acompletion
from ..core.config import settings


class LLMClient:
    """LLM client with retry logic and mock mode support."""

    def __init__(self, api_key: str, endpoint: str, model: str):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self.client = (
            AsyncOpenAI(api_key=api_key, base_url=endpoint) if api_key else None
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        **kwargs,
    ) -> str:
        """Generate text with retry logic."""
        if settings.MOCK_LLM:
            return await self._mock_generate(prompt, system_prompt)

        for attempt in range(max_retries):
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = await acompletion(
                    model=self.model,
                    messages=messages,
                    api_key=self.api_key,
                    api_base=self.endpoint,
                    **kwargs,
                )

                return response.choices[0].message.content

            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = backoff_factor**attempt
                print(
                    f"[WARN] LLM call failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                print(f"[RETRY] Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

        raise Exception("LLM call failed after all retries")

    async def _mock_generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Mock response for development/testing."""
        await asyncio.sleep(0.5)  # Simulate latency

        # Simple mock: detect intent and return appropriate response
        if "反对" in prompt or "oppose" in prompt.lower():
            return "我反对这个提议。我们需要更多的证据和讨论。"
        elif "赞成" in prompt or "approve" in prompt.lower():
            return "我赞成这个提议。这看起来是一个合理的方案。"
        else:
            return "我已经收到了你的提议,让我思考一下..."


# Fast model client (for pre-votes, quick responses)
fast_client = LLMClient(
    api_key=settings.FAST_MODEL_API_KEY,
    endpoint=settings.FAST_MODEL_ENDPOINT,
    model=settings.FAST_MODEL_NAME,
)

# Strong model client (for debates, summaries)
strong_client = LLMClient(
    api_key=settings.STRONG_MODEL_API_KEY,
    endpoint=settings.STRONG_MODEL_ENDPOINT,
    model=settings.STRONG_MODEL_NAME,
)


async def call_llm_with_retry(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_retries: int = 3,
    model: str = "fast",
    **kwargs,
) -> str:
    """Convenience function for LLM calls with retry."""
    client = fast_client if model == "fast" else strong_client
    return await client.generate(prompt, system_prompt, max_retries, **kwargs)
