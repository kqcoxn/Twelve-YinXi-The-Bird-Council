"""API routes."""

from fastapi import APIRouter
from datetime import datetime
import uuid
import logging

from ..models.api import (
    SubmitProposalRequest,
    SeatStateResponse,
    SessionStateResponse,
    UserProfileResponse,
)
from ..models.council import (
    CouncilResponse,
    CouncilConclusion,
    CouncilState,
    CouncilMode,
)
from ..models.seat import SeatState, SeatStance
from ..models.personas import load_all_seats, get_seat_config
from ..services.memory_service import memory_service
from ..services.knife_engine import KnifeEngine
from ..services.bell_engine import BellEngine
from ..core.config import settings
from ..core.llm import LLMClient

logger = logging.getLogger(__name__)

router = APIRouter()

# Lazy-initialized components
_orchestrator = None
_llm_client = None


def get_orchestrator():
    """Get or create orchestrator instance (lazy initialization)."""
    global _orchestrator, _llm_client

    if _orchestrator is None:
        _llm_client = LLMClient()
        knife_engine = KnifeEngine()
        bell_engine = BellEngine()

        from ..agents.orchestrator import CouncilOrchestrator

        _orchestrator = CouncilOrchestrator(
            llm_client=_llm_client,
            memory_service=memory_service,
            knife_engine=knife_engine,
            bell_engine=bell_engine,
        )
        logger.info("CouncilOrchestrator initialized")

    return _orchestrator


@router.post("/council/submit")
async def submit_proposal(request: SubmitProposalRequest):
    """Submit a new proposal to the council."""
    # Create session
    session = await memory_service.create_session(request.session_id, request.user_id)
    session.current_proposal = request.user_input

    try:
        # Get orchestrator and process
        orchestrator = get_orchestrator()
        response = await orchestrator.process_input(
            user_id=request.user_id,
            session_id=request.session_id,
            user_input=request.user_input,
        )

        # Update session with result
        await memory_service.update_session(
            request.session_id,
            {
                "current_proposal": request.user_input,
                "conclusion": response.conclusion.summary,
            },
        )

        return response

    except Exception as e:
        logger.error(f"Failed to process proposal: {e}", exc_info=True)

        # Fallback response
        all_seats = load_all_seats()
        return CouncilResponse(
            session_id=request.session_id,
            mode="light_chat",
            conclusion=CouncilConclusion(
                summary=f"很抱歉，处理提案时遇到了错误：{str(e)}",
                decision="delay",
                main_reasons=["系统错误"],
                risks=[str(e)],
                next_steps=["请稍后重试"],
            ),
            council_state=CouncilState(
                mode=CouncilMode.LIGHT_CHAT,
                visible_seats=[s.seat_id for s in all_seats[:12]],
                hidden_seats=[s.seat_id for s in all_seats[12:]],
            ),
        )


@router.get("/council/session/{session_id}")
async def get_session(session_id: str):
    """Get current session state."""
    session = await memory_service.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    return SessionStateResponse(
        session_id=session_id,
        mode="light_chat",
        council_state={},
        current_proposal=session.current_proposal,
    )


@router.get("/seats")
async def list_seats():
    """List all 23 seats with basic info."""
    all_seats = load_all_seats()
    return [
        {
            "seat_id": s.seat_id,
            "name": s.name,
            "archetype": s.archetype,
            "core_belief": s.core_belief,
        }
        for s in all_seats
    ]


@router.get("/seats/{seat_id}/state")
async def get_seat_state(seat_id: str):
    """Get state of a specific seat."""
    config = get_seat_config(seat_id)
    if not config:
        return {"error": "Seat not found"}

    return SeatStateResponse(
        seat_id=config.seat_id,
        name=config.name,
        status="active",
        current_stance="abstain",
        confidence=0.5,
        bell_health=80,
        stress=20,
        fracture_risk=0.1,
    )


@router.get("/user/profile")
async def get_user_profile(user_id: str = "default_user"):
    """Get user profile."""
    profile = await memory_service.get_user_profile(user_id)
    if not profile:
        profile = await memory_service.create_user_profile(user_id)

    return UserProfileResponse(
        user_id=profile.user_id,
        preferred_output_style=profile.preferred_output_style,
        resonant_seats=profile.resonant_seats,
        common_issue_types=profile.common_issue_types,
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    llm_configured = bool(settings.FAST_MODEL_API_KEY and settings.FAST_MODEL_ENDPOINT)
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "llm_configured": llm_configured,
    }
