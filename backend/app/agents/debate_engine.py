"""Debate Engine - Multi-round debate orchestration."""

import logging
from datetime import datetime

from ..core.llm import LLMClient
from ..models.seat import SeatConfig, SeatState, SeatStance, SeatAction
from ..models.council import DebateTranscript, VoteMap
from ..services.bell_engine import BellEngine
from .seat_agent import SeatAgent

logger = logging.getLogger(__name__)


class DebateEngine:
    """Orchestrates multi-round debates among visible seats."""

    def __init__(self, llm_client: LLMClient, bell_engine: BellEngine):
        self.seat_agent = SeatAgent(llm_client)
        self.bell_engine = bell_engine

    async def run_debate(
        self,
        visible_seat_configs: list[SeatConfig],
        seat_states: dict[str, SeatState],
        rounds: int,
        proposal: str,
    ) -> tuple[DebateTranscript, VoteMap]:
        """Run multi-round debate and return transcript + vote map."""
        transcript = DebateTranscript()
        vote_map = VoteMap()

        for round_num in range(1, rounds + 1):
            logger.info(f"Starting debate round {round_num}")

            # Determine speaking order
            speaking_order = self._determine_speaking_order(
                visible_seat_configs, seat_states, round_num
            )

            round_speeches = []
            for seat_config in speaking_order:
                seat_id = seat_config.seat_id
                seat_state = seat_states.get(seat_id)
                if not seat_state:
                    continue

                # Skip fractured seats
                if seat_state.status.value == "fractured":
                    logger.info(f"Seat {seat_config.name} is fractured, skipping")
                    continue

                # Build debate context
                debate_context = self._build_debate_context(transcript, round_num)

                # Generate speech
                action = await self.seat_agent.generate_speech(
                    seat_config=seat_config,
                    seat_state=seat_state,
                    proposal=proposal,
                    debate_context=debate_context,
                )

                # Update seat state
                seat_state.current_stance = action.intent
                seat_state.confidence = action.confidence

                # Update bell state
                bell_event = self._calculate_bell_event(action, seat_state)
                if bell_event:
                    seat_state.stress = max(0, min(100, seat_state.stress + bell_event))
                    seat_state.bell_health = max(
                        0, min(100, seat_state.bell_health - bell_event // 2)
                    )

                # Record speech
                speech_record = {
                    "seat_id": seat_id,
                    "seat_name": seat_config.name,
                    "speech": action.speech,
                    "stance": action.intent.value,
                    "confidence": action.confidence,
                    "round": round_num,
                }
                round_speeches.append(speech_record)
                logger.info(
                    f"{seat_config.name} ({action.intent.value}): {action.speech[:50]}..."
                )

            # Add round to transcript
            transcript.rounds.append(
                {
                    "round_num": round_num,
                    "speeches": round_speeches,
                }
            )
            transcript.total_speeches += len(round_speeches)

        # Tally final votes
        vote_map = self._tally_votes(seat_states, visible_seat_configs)

        return transcript, vote_map

    def _determine_speaking_order(
        self,
        seat_configs: list[SeatConfig],
        seat_states: dict[str, SeatState],
        round_num: int,
    ) -> list[SeatConfig]:
        """Determine speaking order: stressed seats first, then alternate stances."""
        if round_num == 1:
            # First round: sort by bell_health ascending (most stressed first)
            return sorted(
                seat_configs,
                key=lambda s: seat_states.get(
                    s.seat_id, SeatState(seat_id=s.seat_id, name=s.name)
                ).bell_health,
            )
        else:
            # Later rounds: alternate approve/oppose
            approve_seats = [
                s
                for s in seat_configs
                if seat_states.get(
                    s.seat_id, SeatState(seat_id=s.seat_id, name=s.name)
                ).current_stance
                == SeatStance.APPROVE
            ]
            oppose_seats = [
                s
                for s in seat_configs
                if seat_states.get(
                    s.seat_id, SeatState(seat_id=s.seat_id, name=s.name)
                ).current_stance
                == SeatStance.OPPOSE
            ]
            abstain_seats = [
                s
                for s in seat_configs
                if seat_states.get(
                    s.seat_id, SeatState(seat_id=s.seat_id, name=s.name)
                ).current_stance
                == SeatStance.ABSTAIN
            ]

            # Alternate
            order = []
            max_len = max(len(approve_seats), len(oppose_seats), len(abstain_seats))
            for i in range(max_len):
                if i < len(oppose_seats):
                    order.append(oppose_seats[i])
                if i < len(approve_seats):
                    order.append(approve_seats[i])
                if i < len(abstain_seats):
                    order.append(abstain_seats[i])

            return order if order else seat_configs

    def _build_debate_context(
        self, transcript: DebateTranscript, current_round: int
    ) -> str:
        """Build debate context from previous speeches."""
        if not transcript.rounds:
            return ""

        context_parts = []
        for rd in transcript.rounds:
            round_num = rd["round_num"]
            speeches = rd["speeches"]
            context_parts.append(f"【第{round_num}轮】")
            for sp in speeches:
                context_parts.append(
                    f"{sp['seat_name']}({sp['stance']}): {sp['speech'][:150]}"
                )

        return "\n".join(context_parts)

    def _calculate_bell_event(self, action: SeatAction, seat_state: SeatState) -> int:
        """Calculate stress delta from speech."""
        stress = 0
        # Higher confidence = more stress (strong stance)
        if action.confidence > 0.8:
            stress += 5
        # Opposing stance in a debate adds stress
        if action.intent == SeatStance.OPPOSE:
            stress += 3
        # Existing stress amplifies
        if seat_state.stress > 60:
            stress += 2
        return stress

    def _tally_votes(
        self,
        seat_states: dict[str, SeatState],
        seat_configs: list[SeatConfig],
    ) -> VoteMap:
        """Tally final votes from seat states."""
        vote_map = VoteMap()
        for config in seat_configs:
            state = seat_states.get(config.seat_id)
            if not state:
                continue
            if state.current_stance == SeatStance.APPROVE:
                vote_map.approve += 1
            elif state.current_stance == SeatStance.OPPOSE:
                vote_map.oppose += 1
            else:
                vote_map.abstain += 1
        return vote_map
