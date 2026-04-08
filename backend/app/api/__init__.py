"""API routes."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid
import logging
import asyncio

from ..models.api import (
    SubmitProposalRequest,
    SeatStateResponse,
    SessionStateResponse,
    UserProfileResponse,
    ReconsiderRequest,
    AskSeatRequest,
    SupplementTestimonyRequest,
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
from ..services.websocket_manager import websocket_manager
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


@router.get("/council/history")
async def get_council_history(
    user_id: str = "default_user", limit: int = 20, offset: int = 0
):
    """Get council session history for a user."""
    import aiosqlite
    from ..core.config import settings

    async with aiosqlite.connect(str(settings.DB_PATH)) as db:
        cursor = await db.execute(
            """SELECT case_id, proposal_title, conclusion, minority_opinion, 
                      triggered_reconsider, triggered_fracture, created_at
               FROM cases 
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ? OFFSET ?""",
            (user_id, limit, offset),
        )
        rows = await cursor.fetchall()

    # Get total count
    cursor = await db.execute(
        "SELECT COUNT(*) FROM cases WHERE user_id = ?", (user_id,)
    )
    total_count = await cursor.fetchone()

    return {
        "sessions": [
            {
                "case_id": row[0],
                "proposal_title": row[1],
                "conclusion": row[2],
                "minority_opinion": row[3],
                "triggered_reconsider": row[4],
                "triggered_fracture": row[5],
                "created_at": row[6],
            }
            for row in rows
        ],
        "pagination": {
            "total": total_count[0],
            "limit": limit,
            "offset": offset,
            "has_more": total_count[0] > offset + limit,
        },
    }


@router.get("/ws/sessions")
async def list_active_sessions():
    """List active WebSocket sessions."""
    return {
        "active_sessions": websocket_manager.get_active_sessions(),
        "total": len(websocket_manager.get_active_sessions()),
    }


@router.websocket("/ws/council/{session_id}")
async def council_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time council events."""
    await websocket_manager.connect(websocket, session_id)

    try:
        # Send connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "payload": {
                    "session_id": session_id,
                    "message": "已连接到议会实时推送",
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )

        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for messages from client (with timeout)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Handle client messages (e.g., ping/pong, commands)
                import json

                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_json(
                            {
                                "type": "pong",
                                "payload": {"timestamp": datetime.now().isoformat()},
                            }
                        )
                except json.JSONDecodeError:
                    pass  # Ignore invalid messages

            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_json(
                    {
                        "type": "ping",
                        "payload": {"timestamp": datetime.now().isoformat()},
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        websocket_manager.disconnect(websocket)


@router.post("/council/reconsider")
async def request_reconsider(request: ReconsiderRequest):
    """Request reconsideration of a council decision."""
    try:
        orchestrator = get_orchestrator()
        result = await orchestrator.request_reconsideration(
            session_id=request.session_id,
            user_id=request.user_id,
            reason=request.reason,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to process reconsideration: {e}", exc_info=True)
        return {"error": str(e)}


@router.post("/council/ask-seat")
async def ask_seat(request: AskSeatRequest):
    """Ask a specific seat a question."""
    try:
        orchestrator = get_orchestrator()
        result = await orchestrator.ask_seat_question(
            session_id=request.session_id,
            user_id=request.user_id,
            seat_id=request.seat_id,
            question=request.question,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to process seat question: {e}", exc_info=True)
        return {"error": str(e)}


@router.post("/council/supplement")
async def supplement_testimony(request: SupplementTestimonyRequest):
    """Supplement testimony during an ongoing council session."""
    try:
        orchestrator = get_orchestrator()
        result = await orchestrator.supplement_testimony(
            session_id=request.session_id,
            user_id=request.user_id,
            testimony=request.testimony,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to process supplement testimony: {e}", exc_info=True)
        return {"error": str(e)}


@router.get("/council/relationship-graph")
async def get_relationship_graph():
    """Get relationship graph between seats."""
    try:
        from ..services.relationship_engine import RelationshipEngine
        from ..services.memory_service import memory_service
        from ..models.personas import load_all_seats

        engine = RelationshipEngine(memory_service)
        all_seats = load_all_seats()
        graph = await engine.calculate_graph(all_seats)

        return graph.to_dict()
    except Exception as e:
        logger.error(f"Failed to get relationship graph: {e}", exc_info=True)
        return {"error": str(e)}
