"""Test script for LLM configuration."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.config import settings
from litellm import acompletion


async def test_llm_config():
    """Test LLM configuration and API connectivity."""
    print("=" * 60)
    print("LLM Configuration Test")
    print("=" * 60)

    # Show current configuration
    print("\n[Config] Current settings:")
    print(
        f"  API Key: {settings.FAST_MODEL_API_KEY[:20]}..."
        if settings.FAST_MODEL_API_KEY
        else "  API Key: NOT SET"
    )
    print(f"  Endpoint: {settings.FAST_MODEL_ENDPOINT}")
    print(f"  Model: {settings.FAST_MODEL_NAME}")
    print(f"  Mock Mode: {settings.MOCK_LLM}")

    if not settings.FAST_MODEL_API_KEY:
        print("\n[ERROR] API Key is not configured!")
        print("Please set FAST_MODEL_API_KEY in backend/.env")
        return False

    # Test 1: Direct OpenAI client
    print("\n" + "=" * 60)
    print("Test 1: Direct OpenAI Compatible Call")
    print("=" * 60)
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.FAST_MODEL_API_KEY, base_url=settings.FAST_MODEL_ENDPOINT
        )

        print("Sending test request...")
        response = await client.chat.completions.create(
            model=settings.FAST_MODEL_NAME,
            messages=[{"role": "user", "content": "请回复：测试成功"}],
            max_tokens=50,
            temperature=0.7,
        )

        content = response.choices[0].message.content
        print(f"[SUCCESS] Response: {content}")
        test1_passed = True

    except Exception as e:
        print(f"[FAILED] Error: {e}")
        test1_passed = False

    # Test 2: LiteLLM with openai/ prefix
    print("\n" + "=" * 60)
    print("Test 2: LiteLLM with openai/ prefix")
    print("=" * 60)
    try:
        model_name = f"openai/{settings.FAST_MODEL_NAME}"
        print(f"Model: {model_name}")
        print("Sending test request...")

        response = await acompletion(
            model=model_name,
            messages=[{"role": "user", "content": "请回复：测试成功"}],
            api_key=settings.FAST_MODEL_API_KEY,
            api_base=settings.FAST_MODEL_ENDPOINT,
            max_tokens=50,
            temperature=0.7,
        )

        content = response.choices[0].message.content
        print(f"[SUCCESS] Response: {content}")
        test2_passed = True

    except Exception as e:
        print(f"[FAILED] Error: {e}")
        test2_passed = False

    # Test 3: LiteLLM without prefix (original issue)
    print("\n" + "=" * 60)
    print("Test 3: LiteLLM without prefix (should fail)")
    print("=" * 60)
    try:
        print(f"Model: {settings.FAST_MODEL_NAME}")
        print("Sending test request...")

        response = await acompletion(
            model=settings.FAST_MODEL_NAME,
            messages=[{"role": "user", "content": "请回复：测试成功"}],
            api_key=settings.FAST_MODEL_API_KEY,
            api_base=settings.FAST_MODEL_ENDPOINT,
            max_tokens=50,
            temperature=0.7,
        )

        content = response.choices[0].message.content
        print(f"[SUCCESS] Response: {content}")
        test3_passed = True

    except Exception as e:
        print(f"[EXPECTED FAILURE] Error: {type(e).__name__}: {str(e)[:100]}")
        test3_passed = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Test 1 (OpenAI Direct):    {'PASS' if test1_passed else 'FAIL'}")
    print(f"Test 2 (LiteLLM+prefix):   {'PASS' if test2_passed else 'FAIL'}")
    print(f"Test 3 (LiteLLM no prefix):{'PASS' if test3_passed else 'FAIL (expected)'}")

    if test1_passed and test2_passed:
        print("\n[OK] Your API configuration is correct!")
        print("[INFO] The code fix (adding openai/ prefix) should work.")
        return True
    else:
        print("\n[ERROR] API configuration has issues.")
        print("[TIP] Check your API key and endpoint in backend/.env")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_llm_config())
    sys.exit(0 if result else 1)
