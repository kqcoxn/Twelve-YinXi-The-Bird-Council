"""SSE (Server-Sent Events) streaming endpoints."""

import json
import logging
from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from datetime import datetime

from ..models.api import SubmitProposalRequest
from ..models.council import CouncilConclusion
from ..services.memory_service import memory_service
from ..core.llm import LLMClient

logger = logging.getLogger(__name__)

router = APIRouter()

_llm_client = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


async def stream_conclusion(proposal: str) -> AsyncGenerator[str, None]:
    """Stream council conclusion as SSE events."""
    client = get_llm_client()

    try:
        # Send start event
        yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now().isoformat()})}\n\n"

        # Build system prompt
        system_prompt = """你是一个群鸟议会的主持人。请针对用户的议题，提供一个全面、平衡的分析。
请以JSON格式返回，包含以下字段：
- summary: 总体结论（200-300字）
- decision: 决策类型（approve/oppose/conditional/delay）
- main_reasons: 主要理由（数组，2-3条）
- risks: 风险提示（数组，1-2条）
- next_steps: 建议的下一步行动（数组，1-2条）"""

        user_prompt = f"用户议题：{proposal}\n\n请提供你的分析和结论。"

        # Stream the response token by token
        accumulated_text = ""
        async for token in client.stream_fast(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
        ):
            accumulated_text += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        # Try to parse the accumulated text as JSON
        try:
            json_str = accumulated_text[
                accumulated_text.find("{") : accumulated_text.rfind("}") + 1
            ]
            if json_str:
                conclusion_data = json.loads(json_str)
                yield f"data: {json.dumps({'type': 'conclusion', 'data': conclusion_data})}\n\n"
        except json.JSONDecodeError:
            # If not valid JSON, send as text
            yield f"data: {json.dumps({'type': 'text_response', 'content': accumulated_text})}\n\n"

        # Send complete event
        yield f"data: {json.dumps({'type': 'complete', 'timestamp': datetime.now().isoformat()})}\n\n"

    except Exception as e:
        logger.error(f"SSE streaming failed: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/council/stream")
async def stream_proposal(request: SubmitProposalRequest):
    """Stream a council response using Server-Sent Events."""
    return StreamingResponse(
        stream_conclusion(request.user_input),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
