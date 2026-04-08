from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class CouncilMode(str, Enum):
    """Council operation mode."""

    LIGHT_CHAT = "light_chat"
    FULL_COUNCIL = "full_council"
    ETERNAL_COUNCIL = "eternal_council"
    SAFETY_MODE = "safety_mode"


class OrchestratorState(str, Enum):
    """Orchestrator state machine states."""

    IDLE = "idle"
    PERCEIVING = "perceiving"
    RISK_DETECTED = "risk_detected"
    SAFETY_MODE = "safety_mode"
    RETRIEVING = "retrieving"
    PLANNING = "planning"
    LIGHT_COUNCIL = "light_council"
    FULL_COUNCIL = "full_council"
    PREVOTING_23 = "prevoting_23"
    KNIFE_CUTTING = "knife_cutting"
    DEBATING_12 = "debating_12"
    VOTING = "voting"
    EVALUATING = "evaluating"
    RECONSIDERING = "reconsidering"
    CONCLUDING = "concluding"
    RENDERING = "rendering"
    OUTPUT = "output"


class VoteMap(BaseModel):
    """Vote tally."""

    approve: int = 0
    oppose: int = 0
    abstain: int = 0


class CouncilState(BaseModel):
    """Current state of the council."""

    mode: CouncilMode = CouncilMode.LIGHT_CHAT
    orchestrator_state: OrchestratorState = OrchestratorState.IDLE
    round: int = 0
    visible_seats: list[str] = Field(default_factory=list)  # seat_ids
    hidden_seats: list[str] = Field(default_factory=list)  # seat_ids
    unanimity_required: bool = False
    vote_map: VoteMap = Field(default_factory=VoteMap)
    tension_level: float = 0.0  # 0.0-1.0
    knife_risk: float = 0.0  # 0.0-1.0
    dominant_axis: str = ""
    pending_reconsideration: bool = False
    updated_at: datetime = Field(default_factory=datetime.now)


class PerceptionResult(BaseModel):
    """Result of user input perception."""

    task_type: (
        str  # decision, emotional_sorting, chat, creative_debate, worldview_interaction
    )
    emotion_profile: dict = Field(default_factory=dict)
    # anxiety, confusion, urgency, etc.
    risk_flags: list[str] = Field(default_factory=list)
    suggested_mode: str = "light_chat"
    suggested_depth: int = 1  # 1-3


class FlowPlan(BaseModel):
    """Planned flow execution."""

    mode: str = "light_chat"
    rounds: int = 1
    need_knife: bool = False
    output_views: list[str] = Field(default_factory=lambda: ["dramatic", "practical"])
    tool_calls: list[dict] = Field(default_factory=list)


class DebateTranscript(BaseModel):
    """Complete debate transcript."""

    rounds: list[dict] = Field(default_factory=list)
    # Each round: {round_num, speeches: [{seat_id, speech, stance}]}
    total_speeches: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class CouncilConclusion(BaseModel):
    """Final conclusion from debate."""

    summary: str = ""
    decision: str = ""  # approve, oppose, conditional, delay
    main_reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    minority_opinion: str = ""
    vote_result: VoteMap = Field(default_factory=VoteMap)


class UICommand(BaseModel):
    """Command for frontend UI."""

    command_type: str  # highlight_seat, animate_bell, show_knife, update_vote, etc.
    payload: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class MemoryWrite(BaseModel):
    """Memory write instruction."""

    memory_type: str  # session, user, seat, archive
    seat_id: Optional[str] = None
    data: dict = Field(default_factory=dict)
    priority: str = "normal"  # low, normal, high


class CouncilResponse(BaseModel):
    """Complete API response for council deliberation."""

    session_id: str
    mode: str
    transcript: Optional[DebateTranscript] = None
    conclusion: CouncilConclusion
    council_state: CouncilState
    ui_commands: list[UICommand] = Field(default_factory=list)
    memory_updates: list[MemoryWrite] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
