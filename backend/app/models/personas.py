"""23 seat personas loader."""

import json
from pathlib import Path
from typing import Optional
from ..models.seat import SeatConfig

_personas_cache: dict[str, SeatConfig] = {}


def load_all_seats() -> list[SeatConfig]:
    """Load all 23 seat configurations."""
    if _personas_cache:
        return list(_personas_cache.values())

    personas_path = Path(__file__).parent.parent / "data" / "personas.json"

    with open(personas_path, "r", encoding="utf-8") as f:
        personas_data = json.load(f)

    seats = []
    for data in personas_data:
        seat = SeatConfig(**data)
        _personas_cache[seat.seat_id] = seat
        seats.append(seat)

    return seats


def get_seat_config(seat_id: str) -> Optional[SeatConfig]:
    """Get configuration for a specific seat."""
    if not _personas_cache:
        load_all_seats()
    return _personas_cache.get(seat_id)


def get_all_seat_ids() -> list[str]:
    """Get all 23 seat IDs."""
    if not _personas_cache:
        load_all_seats()
    return list(_personas_cache.keys())
