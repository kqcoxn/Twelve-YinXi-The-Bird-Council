"""Safety Layer - Detects high-risk inputs and generates safe responses."""

import logging

from ..core.llm import LLMClient
from .prompts import SAFETY_SYSTEM_PROMPT, SAFETY_USER_PROMPT

logger = logging.getLogger(__name__)

# Expanded risk keyword list
CRITICAL_RISK_KEYWORDS = [
    "自杀",
    "自残",
    "不想活",
    "去死",
    "死掉",
    "结束生命",
    "活着没意义",
    "不想活了",
    "活够了",
    "自我了断",
    "吞药",
    "跳楼",
    "割腕",
    "suicide",
    "kill myself",
    "end my life",
    "don't want to live",
    "killing",
    "murder",
    "hurt myself",
    "self-harm",
    "self harm",
]


class SafetyLayer:
    """Detects and handles high-risk user inputs."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def is_high_risk(self, user_input: str) -> tuple[bool, list[str]]:
        """Check if input contains high-risk indicators."""
        flags = []
        text_lower = user_input.lower()

        for keyword in CRITICAL_RISK_KEYWORDS:
            if keyword.lower() in text_lower:
                flags.append(f"critical_risk:{keyword}")

        # Check for emotional intensity markers
        intensity_markers = [
            "!!!",
            "！！！",
            "啊啊啊",
            "受不了",
            "崩溃",
            "绝望",
            "!!!",
            "help me",
            "救救我",
            "救命",
        ]
        intensity_count = sum(
            1 for marker in intensity_markers if marker.lower() in text_lower
        )
        if intensity_count >= 2:
            flags.append("high_emotional_intensity")

        return len(flags) > 0, flags

    async def generate_safe_response(self, user_input: str) -> str:
        """Generate a supportive, safe response."""
        try:
            system_prompt = SAFETY_SYSTEM_PROMPT
            user_prompt = SAFETY_USER_PROMPT.format(user_input=user_input)

            response = await self.llm.call_fast(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
            )
            return response
        except Exception as e:
            logger.error(f"Safe response generation failed: {e}")
            return self._fallback_safe_response()

    @staticmethod
    def _fallback_safe_response() -> str:
        """Fallback safe response when LLM fails."""
        return (
            "我感受到你可能正在经历一些困难的时刻。请记住，你并不孤单。"
            "如果你感到极度痛苦或有伤害自己的想法，请立即寻求专业帮助：\n\n"
            "- 全国心理援助热线：400-161-9995\n"
            "- 生命热线：400-821-1215\n\n"
            "你的感受是重要的，有人愿意帮助你。"
        )
