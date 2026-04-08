"""Seat Agent - Per-seat LLM interactions for prevotes and debate speeches."""

import json
import logging
from typing import Any

from ..core.llm import LLMClient
from ..models.seat import (
    SeatConfig,
    SeatState,
    SeatPrevote,
    SeatAction,
    SeatStance,
    SeatActionType,
)
from ..models.council import DebateTranscript
from .prompts import (
    PREVOTE_SYSTEM_PROMPT,
    PREVOTE_USER_PROMPT,
    DEBATE_SYSTEM_PROMPT,
    DEBATE_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class SeatAgent:
    """Agent for individual seat interactions."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def generate_prevote(
        self,
        seat_config: SeatConfig,
        user_input: str,
    ) -> SeatPrevote:
        """Generate a pre-vote for a seat."""
        try:
            system_prompt = self._build_prevote_system_prompt(seat_config)
            user_prompt = PREVOTE_USER_PROMPT.format(user_input=user_input)

            response = await self.llm.call_fast(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
            )

            return self._parse_prevote_response(response, seat_config.seat_id)
        except Exception as e:
            logger.warning(f"Prevote generation failed for {seat_config.name}: {e}")
            return self._fallback_prevote(seat_config.seat_id)

    async def generate_speech(
        self,
        seat_config: SeatConfig,
        seat_state: SeatState,
        proposal: str,
        debate_context: str,
    ) -> SeatAction:
        """Generate a debate speech for a seat."""
        try:
            system_prompt = self._build_debate_system_prompt(seat_config, seat_state)
            user_prompt = DEBATE_USER_PROMPT.format(
                proposal=proposal,
                debate_context=(
                    debate_context
                    if debate_context
                    else "辩论刚刚开始，你是第一位发言者。"
                ),
            )

            response = await self.llm.call_strong(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.8,
            )

            return self._parse_speech_response(
                response, seat_config.seat_id, seat_state.current_stance
            )
        except Exception as e:
            logger.warning(f"Speech generation failed for {seat_config.name}: {e}")
            return self._fallback_speech(seat_config.seat_id, seat_state.current_stance)

    def _build_prevote_system_prompt(self, config: SeatConfig) -> str:
        """Build system prompt for pre-vote with seat persona."""
        return PREVOTE_SYSTEM_PROMPT.format(
            seat_name=config.name,
            core_belief=config.core_belief,
            trait_logic=config.traits.get("logic", 0.5),
            trait_empathy=config.traits.get("empathy", 0.5),
            trait_risk=config.traits.get("risk_aversion", 0.5),
            trait_longterm=config.traits.get("long_termism", 0.5),
            tone_style=self._format_tone(config.tone),
            example_phrases="\n".join(f"- {p}" for p in config.example_phrases[:3]),
        )

    def _build_debate_system_prompt(self, config: SeatConfig, state: SeatState) -> str:
        """Build system prompt for debate speech with seat persona and state."""
        return DEBATE_SYSTEM_PROMPT.format(
            seat_name=config.name,
            core_belief=config.core_belief,
            trait_logic=config.traits.get("logic", 0.5),
            trait_empathy=config.traits.get("empathy", 0.5),
            trait_risk=config.traits.get("risk_aversion", 0.5),
            trait_longterm=config.traits.get("long_termism", 0.5),
            tone_style=self._format_tone(config.tone),
            example_phrases="\n".join(f"- {p}" for p in config.example_phrases[:3]),
            current_stance=state.current_stance.value,
            confidence=state.confidence,
            bell_health=state.bell_health,
            stress=state.stress,
        )

    @staticmethod
    def _format_tone(tone: dict) -> str:
        """Format tone dict into readable string."""
        if not tone:
            return "中性、客观"
        parts = []
        for key, val in tone.items():
            parts.append(f"{key}: {val}")
        return "，".join(parts[:3])

    @staticmethod
    def _parse_prevote_response(response: str, seat_id: str) -> SeatPrevote:
        """Parse LLM response into SeatPrevote."""
        try:
            json_str = SeatAgent._extract_json(response)
            if not json_str:
                logger.warning(f"No JSON found in prevote response for {seat_id}")
                return SeatAgent._fallback_prevote(seat_id)

            data = json.loads(json_str)

            # Validate required fields
            if "stance" not in data:
                logger.warning(
                    f"Missing 'stance' field in prevote response for {seat_id}"
                )
                return SeatAgent._fallback_prevote(seat_id)

            stance_str = data.get("stance", "abstain").lower().strip()
            stance_map = {
                "approve": SeatStance.APPROVE,
                "oppose": SeatStance.OPPOSE,
                "abstain": SeatStance.ABSTAIN,
            }
            stance = stance_map.get(stance_str, SeatStance.ABSTAIN)

            return SeatPrevote(
                seat_id=seat_id,
                stance=stance,
                confidence=float(data.get("confidence", 0.5)),
                stress_hint=int(data.get("stress_hint", 0)),
                risk_assessment=data.get("risk_assessment", ""),
            )
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse prevote response for {seat_id}: {e}")
            return SeatAgent._fallback_prevote(seat_id)

    @staticmethod
    def _parse_speech_response(
        response: str, seat_id: str, current_stance: SeatStance
    ) -> SeatAction:
        """Parse LLM response into SeatAction."""
        # For debate, the response is primarily text (the speech)
        # Try to extract stance if present
        stance = current_stance
        confidence = 0.6

        json_str = SeatAgent._extract_json(response)
        if json_str and json_str.startswith("{"):
            try:
                data = json.loads(json_str)
                stance_str = data.get("stance", "").lower()
                if stance_str in ("approve", "oppose", "abstain"):
                    stance_map = {
                        "approve": SeatStance.APPROVE,
                        "oppose": SeatStance.OPPOSE,
                        "abstain": SeatStance.ABSTAIN,
                    }
                    stance = stance_map[stance_str]
                confidence = float(data.get("confidence", 0.6))
            except json.JSONDecodeError:
                pass

        # Use the full response as speech text (minus any JSON block)
        speech = response
        if json_str:
            speech = response.replace(json_str, "").strip()
            if not speech:
                speech = response  # Fallback to full response

        return SeatAction(
            seat_id=seat_id,
            intent=stance,
            confidence=confidence,
            proposed_action=SeatActionType.SPEAK,
            speech=speech[:500],  # Limit length
        )

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from text, handling markdown code blocks."""
        # Try to find JSON in markdown code block
        import re

        # Pattern 1: JSON inside ```json ... ```
        json_block_match = re.search(r"```json\s*\n(.*?)\n\s*```", text, re.DOTALL)
        if json_block_match:
            return json_block_match.group(1).strip()

        # Pattern 2: JSON inside ``` ... ``` (without language tag)
        generic_block_match = re.search(r"```\s*\n(.*?)\n\s*```", text, re.DOTALL)
        if generic_block_match:
            return generic_block_match.group(1).strip()

        # Pattern 3: Raw JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start : end + 1]

        return ""

    @staticmethod
    def _fallback_prevote(seat_id: str) -> SeatPrevote:
        """Fallback pre-vote when LLM fails."""
        return SeatPrevote(
            seat_id=seat_id,
            stance=SeatStance.ABSTAIN,
            confidence=0.3,
            stress_hint=0,
            risk_assessment="信息不足，暂无法判断",
        )

    @staticmethod
    def _fallback_speech(seat_id: str, stance: SeatStance) -> SeatAction:
        """Fallback speech when LLM fails."""
        stance_text = {
            SeatStance.APPROVE: "支持",
            SeatStance.OPPOSE: "反对",
            SeatStance.ABSTAIN: "弃权",
        }
        return SeatAction(
            seat_id=seat_id,
            intent=stance,
            confidence=0.3,
            proposed_action=SeatActionType.SPEAK,
            speech=f"[系统] 由于技术原因，我暂时无法详细表达。我当前的立场是{stance_text.get(stance, '中立')}。",
        )
