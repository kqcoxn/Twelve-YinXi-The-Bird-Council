from pydantic import BaseModel, Field
from typing import Optional


# Request models


class SubmitProposalRequest(BaseModel):
    """Submit a new proposal."""

    user_id: str
    session_id: str
    user_input: str
    action_type: str = "submit_proposal"
    # submit_proposal | supplement_testimony | ask_seat | request_reconsider | ask_summary


class SupplementTestimonyRequest(BaseModel):
    """Supplement testimony during debate."""

    user_id: str
    session_id: str
    testimony: str


class AskSeatRequest(BaseModel):
    """Ask a specific seat a question."""

    user_id: str
    session_id: str
    seat_id: str
    question: str


class ReconsiderRequest(BaseModel):
    """Request reconsideration."""

    user_id: str
    session_id: str
    reason: str


class SummaryRequest(BaseModel):
    """Request moderator summary."""

    user_id: str
    session_id: str


# Response models


class SeatStateResponse(BaseModel):
    """API response for seat state."""

    seat_id: str
    name: str
    status: str
    current_stance: str
    confidence: float
    bell_health: int
    stress: int
    fracture_risk: float


class SessionStateResponse(BaseModel):
    """API response for session state."""

    session_id: str
    mode: str
    council_state: dict
    current_proposal: str = ""
    transcript: Optional[dict] = None


class UserProfileResponse(BaseModel):
    """API response for user profile."""

    user_id: str
    preferred_output_style: str = "dramatic"
    resonant_seats: list[str] = Field(default_factory=list)
    common_issue_types: list[str] = Field(default_factory=list)


class UserProfileUpdateRequest(BaseModel):
    """Request to update user profile."""

    preferred_output_style: Optional[str] = None
    resonant_seats: Optional[list[str]] = None


# WebSocket message types


class WebSocketMessage(BaseModel):
    """Base WebSocket message."""

    type: str
    payload: dict = Field(default_factory=dict)


class SeatSpeakingMessage(WebSocketMessage):
    """Seat speaking event."""

    type: str = "seat_speaking"
    seat_id: str = ""
    speech: str = ""


class BellUpdateMessage(WebSocketMessage):
    """Bell state update event."""

    type: str = "bell_update"
    seat_id: str = ""
    bell_health: int = 0
    fracture_risk: float = 0.0


class VoteUpdateMessage(WebSocketMessage):
    """Vote map update event."""

    type: str = "vote_update"
    vote_map: dict = Field(default_factory=dict)


class KnifeCutMessage(WebSocketMessage):
    """Knife cut animation event."""

    type: str = "knife_cut"
    visible_seats: list[str] = Field(default_factory=list)
    hidden_seats: list[str] = Field(default_factory=list)
    cut_risk: float = 0.0


class ConclusionMessage(WebSocketMessage):
    """Conclusion event."""

    type: str = "conclusion"
    conclusion: dict = Field(default_factory=dict)
    views: dict = Field(default_factory=dict)
