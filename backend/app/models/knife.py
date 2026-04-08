from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class KnifeResult(BaseModel):
    """Result of knife cut operation."""

    visible_seats: list[str]  # seat_ids of 12 visible seats
    hidden_seats: list[str]  # seat_ids of 11 hidden seats
    cut_risk: float  # 0.0-1.0
    cut_mode: str  # 剧情 | decision | lottery
    cut_timestamp: datetime = Field(default_factory=datetime.now)
    warnings: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Validation result for knife cut."""

    is_valid: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
