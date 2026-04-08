"""Bell engine for stress and fracture management."""

import random
from ..models.bell import BellEvent, BellEventType, BellState, FractureResult
from ..models.seat import SeatState


# Stress delta values per event type
STRESS_DELTAS = {
    BellEventType.STANCE_CONFLICT: (10, 20),
    BellEventType.STRONG_COLLISION: (15, 25),
    BellEventType.ISSUE_TRIGGER: (10, 30),
    BellEventType.NOT_UNDERSTOOD: (5, 5),
    BellEventType.FORCED_SPEAK: (10, 10),
    BellEventType.QUESTIONED: (15, 15),
    BellEventType.ALLY_SUPPORT: (-10, -10),
    BellEventType.USER_AGREEMENT: (-15, -15),
    BellEventType.MODERATOR_PROTECTION: (-20, -20),
    BellEventType.CONVERSION_ACCEPTED: (-10, -10),
}


class BellEngine:
    """Manages bell state transitions and fracture detection."""

    async def update_bell_state(
        self,
        seat_id: str,
        events: list[BellEvent],
        current_state: SeatState,
        seat_traits: dict,
    ) -> SeatState:
        """Update bell state based on events."""
        if not events:
            return current_state

        # Calculate stress delta
        stress_delta = await self.calculate_stress_delta(events, seat_traits)

        # Apply stress
        current_state.stress = max(0, min(100, current_state.stress + stress_delta))

        # Update bell health (inverse of stress)
        bell_delta = -stress_delta * 0.5  # Bell health changes slower than stress
        current_state.bell_health = max(
            0, min(100, current_state.bell_health + bell_delta)
        )

        # Update fracture risk
        current_state.fracture_risk = await self.calculate_fracture_risk(
            current_state.stress,
            current_state.bell_health,
            current_state.suppression_count,
        )

        # Check for fracture
        fracture_result = await self.check_fracture(current_state)
        if fracture_result.will_fracture:
            current_state = await self.handle_fracture(
                seat_id, fracture_result, current_state
            )

        return current_state

    async def calculate_stress_delta(
        self, events: list[BellEvent], seat_traits: dict
    ) -> int:
        """Calculate total stress change from events."""
        delta = 0
        sensitivity = seat_traits.get("stress_sensitivity", 1.0)

        for event in events:
            if event.type in STRESS_DELTAS:
                min_val, max_val = STRESS_DELTAS[event.type]
                base_delta = random.randint(min_val, max_val)
                delta += int(base_delta * event.intensity * sensitivity)

        return delta

    async def calculate_fracture_risk(
        self, current_stress: int, bell_health: int, suppression_count: int
    ) -> float:
        """Calculate fracture risk (0.0-1.0)."""
        risk = 0.0

        # High stress contribution
        if current_stress > 80:
            risk += 0.4
        elif current_stress > 60:
            risk += 0.2

        # Low bell health contribution
        if bell_health < 30:
            risk += 0.4
        elif bell_health < 50:
            risk += 0.2

        # Suppression count contribution
        if suppression_count > 5:
            risk += 0.3
        elif suppression_count > 3:
            risk += 0.15

        return min(risk, 1.0)

    async def check_fracture(self, seat_state: SeatState) -> FractureResult:
        """Check if seat should fracture."""
        risk = seat_state.fracture_risk
        stress = seat_state.stress
        suppression = seat_state.suppression_count

        if risk > 0.8:
            return FractureResult(
                will_fracture=True, confidence=0.95, reason="critical_fracture_risk"
            )
        elif risk > 0.6 and stress > 80:
            return FractureResult(
                will_fracture=True, confidence=0.75, reason="high_risk_high_stress"
            )
        elif suppression > 5:
            return FractureResult(
                will_fracture=True, confidence=0.6, reason="accumulated_suppression"
            )

        return FractureResult(will_fracture=False, confidence=1.0, reason="stable")

    async def handle_fracture(
        self, seat_id: str, fracture_result: FractureResult, seat_state: SeatState
    ) -> SeatState:
        """Handle fracture event."""
        from ..models.seat import SeatStatus

        seat_state.status = SeatStatus.FRACTURED
        seat_state.bell_health = random.randint(10, 20)
        seat_state.fracture_risk = 0.9
        return seat_state

    async def apply_relief(
        self, seat_state: SeatState, relief_type: str, intensity: float
    ) -> SeatState:
        """Apply stress relief to a seat."""
        relief_map = {
            "ally_support": -10,
            "user_agreement": -15,
            "moderator_protection": -20,
            "conversion_accepted": -10,
        }

        base_relief = relief_map.get(relief_type, -5)
        relief = int(base_relief * intensity)

        seat_state.stress = max(0, seat_state.stress + relief)
        seat_state.bell_health = min(100, seat_state.bell_health - relief * 0.5)
        seat_state.fracture_risk = max(
            0.0, seat_state.fracture_risk - abs(relief) * 0.01
        )

        return seat_state


# Global instance
bell_engine = BellEngine()
