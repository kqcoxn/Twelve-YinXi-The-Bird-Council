"""Narrative Renderer - Generates multi-view output from debate results."""

import json
import logging
from typing import Any

from ..core.llm import LLMClient
from ..models.council import CouncilConclusion, DebateTranscript, PerceptionResult
from .prompts import (
    RENDER_DRAMATIC_PROMPT,
    RENDER_PRACTICAL_PROMPT,
    RENDER_PSYCHOLOGICAL_PROMPT,
)

logger = logging.getLogger(__name__)


class Renderer:
    """Generates dramatic, practical, and psychological output views."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def render_all(
        self,
        conclusion: CouncilConclusion,
        transcript: DebateTranscript,
        perception: PerceptionResult | None = None,
    ) -> dict[str, str]:
        """Generate all three views."""
        conclusion_data = self._conclusion_to_dict(conclusion)
        debate_highlights = self._extract_highlights(transcript)
        emotion_profile = perception.emotion_profile if perception else {}

        views = {}

        # Generate views in parallel (independent)
        import asyncio

        tasks = [
            self._render_dramatic(conclusion_data, debate_highlights),
            self._render_practical(conclusion_data),
            self._render_psychological(conclusion_data, emotion_profile),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        view_names = ["dramatic", "practical", "psychological"]
        for name, result in zip(view_names, results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to render {name} view: {result}")
                views[name] = self._fallback_render(name, conclusion_data)
            else:
                views[name] = result

        return views

    async def _render_dramatic(self, conclusion_data: dict, highlights: str) -> str:
        """Generate dramatic narrative."""
        prompt = RENDER_DRAMATIC_PROMPT.format(
            conclusion_data=json.dumps(conclusion_data, ensure_ascii=False, indent=2),
            debate_highlights=highlights,
        )
        response = await self.llm.call_strong(
            system_prompt="你是一个擅长戏剧性叙事的作家。请用充满张力和冲突的语言描述事件。",
            user_prompt=prompt,
            temperature=0.9,
        )
        return response.strip()

    async def _render_practical(self, conclusion_data: dict) -> str:
        """Generate practical summary."""
        prompt = RENDER_PRACTICAL_PROMPT.format(
            conclusion_data=json.dumps(conclusion_data, ensure_ascii=False, indent=2),
        )
        response = await self.llm.call_fast(
            system_prompt="你是一个擅长实用建议的顾问。请给出清晰、可操作的建议。",
            user_prompt=prompt,
            temperature=0.5,
        )
        return response.strip()

    async def _render_psychological(
        self, conclusion_data: dict, emotion_profile: dict
    ) -> str:
        """Generate psychological analysis."""
        prompt = RENDER_PSYCHOLOGICAL_PROMPT.format(
            conclusion_data=json.dumps(conclusion_data, ensure_ascii=False, indent=2),
            emotion_profile=json.dumps(emotion_profile, ensure_ascii=False, indent=2),
        )
        response = await self.llm.call_strong(
            system_prompt="你是一个心理分析师。请从心理学角度分析用户的情绪状态和需求。",
            user_prompt=prompt,
            temperature=0.7,
        )
        return response.strip()

    def _conclusion_to_dict(self, conclusion: CouncilConclusion) -> dict:
        """Convert CouncilConclusion to dict for rendering."""
        return {
            "summary": conclusion.summary,
            "decision": conclusion.decision,
            "main_reasons": conclusion.main_reasons,
            "risks": conclusion.risks,
            "next_steps": conclusion.next_steps,
            "minority_opinion": conclusion.minority_opinion,
            "vote_result": {
                "approve": conclusion.vote_result.approve,
                "oppose": conclusion.vote_result.oppose,
                "abstain": conclusion.vote_result.abstain,
            },
        }

    def _extract_highlights(self, transcript: DebateTranscript) -> str:
        """Extract debate highlights from transcript."""
        if not transcript.rounds:
            return "辩论记录为空"

        highlights = []
        for rd in transcript.rounds:
            for sp in rd.get("speeches", []):
                # Keep first 100 chars of each speech
                highlights.append(
                    f"{sp.get('seat_name', 'Unknown')}: {sp.get('speech', '')[:100]}"
                )

        return "\n".join(highlights[:10])  # Top 10 highlights

    @staticmethod
    def _fallback_render(view_name: str, conclusion_data: dict) -> str:
        """Fallback rendering when LLM fails."""
        summary = conclusion_data.get("summary", "无结论")
        decision = conclusion_data.get("decision", "unknown")

        if view_name == "dramatic":
            return f"议会已经做出了裁决——「{decision}」。{summary}"
        elif view_name == "practical":
            reasons = "\n".join(
                f"- {r}" for r in conclusion_data.get("main_reasons", [])
            )
            return f"决策：{decision}\n\n主要原因：\n{reasons}"
        else:  # psychological
            return f"从心理分析角度看，这次讨论反映了深层的情绪模式。结论：{decision}。{summary}"
