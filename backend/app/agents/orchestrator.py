"""Orchestrator - Main state machine for the 10-step council workflow."""

import logging
import asyncio
from datetime import datetime
from typing import Any

from ..core.llm import LLMClient
from ..core.config import settings
from ..models.council import (
    CouncilMode,
    OrchestratorState,
    CouncilState,
    VoteMap,
    PerceptionResult,
    FlowPlan,
    DebateTranscript,
    CouncilConclusion,
    CouncilResponse,
    UICommand,
    MemoryWrite,
)
from ..models.seat import SeatConfig, SeatState, SeatStance
from ..models.api import SubmitProposalRequest
from ..models.memory import UserProfile, SessionMemory
from ..models.personas import load_all_seats
from ..services.memory_service import MemoryService
from ..services.knife_engine import KnifeEngine
from ..services.bell_engine import BellEngine

from .perceiver import Perceiver
from .planner import Planner
from .seat_agent import SeatAgent
from .debate_engine import DebateEngine
from .renderer import Renderer
from .safety_layer import SafetyLayer
from .prompts import CONCLUDE_SYSTEM_PROMPT, CONCLUDE_USER_PROMPT

logger = logging.getLogger(__name__)


class CouncilOrchestrator:
    """Main orchestrator for the council deliberation workflow."""

    def __init__(
        self,
        llm_client: LLMClient,
        memory_service: MemoryService,
        knife_engine: KnifeEngine,
        bell_engine: BellEngine,
    ):
        self.llm = llm_client
        self.memory = memory_service
        self.knife_engine = knife_engine
        self.bell_engine = bell_engine

        # Initialize agents
        self.perceiver = Perceiver(llm_client)
        self.planner = Planner()
        self.safety_layer = SafetyLayer(llm_client)
        self.seat_agent = SeatAgent(llm_client)
        self.debate_engine = DebateEngine(llm_client, bell_engine)
        self.renderer = Renderer(llm_client)

        # Load personas
        self.all_seats: list[SeatConfig] = load_all_seats()
        self.seat_states: dict[str, SeatState] = {}
        for seat in self.all_seats:
            self.seat_states[seat.seat_id] = SeatState(
                seat_id=seat.seat_id,
                name=seat.name,
                config=seat,
            )

    async def process_input(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
    ) -> CouncilResponse:
        """Main entry point - processes user input through the full workflow."""
        logger.info(f"Processing input for session {session_id}: {user_input[:50]}...")

        council_state = CouncilState()
        ui_commands: list[UICommand] = []
        memory_updates: list[MemoryWrite] = []
        transcript: DebateTranscript | None = None
        conclusion: CouncilConclusion | None = None

        try:
            # Step 1: PERCEIVE
            council_state.orchestrator_state = OrchestratorState.PERCEIVING
            perception = await self.perceiver.perceive(user_input)
            logger.info(
                f"Perception: task_type={perception.task_type}, risks={perception.risk_flags}"
            )

            # Safety check
            is_risky, risk_flags = self.safety_layer.is_high_risk(user_input)
            if (
                is_risky
                or "self_harm" in str(perception.risk_flags)
                or "suicide" in str(perception.risk_flags).lower()
            ):
                logger.warning("High risk input detected, switching to safety mode")
                council_state.mode = CouncilMode.SAFETY_MODE
                safe_response = await self.safety_layer.generate_safe_response(
                    user_input
                )
                conclusion = CouncilConclusion(
                    summary=safe_response,
                    decision="delay",
                    main_reasons=["安全风险"],
                    risks=["用户输入包含高风险内容"],
                    next_steps=["建议寻求专业帮助"],
                    minority_opinion="",
                )
                return CouncilResponse(
                    session_id=session_id,
                    mode="safety_mode",
                    conclusion=conclusion,
                    council_state=council_state,
                )

            # Step 2: RETRIEVE
            council_state.orchestrator_state = OrchestratorState.RETRIEVING
            user_profile = await self.memory.get_user_profile(user_id)
            memory_context = await self.memory.build_context(
                user_id=user_id,
                user_input=user_input,
            )
            logger.info(f"Retrieved user profile: {user_id}")

            # Step 3: PLAN
            council_state.orchestrator_state = OrchestratorState.PLANNING
            flow_plan = self.planner.plan(perception, user_profile)
            council_state.mode = CouncilMode(flow_plan.mode)
            council_state.round = flow_plan.rounds
            logger.info(
                f"Flow plan: mode={flow_plan.mode}, rounds={flow_plan.rounds}, knife={flow_plan.need_knife}"
            )

            # Branch based on mode
            if flow_plan.mode == "light_chat":
                # Light chat: quick response
                council_state.orchestrator_state = OrchestratorState.LIGHT_COUNCIL
                conclusion = await self._generate_light_response(
                    user_input, perception, memory_context
                )
            elif flow_plan.mode == "safety_mode":
                conclusion = CouncilConclusion(
                    summary="检测到潜在风险，请优先关注情绪状态。",
                    decision="delay",
                    main_reasons=["安全考虑"],
                    risks=["需要关注用户心理状态"],
                    next_steps=["建议温和引导"],
                    minority_opinion="",
                )
            else:
                # Full council deliberation
                council_state.orchestrator_state = OrchestratorState.FULL_COUNCIL
                conclusion, transcript, ui_commands, memory_updates = (
                    await self._run_full_council(
                        session_id, user_input, perception, flow_plan, council_state
                    )
                )

            # Step: RENDER (multi-view)
            council_state.orchestrator_state = OrchestratorState.RENDERING
            if conclusion and transcript:
                views = await self.renderer.render_all(
                    conclusion, transcript, perception
                )
                ui_commands.append(
                    UICommand(
                        command_type="show_views",
                        payload={"views": views},
                    )
                )

            # Step: ARCHIVE
            council_state.orchestrator_state = OrchestratorState.OUTPUT
            await self._archive_case(
                user_id, session_id, user_input, conclusion, perception
            )

        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            conclusion = CouncilConclusion(
                summary="很抱歉，议会系统遇到了一个技术问题。请稍后再试。",
                decision="delay",
                main_reasons=["系统错误"],
                risks=[str(e)],
                next_steps=["重试"],
                minority_opinion="",
            )
            council_state.orchestrator_state = OrchestratorState.OUTPUT

        council_state.updated_at = datetime.now()

        return CouncilResponse(
            session_id=session_id,
            mode=council_state.mode.value,
            transcript=transcript,
            conclusion=conclusion or CouncilConclusion(summary="无结论"),
            council_state=council_state,
            ui_commands=ui_commands,
            memory_updates=memory_updates,
        )

    async def _run_full_council(
        self,
        session_id: str,
        user_input: str,
        perception: PerceptionResult,
        flow_plan: FlowPlan,
        council_state: CouncilState,
    ) -> tuple[CouncilConclusion, DebateTranscript, list[UICommand], list[MemoryWrite]]:
        """Run the full 23→12 council deliberation."""
        ui_commands: list[UICommand] = []
        memory_updates: list[MemoryWrite] = []

        # Step 4: PREVOTE_23
        council_state.orchestrator_state = OrchestratorState.PREVOTING_23
        logger.info("Running 23-seat pre-vote...")
        prevotes = await self._run_prevotes(self.all_seats, user_input)
        council_state.knife_risk = 0.3  # Default risk
        logger.info(f"Pre-votes complete: {len(prevotes)} seats responded")

        # Step 5: KNIFE
        council_state.orchestrator_state = OrchestratorState.KNIFE_CUTTING
        if flow_plan.need_knife and len(prevotes) >= 12:
            knife_result = await self.knife_engine.execute_cut(
                all_seats=self.all_seats,
                prevotes=prevotes,
                cut_mode=flow_plan.mode,
                issue_type=perception.task_type,
            )
            visible_ids = knife_result.visible_seats
            hidden_ids = knife_result.hidden_seats
            council_state.knife_risk = knife_result.cut_risk

            ui_commands.append(
                UICommand(
                    command_type="knife_cut",
                    payload={
                        "visible_seats": visible_ids,
                        "hidden_seats": hidden_ids,
                        "cut_risk": knife_result.cut_risk,
                    },
                )
            )
            logger.info(
                f"Knife cut: {len(visible_ids)} visible, {len(hidden_ids)} hidden"
            )
        else:
            # No knife, use first 12 seats
            visible_ids = [s.seat_id for s in self.all_seats[:12]]
            hidden_ids = [s.seat_id for s in self.all_seats[12:]]

        council_state.visible_seats = visible_ids
        council_state.hidden_seats = hidden_ids

        # Get visible seat configs and states
        visible_configs = [s for s in self.all_seats if s.seat_id in visible_ids]
        visible_states = {
            sid: self.seat_states[sid] for sid in visible_ids if sid in self.seat_states
        }

        # Update prevote stances into seat states
        for prevote in prevotes:
            if prevote.seat_id in self.seat_states:
                self.seat_states[prevote.seat_id].current_stance = prevote.stance
                self.seat_states[prevote.seat_id].confidence = prevote.confidence

        # Step 6: DEBATE_12
        council_state.orchestrator_state = OrchestratorState.DEBATING_12
        rounds = max(flow_plan.rounds, 2)  # At least 2 rounds for full council
        logger.info(
            f"Starting debate with {len(visible_configs)} seats, {rounds} rounds..."
        )

        transcript, vote_map = await self.debate_engine.run_debate(
            visible_seat_configs=visible_configs,
            seat_states=visible_states,
            rounds=rounds,
            proposal=user_input,
        )
        council_state.vote_map = vote_map
        council_state.tension_level = min(1.0, transcript.total_speeches / 20.0)
        logger.info(f"Debate complete: {transcript.total_speeches} speeches")

        # Step 7: VOTE
        council_state.orchestrator_state = OrchestratorState.VOTING
        # Vote map already computed from debate

        # Step 8: EVALUATE
        council_state.orchestrator_state = OrchestratorState.EVALUATING
        total_votes = vote_map.approve + vote_map.oppose + vote_map.abstain
        if total_votes > 0:
            majority_ratio = max(vote_map.approve, vote_map.oppose) / total_votes
            if majority_ratio < 0.6:
                logger.info("Split vote detected, high minority ratio")

        # Step 9: CONCLUDE
        council_state.orchestrator_state = OrchestratorState.CONCLUDING
        conclusion = await self._generate_conclusion(user_input, transcript, vote_map)

        return conclusion, transcript, ui_commands, memory_updates

    async def _run_prevotes(self, seats: list[SeatConfig], user_input: str) -> list:
        """Run pre-votes for all seats in parallel."""
        from ..models.seat import SeatPrevote

        async def prevote_seat(seat: SeatConfig) -> SeatPrevote:
            return await self.seat_agent.generate_prevote(seat, user_input)

        # Limit concurrency to avoid rate limits
        semaphore = asyncio.Semaphore(5)

        async def limited_prevote(seat: SeatConfig) -> SeatPrevote:
            async with semaphore:
                return await prevote_seat(seat)

        tasks = [limited_prevote(seat) for seat in seats]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and use fallbacks
        prevotes = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Prevote failed for {seats[i].name}: {result}")
                prevotes.append(SeatPrevote(seat_id=seats[i].seat_id))
            else:
                prevotes.append(result)

        return prevotes

    async def _generate_conclusion(
        self,
        proposal: str,
        transcript: DebateTranscript,
        vote_map: VoteMap,
    ) -> CouncilConclusion:
        """Generate conclusion from debate transcript."""
        try:
            # Build transcript summary
            transcript_text = self._format_transcript(transcript)

            system_prompt = CONCLUDE_SYSTEM_PROMPT
            user_prompt = CONCLUDE_USER_PROMPT.format(
                proposal=proposal,
                transcript=transcript_text,
                approve_count=vote_map.approve,
                oppose_count=vote_map.oppose,
                abstain_count=vote_map.abstain,
            )

            response = await self.llm.call_strong(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
            )

            # Parse JSON response
            json_str = self._extract_json(response)
            if json_str:
                import json

                data = json.loads(json_str)
                return CouncilConclusion(
                    summary=data.get("summary", ""),
                    decision=data.get("decision", "conditional"),
                    main_reasons=data.get("main_reasons", []),
                    risks=data.get("risks", []),
                    next_steps=data.get("next_steps", []),
                    minority_opinion=data.get("minority_opinion", ""),
                    vote_result=vote_map,
                )
        except Exception as e:
            logger.warning(f"Conclusion generation failed: {e}")

        # Fallback conclusion
        return CouncilConclusion(
            summary="议会已就议题进行了讨论。",
            decision="conditional",
            main_reasons=["综合各方意见"],
            risks=["存在不同观点"],
            next_steps=["建议综合考虑多方意见"],
            minority_opinion="少数席位持保留意见",
            vote_result=vote_map,
        )

    async def _generate_light_response(
        self,
        user_input: str,
        perception: PerceptionResult,
        memory_context: dict,
    ) -> CouncilConclusion:
        """Generate a light chat response."""
        try:
            context = f"用户议题：{user_input}\n\n感知结果：{perception.task_type}"
            if memory_context.get("similar_cases"):
                context += (
                    f"\n\n历史案例：{len(memory_context['similar_cases'])} 个相关案例"
                )

            response = await self.llm.call_fast(
                system_prompt="你是一个群鸟议会的主持人。请简洁地回应用户的议题，200字以内。",
                user_prompt=context,
                temperature=0.7,
            )

            return CouncilConclusion(
                summary=response.strip(),
                decision="conditional",
                main_reasons=[],
                risks=[],
                next_steps=[],
                minority_opinion="",
            )
        except Exception as e:
            logger.warning(f"Light response failed: {e}")
            return CouncilConclusion(
                summary="议会收到了你的议题。",
                decision="conditional",
                main_reasons=[],
                risks=[],
                next_steps=[],
                minority_opinion="",
            )

    async def _archive_case(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        conclusion: CouncilConclusion | None,
        perception: PerceptionResult | None,
    ):
        """Archive the case to memory."""
        try:
            from ..models.memory import CaseRecord
            import uuid

            case_record = CaseRecord(
                case_id=str(uuid.uuid4()),
                user_id=user_id,
                proposal_title=user_input[:100] if user_input else "Unknown",
                conclusion=conclusion.summary if conclusion else "",
                minority_opinion=None,
                triggered_reconsider=False,
                triggered_fracture=False,
            )
            await self.memory.archive_case(case_record)
        except Exception as e:
            logger.warning(f"Failed to archive case: {e}")

    @staticmethod
    def _format_transcript(transcript: DebateTranscript) -> str:
        """Format transcript for LLM consumption."""
        parts = []
        for rd in transcript.rounds:
            parts.append(f"=== 第{rd['round_num']}轮 ===")
            for sp in rd.get("speeches", []):
                parts.append(f"{sp['seat_name']}({sp['stance']}): {sp['speech']}")
        return "\n".join(parts)

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from text."""
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start : end + 1]
        return ""
