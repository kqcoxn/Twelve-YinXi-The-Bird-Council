"""Perceiver - Analyzes user input for intent, emotion, and risk flags."""

import json
import logging
from typing import Any

from ..core.llm import LLMClient
from ..models.council import PerceptionResult
from .prompts import PERCEIVER_SYSTEM_PROMPT, PERCEIVER_USER_PROMPT

logger = logging.getLogger(__name__)

# Keyword-based risk detection fallback
RISK_KEYWORDS = [
    "自杀",
    "自残",
    "不想活",
    "去死",
    "死掉",
    "结束生命",
    "活着没意义",
    "杀人",
    "暴力",
    "伤害自己",
    "伤害别人",
    "崩溃",
    "活不下去",
    "suicide",
    "kill",
    "die",
    "death",
    "hurt myself",
    "end my life",
]


class Perceiver:
    """Perceives user input intent using LLM with keyword fallback."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def perceive(self, user_input: str) -> PerceptionResult:
        """Analyze user input and return PerceptionResult."""
        # Check risk keywords first
        risk_flags = self._check_risk_keywords(user_input)

        try:
            result = await self._llm_perceive(user_input)
            # Merge keyword risks with LLM risks
            for flag in risk_flags:
                if flag not in result.risk_flags:
                    result.risk_flags.append(flag)
            return result
        except Exception as e:
            logger.warning(f"LLM perception failed, using fallback: {e}")
            return self._fallback_perceive(user_input, risk_flags)

    async def _llm_perceive(self, user_input: str) -> PerceptionResult:
        """Call LLM for structured perception."""
        system_prompt = PERCEIVER_SYSTEM_PROMPT
        user_prompt = PERCEIVER_USER_PROMPT.format(user_input=user_input)

        response = await self.llm.call_fast(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        # Parse JSON response
        json_str = self._extract_json(response)
        data = json.loads(json_str)

        return PerceptionResult(
            task_type=data.get("task_type", "chat"),
            emotion_profile=data.get(
                "emotion_profile",
                {
                    "anxiety": 0.0,
                    "confusion": 0.0,
                    "urgency": 0.0,
                    "sadness": 0.0,
                    "anger": 0.0,
                    "hope": 0.0,
                },
            ),
            risk_flags=data.get("risk_flags", []),
            suggested_mode=data.get("suggested_mode", "light_chat"),
            suggested_depth=data.get("suggested_depth", 1),
        )

    def _check_risk_keywords(self, text: str) -> list[str]:
        """Check for risk keywords in input."""
        flags = []
        text_lower = text.lower()
        for keyword in RISK_KEYWORDS:
            if keyword.lower() in text_lower:
                flags.append(f"risk_keyword:{keyword}")
        return flags

    def _fallback_perceive(
        self, user_input: str, risk_flags: list[str]
    ) -> PerceptionResult:
        """Fallback perception when LLM fails."""
        length = len(user_input)
        is_question = "?" in user_input or "？" in user_input

        # Simple heuristic
        if length < 20:
            task_type = "chat"
        elif is_question:
            task_type = "decision"
        else:
            task_type = "emotional_sorting"

        return PerceptionResult(
            task_type=task_type,
            emotion_profile={
                "anxiety": 0.3,
                "confusion": 0.3,
                "urgency": 0.2,
                "sadness": 0.2,
                "anger": 0.1,
                "hope": 0.3,
            },
            risk_flags=risk_flags,
            suggested_mode="light_chat" if task_type == "chat" else "full_council",
            suggested_depth=1 if task_type == "chat" else 2,
        )

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from LLM response."""
        # Try to find JSON block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start : end + 1]
        return text
