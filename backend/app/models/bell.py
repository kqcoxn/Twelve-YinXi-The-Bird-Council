from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class BellEventType(str, Enum):
    """Types of bell events."""

    STANCE_CONFLICT = "stance_conflict"
    STRONG_COLLISION = "strong_collision"
    ISSUE_TRIGGER = "issue_trigger"
    NOT_UNDERSTOOD = "not_understood"
    FORCED_SPEAK = "forced_speak"
    QUESTIONED = "questioned"
    ALLY_SUPPORT = "ally_support"
    USER_AGREEMENT = "user_agreement"
    MODERATOR_PROTECTION = "moderator_protection"
    CONVERSION_ACCEPTED = "conversion_accepted"


class BellState(BaseModel):
    """Current state of a seat's bell."""

    bell_health: int = 80  # 0-100
    stress: int = 20  # 0-100
    fracture_risk: float = 0.1  # 0.0-1.0
    suppression_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)


class BellEvent(BaseModel):
    """Event affecting bell state."""

    type: BellEventType
    source_seat_id: Optional[str] = None
    target_seat_id: str
    intensity: float = 1.0  # 0.0-1.0
    timestamp: datetime = Field(default_factory=datetime.now)


class FractureResult(BaseModel):
    """Result of fracture check."""

    will_fracture: bool
    confidence: float  # 0.0-1.0
    reason: str  # stable, critical_fracture_risk, high_risk_high_stress, accumulated_suppression


class BellDamage(BaseModel):
    """Record of bell damage during a case."""

    seat_id: str
    case_id: str
    damage_amount: int
    fracture_triggered: bool
    timestamp: datetime = Field(default_factory=datetime.now)
