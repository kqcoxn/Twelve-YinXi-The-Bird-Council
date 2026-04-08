from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SessionMemory(BaseModel):
    """In-memory session data (volatile, stored in dict)."""

    session_id: str
    user_id: str
    current_proposal: str = ""
    speaking_seats: list[str] = Field(default_factory=list)
    current_vote_map: dict = Field(default_factory=dict)
    current_evidence: list[str] = Field(default_factory=list)
    conflict_points: list[str] = Field(default_factory=list)
    discussion_round: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserProfile(BaseModel):
    """Long-term user profile (stored in SQLite)."""

    user_id: str
    common_issue_types: list[str] = Field(default_factory=list)
    triggered_emotional_axes: list[str] = Field(default_factory=list)
    preferred_output_style: str = "dramatic"
    resonant_seats: list[str] = Field(default_factory=list)
    major_cases: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SeatMemoryState(BaseModel):
    """Per-seat memory (stored in SQLite)."""

    seat_id: str
    user_id: str
    recent_suppression_count: int = 0
    consecutive_minority_rounds: int = 0
    common_oppose_issues: list[str] = Field(default_factory=list)
    common_allies: list[str] = Field(default_factory=list)
    user_interaction_impression: str = ""
    last_updated: datetime = Field(default_factory=datetime.now)


class CaseSummary(BaseModel):
    """Summary of a case for retrieval."""

    case_id: str
    proposal_title: str
    conclusion: str
    minority_opinion: Optional[str] = None
    created_at: datetime
    similarity: float = 0.0  # For vector search results


class CaseRecord(BaseModel):
    """Complete case record (archived)."""

    case_id: str
    user_id: str
    proposal_title: str
    conclusion: str
    minority_opinion: Optional[str] = None
    bell_damage_records: list[dict] = Field(default_factory=list)
    triggered_reconsider: bool = False
    triggered_fracture: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


class MemoryContext(BaseModel):
    """Aggregated memory context for deliberation."""

    user_profile: Optional[UserProfile] = None
    similar_cases: list[CaseSummary] = Field(default_factory=list)
    seat_memories: dict[str, SeatMemoryState] = Field(default_factory=dict)
    # seat_id -> SeatMemoryState
