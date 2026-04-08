from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class SeatStatus(str, Enum):
    """Seat runtime status."""

    ACTIVE = "active"
    SILENT = "silent"
    FRACTURED = "fractured"
    EXILED = "exiled"
    SHADOW = "shadow"


class SeatStance(str, Enum):
    """Seat voting stance."""

    APPROVE = "approve"
    OPPOSE = "oppose"
    ABSTAIN = "abstain"


class SeatActionType(str, Enum):
    """Type of action a seat can take."""

    SPEAK = "speak"
    QUESTION = "question"
    HOLD = "hold"
    CONVERT = "convert"
    WITHDRAW = "withdraw"


class SeatConfig(BaseModel):
    """Static persona configuration for a seat."""

    seat_id: str
    name: str
    archetype: str
    core_belief: str

    # Traits (0-1 normalized)
    traits: dict = Field(default_factory=dict)
    # logic, empathy, risk_aversion, long_termism, emotional_stability,
    # assertiveness, openness, stress_sensitivity

    # Planner preferences
    planner_preference: dict = Field(default_factory=dict)
    # priority_weights, speak_threshold, question_threshold,
    # convert_sensitivity, risk_aversion, long_term_bias

    # Memory focus
    memory_schema: dict = Field(default_factory=dict)
    # focus_areas, retention_priority, forgetting_rate

    # Tone characteristics
    tone: dict = Field(default_factory=dict)
    # style, pace, vocabulary, rhetorical_devices, emotional_range

    # Trigger conditions
    trigger_conditions: dict = Field(default_factory=dict)
    # high_triggers, calming_factors

    # Alliance tendencies
    alliance_tendency: dict = Field(default_factory=dict)
    # natural_allies, frequent_conflicts, conditional_allies

    # Conflict axes
    conflict_axes: dict = Field(default_factory=dict)
    # primary, secondary, tertiary

    # Bell sensitivity
    bell_sensitivity: dict = Field(default_factory=dict)
    # stress_accumulation, stress_recovery, fracture_threshold, suppression_tolerance

    # Speech pattern
    speech_pattern: dict = Field(default_factory=dict)
    # structure, length, turn_taking, interruption_style

    # Example phrases
    example_phrases: list[str] = Field(default_factory=list)


class SeatState(BaseModel):
    """Runtime state of a seat."""

    seat_id: str
    name: str

    # Current voting state
    current_stance: SeatStance = SeatStance.ABSTAIN
    confidence: float = 0.5

    # Bell state
    bell_health: int = 80  # 0-100
    stress: int = 20  # 0-100
    fracture_risk: float = 0.1  # 0.0-1.0
    suppression_count: int = 0
    minority_streak: int = 0

    # Alliance vector (tracks relationships with other seats)
    alliance_vector: dict = Field(default_factory=dict)

    # Status
    status: SeatStatus = SeatStatus.ACTIVE

    # Config reference (loaded from SeatConfig)
    config: Optional[SeatConfig] = None

    updated_at: datetime = Field(default_factory=datetime.now)


class SeatAction(BaseModel):
    """Structured action output from a seat."""

    seat_id: str
    intent: SeatStance = SeatStance.ABSTAIN
    confidence: float = 0.5
    proposed_action: SeatActionType = SeatActionType.HOLD
    target_seat: Optional[str] = None
    argument_vector: list[str] = Field(default_factory=list)
    ask_for: Optional[str] = None  # delay, protection, reconsider
    stress_delta_hint: int = 0
    speech: str = ""  # Generated speech text


class SeatPrevote(BaseModel):
    """Pre-vote result from 23 seats."""

    seat_id: str
    stance: SeatStance = SeatStance.ABSTAIN
    confidence: float = 0.5
    stress_hint: int = 0
    risk_assessment: str = ""  # Brief risk assessment
