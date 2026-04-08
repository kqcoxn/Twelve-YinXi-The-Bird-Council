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
    TokenUsage,
)
from ..models.seat import SeatConfig, SeatState, SeatStance
from ..models.api import SubmitProposalRequest
from ..models.memory import UserProfile, SessionMemory
from ..models.personas import load_all_seats
from ..services.memory_service import MemoryService
from ..services.knife_engine import KnifeEngine
from ..services.bell_engine import BellEngine
from ..services.websocket_manager import websocket_manager

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
        total_token_usage = TokenUsage()

        try:
            # Send start event
            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "council_started",
                    "payload": {
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                },
            )

            # Step 1: PERCEIVE
            council_state.orchestrator_state = OrchestratorState.PERCEIVING
            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "step_started",
                    "payload": {"step": "perceiving", "message": "感知用户意图..."},
                },
            )

            perception = await self.perceiver.perceive(user_input)
            logger.info(
                f"Perception: task_type={perception.task_type}, risks={perception.risk_flags}"
            )

            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "step_completed",
                    "payload": {"step": "perceiving", "result": perception.dict()},
                },
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

                await websocket_manager.send_to_session(
                    session_id,
                    {
                        "type": "safety_mode",
                        "payload": {"message": "检测到安全风险，已切换到安全模式"},
                    },
                )

                return CouncilResponse(
                    session_id=session_id,
                    mode="safety_mode",
                    conclusion=conclusion,
                    council_state=council_state,
                )

            # Step 2: RETRIEVE
            council_state.orchestrator_state = OrchestratorState.RETRIEVING
            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "step_started",
                    "payload": {"step": "retrieving", "message": "检索历史记忆..."},
                },
            )

            user_profile = await self.memory.get_user_profile(user_id)
            memory_context = await self.memory.build_context(
                user_id=user_id,
                user_input=user_input,
            )
            logger.info(f"Retrieved user profile: {user_id}")

            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "step_completed",
                    "payload": {"step": "retrieving"},
                },
            )

            # Step 3: PLAN
            council_state.orchestrator_state = OrchestratorState.PLANNING
            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "step_started",
                    "payload": {"step": "planning", "message": "规划议会流程..."},
                },
            )

            flow_plan = self.planner.plan(perception, user_profile)
            council_state.mode = CouncilMode(flow_plan.mode)
            council_state.round = flow_plan.rounds
            logger.info(
                f"Flow plan: mode={flow_plan.mode}, rounds={flow_plan.rounds}, knife={flow_plan.need_knife}"
            )

            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "step_completed",
                    "payload": {
                        "step": "planning",
                        "result": {"mode": flow_plan.mode, "rounds": flow_plan.rounds},
                    },
                },
            )

            # Branch based on mode
            if flow_plan.mode == "light_chat":
                # Light chat: quick response
                council_state.orchestrator_state = OrchestratorState.LIGHT_COUNCIL
                await websocket_manager.send_to_session(
                    session_id,
                    {
                        "type": "mode_changed",
                        "payload": {"mode": "light_chat", "message": "快速响应模式"},
                    },
                )
                conclusion, tokens = await self._generate_light_response(
                    user_input, perception, memory_context
                )
                total_token_usage.add(tokens)
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
                await websocket_manager.send_to_session(
                    session_id,
                    {
                        "type": "mode_changed",
                        "payload": {"mode": "full_council", "message": "完整议会模式"},
                    },
                )
                conclusion, transcript, ui_commands, memory_updates, council_tokens = (
                    await self._run_full_council(
                        session_id, user_input, perception, flow_plan, council_state
                    )
                )
                total_token_usage.add(council_tokens)

            # Step: RENDER (multi-view)
            council_state.orchestrator_state = OrchestratorState.RENDERING
            if conclusion and transcript:
                await websocket_manager.send_to_session(
                    session_id,
                    {
                        "type": "step_started",
                        "payload": {
                            "step": "rendering",
                            "message": "生成多视图输出...",
                        },
                    },
                )

                views = await self.renderer.render_all(
                    conclusion, transcript, perception
                )
                ui_commands.append(
                    UICommand(
                        command_type="show_views",
                        payload={"views": views},
                    )
                )

                await websocket_manager.send_to_session(
                    session_id,
                    {
                        "type": "views_ready",
                        "payload": {"views": list(views.keys())},
                    },
                )

            # Step: ARCHIVE
            council_state.orchestrator_state = OrchestratorState.OUTPUT
            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "council_completed",
                    "payload": {
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                },
            )

            await self._archive_case(
                user_id, session_id, user_input, conclusion, perception
            )

        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)

            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "error",
                    "payload": {
                        "message": str(e),
                        "timestamp": datetime.now().isoformat(),
                    },
                },
            )

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
            token_usage=total_token_usage,
        )

    async def _run_full_council(
        self,
        session_id: str,
        user_input: str,
        perception: PerceptionResult,
        flow_plan: FlowPlan,
        council_state: CouncilState,
    ) -> tuple[
        CouncilConclusion,
        DebateTranscript,
        list[UICommand],
        list[MemoryWrite],
        TokenUsage,
    ]:
        """Run the full 23→12 council deliberation. Returns (conclusion, transcript, ui_commands, memory_updates, token_usage)."""
        ui_commands: list[UICommand] = []
        memory_updates: list[MemoryWrite] = []
        total_token_usage = TokenUsage()

        # Step 4: PREVOTE_23
        council_state.orchestrator_state = OrchestratorState.PREVOTING_23
        await websocket_manager.send_to_session(
            session_id,
            {
                "type": "step_started",
                "payload": {"step": "prevoting_23", "message": "23席预判中..."},
            },
        )

        logger.info("Running 23-seat pre-vote...")
        prevotes = await self._run_prevotes(self.all_seats, user_input, session_id)
        council_state.knife_risk = 0.3  # Default risk
        logger.info(f"Pre-votes complete: {len(prevotes)} seats responded")

        await websocket_manager.send_to_session(
            session_id,
            {
                "type": "step_completed",
                "payload": {
                    "step": "prevoting_23",
                    "result": {"seats_responded": len(prevotes)},
                },
            },
        )

        # Step 5: KNIFE
        council_state.orchestrator_state = OrchestratorState.KNIFE_CUTTING
        if flow_plan.need_knife and len(prevotes) >= 12:
            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "step_started",
                    "payload": {"step": "knife_cutting", "message": "餐刀切分中..."},
                },
            )

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

            # Send knife cut event via WebSocket
            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "knife_cut",
                    "payload": {
                        "visible_seats": visible_ids,
                        "hidden_seats": hidden_ids,
                        "cut_risk": knife_result.cut_risk,
                    },
                },
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

        await websocket_manager.send_to_session(
            session_id,
            {
                "type": "step_started",
                "payload": {
                    "step": "debating_12",
                    "message": f"12席辩论开始 ({rounds}轮)...",
                },
            },
        )

        transcript, vote_map = await self.debate_engine.run_debate(
            visible_seat_configs=visible_configs,
            seat_states=visible_states,
            rounds=rounds,
            proposal=user_input,
            session_id=session_id,  # Pass session_id for WebSocket events
        )
        council_state.vote_map = vote_map
        council_state.tension_level = min(1.0, transcript.total_speeches / 20.0)
        logger.info(f"Debate complete: {transcript.total_speeches} speeches")

        await websocket_manager.send_to_session(
            session_id,
            {
                "type": "step_completed",
                "payload": {
                    "step": "debating_12",
                    "result": {"total_speeches": transcript.total_speeches},
                },
            },
        )

        # Step 7: VOTE
        council_state.orchestrator_state = OrchestratorState.VOTING
        await websocket_manager.send_to_session(
            session_id,
            {
                "type": "vote_update",
                "payload": {
                    "vote_map": {
                        "approve": vote_map.approve,
                        "oppose": vote_map.oppose,
                        "abstain": vote_map.abstain,
                    }
                },
            },
        )
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
        await websocket_manager.send_to_session(
            session_id,
            {
                "type": "step_started",
                "payload": {"step": "concluding", "message": "生成结论中..."},
            },
        )

        conclusion, tokens = await self._generate_conclusion(
            user_input, transcript, vote_map
        )
        total_token_usage.add(tokens)

        await websocket_manager.send_to_session(
            session_id,
            {
                "type": "conclusion",
                "payload": {"conclusion": conclusion.dict()},
            },
        )

        return conclusion, transcript, ui_commands, memory_updates, total_token_usage

    async def _run_prevotes(
        self, seats: list[SeatConfig], user_input: str, session_id: str = None
    ) -> list:
        """Run pre-votes for all seats in parallel."""
        from ..models.seat import SeatPrevote

        async def prevote_seat(seat: SeatConfig) -> SeatPrevote:
            return await self.seat_agent.generate_prevote(seat, user_input)

        # Limit concurrency to avoid rate limits
        semaphore = asyncio.Semaphore(5)

        async def limited_prevote(seat: SeatConfig) -> SeatPrevote:
            async with semaphore:
                result = await prevote_seat(seat)
                # Send individual seat prevote event if session_id provided
                if session_id:
                    await websocket_manager.send_to_session(
                        session_id,
                        {
                            "type": "seat_prevote",
                            "payload": {
                                "seat_id": seat.seat_id,
                                "seat_name": seat.name,
                                "stance": (
                                    result.stance.value if result.stance else "abstain"
                                ),
                                "confidence": result.confidence,
                            },
                        },
                    )
                return result

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
    ) -> tuple[CouncilConclusion, TokenUsage]:
        """Generate conclusion from debate transcript. Returns (conclusion, token_usage)."""
        token_usage = TokenUsage()
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

            response, tokens = await self.llm.call_strong(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
            )
            token_usage.add(tokens)

            # Parse JSON response
            json_str = self._extract_json(response)
            if json_str:
                import json

                data = json.loads(json_str)
                return (
                    CouncilConclusion(
                        summary=data.get("summary", ""),
                        decision=data.get("decision", "conditional"),
                        main_reasons=data.get("main_reasons", []),
                        risks=data.get("risks", []),
                        next_steps=data.get("next_steps", []),
                        minority_opinion=data.get("minority_opinion", ""),
                        vote_result=vote_map,
                    ),
                    token_usage,
                )
        except Exception as e:
            logger.warning(f"Conclusion generation failed: {e}")

        # Fallback conclusion
        return (
            CouncilConclusion(
                summary="议会已就议题进行了讨论。",
                decision="conditional",
                main_reasons=["综合各方意见"],
                risks=["存在不同观点"],
                next_steps=["建议综合考虑多方意见"],
                minority_opinion="少数席位持保留意见",
                vote_result=vote_map,
            ),
            token_usage,
        )

    async def _generate_light_response(
        self,
        user_input: str,
        perception: PerceptionResult,
        memory_context: dict,
    ) -> tuple[CouncilConclusion, TokenUsage]:
        """Generate a light chat response. Returns (conclusion, token_usage)."""
        token_usage = TokenUsage()
        try:
            context = f"用户议题：{user_input}\n\n感知结果：{perception.task_type}"
            if memory_context.get("similar_cases"):
                context += (
                    f"\n\n历史案例：{len(memory_context['similar_cases'])} 个相关案例"
                )

            response, tokens = await self.llm.call_fast(
                system_prompt="你是一个群鸟议会的主持人。请简洁地回应用户的议题，200字以内。",
                user_prompt=context,
                temperature=0.7,
            )
            token_usage.add(tokens)

            return (
                CouncilConclusion(
                    summary=response.strip(),
                    decision="conditional",
                    main_reasons=[],
                    risks=[],
                    next_steps=[],
                    minority_opinion="",
                ),
                token_usage,
            )
        except Exception as e:
            logger.warning(f"Light response failed: {e}")
            return (
                CouncilConclusion(
                    summary="议会收到了你的议题。",
                    decision="conditional",
                    main_reasons=[],
                    risks=[],
                    next_steps=[],
                    minority_opinion="",
                ),
                token_usage,
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

    async def request_reconsideration(
        self,
        session_id: str,
        user_id: str,
        reason: str,
    ) -> dict:
        """Request reconsideration of a council decision."""
        logger.info(f"Reconsideration requested for session {session_id}: {reason}")

        # Get the existing session data
        session = await self.memory.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        # Check if there's a previous conclusion to reconsider
        if not session.conclusion:
            return {"error": "No conclusion to reconsider"}

        # Trigger reconsideration state
        await self.memory.update_session(
            session_id,
            {
                "triggered_reconsider": True,
                "reconsider_reason": reason,
            },
        )

        # Send WebSocket event
        await websocket_manager.send_to_session(
            session_id,
            {
                "type": "reconsideration_started",
                "payload": {
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                },
            },
        )

        return {
            "session_id": session_id,
            "triggered": True,
            "reason": reason,
            "message": "复议已触发，议会正在重新审议",
        }

    async def ask_seat_question(
        self,
        session_id: str,
        user_id: str,
        seat_id: str,
        question: str,
    ) -> dict:
        """Ask a specific seat a question."""
        logger.info(f"Ask seat {seat_id} question: {question[:50]}...")

        # Find the seat config
        seat_config = None
        for seat in self.all_seats:
            if seat.seat_id == seat_id:
                seat_config = seat
                break

        if not seat_config:
            return {"error": f"Seat {seat_id} not found"}

        # Generate response from the seat
        try:
            response = await self.seat_agent.generate_response(
                seat_config, question, context="用户提问"
            )

            # Send WebSocket event
            await websocket_manager.send_to_session(
                session_id,
                {
                    "type": "seat_response",
                    "payload": {
                        "seat_id": seat_id,
                        "seat_name": seat_config.name,
                        "question": question,
                        "response": response,
                        "timestamp": datetime.now().isoformat(),
                    },
                },
            )

            return {
                "seat_id": seat_id,
                "seat_name": seat_config.name,
                "question": question,
                "response": response,
            }
        except Exception as e:
            logger.error(f"Failed to get seat response: {e}")
            return {"error": str(e)}

    async def supplement_testimony(
        self,
        session_id: str,
        user_id: str,
        testimony: str,
    ) -> dict:
        """Supplement testimony during an ongoing council session."""
        logger.info(
            f"Supplement testimony for session {session_id}: {testimony[:50]}..."
        )

        # Get the session
        session = await self.memory.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        # Add testimony to session memory
        await self.memory.update_session(
            session_id,
            {
                "supplement_testimonies": session.supplement_testimonies + [testimony],
            },
        )

        # Send WebSocket event
        await websocket_manager.send_to_session(
            session_id,
            {
                "type": "testimony_supplemented",
                "payload": {
                    "testimony": testimony,
                    "timestamp": datetime.now().isoformat(),
                },
            },
        )

        return {
            "session_id": session_id,
            "supplemented": True,
            "message": "证词已补充到议会记录",
        }
