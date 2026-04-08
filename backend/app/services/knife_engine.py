"""Knife engine for 23->12+11 seat selection."""

import random
from typing import Optional
from ..models.knife import KnifeResult, ValidationResult
from ..models.seat import SeatConfig, SeatPrevote
from ..models.memory import UserProfile


class KnifeEngine:
    """Executes the layered knife cut to select 12 visible seats from 23."""

    async def execute_cut(
        self,
        all_seats: list[SeatConfig],
        prevotes: list[SeatPrevote],
        cut_mode: str,
        issue_type: str = "decision",
        user_profile: Optional[UserProfile] = None,
        seat_states: dict[str, dict] = None,
    ) -> KnifeResult:
        """Execute 23->12+11 cut based on mode and factors."""

        if cut_mode == "lottery":
            return await self._lottery_cut(all_seats)

        # Decision mode: weighted selection
        visible_ids, hidden_ids, risk = await self._weighted_cut(
            all_seats, prevotes, issue_type, user_profile, seat_states or {}
        )

        warnings = []
        if risk > 0.7:
            warnings.append("切割风险过高，可能导致席位不稳定")

        return KnifeResult(
            visible_seats=visible_ids,
            hidden_seats=hidden_ids,
            cut_risk=risk,
            cut_mode=cut_mode,
            warnings=warnings,
        )

    async def _weighted_cut(
        self,
        all_seats: list[SeatConfig],
        prevotes: list[SeatPrevote],
        issue_type: str,
        user_profile: Optional[UserProfile],
        seat_states: dict[str, dict],
    ) -> tuple[list[str], list[str], float]:
        """Weighted seat selection based on multiple factors."""
        # Default weights from TDD
        weights = {
            "issue_match": 0.3,
            "user_preference": 0.2,
            "bell_stability": 0.2,
            "diversity": 0.2,
            "narrative_priority": 0.1,
        }

        scores = []
        for seat in all_seats:
            seat_id = seat.seat_id

            # Calculate composite score
            issue_score = self._calculate_issue_match(seat, issue_type)
            user_score = (
                self._calculate_user_preference(seat, user_profile)
                if user_profile
                else 0.5
            )
            bell_score = self._calculate_bell_stability(seat_states.get(seat_id, {}))
            diversity_score = 0.5  # Will be adjusted later
            narrative_score = self._calculate_narrative_priority(seat)

            total_score = (
                weights["issue_match"] * issue_score
                + weights["user_preference"] * user_score
                + weights["bell_stability"] * bell_score
                + weights["diversity"] * diversity_score
                + weights["narrative_priority"] * narrative_score
            )

            scores.append((seat_id, total_score))

        # Sort by score and select top 12
        scores.sort(key=lambda x: x[1], reverse=True)
        visible_ids = [s[0] for s in scores[:12]]
        hidden_ids = [s[0] for s in scores[12:]]

        # Calculate cut risk
        visible_states = [seat_states.get(sid, {}) for sid in visible_ids]
        hidden_states = [seat_states.get(sid, {}) for sid in hidden_ids]
        risk = self._calculate_cut_risk(visible_states, hidden_states)

        # If risk too high, adjust selection
        if risk > 0.7:
            visible_ids, hidden_ids, risk = self._adjust_for_risk(
                visible_ids, hidden_ids, scores, seat_states
            )

        return visible_ids, hidden_ids, risk

    def _calculate_issue_match(self, seat: SeatConfig, issue_type: str) -> float:
        """Calculate how well a seat matches the issue type."""
        # Simple heuristic: seats with relevant traits score higher
        traits = seat.traits
        weights = seat.planner_preference.get("priority_weights", {})

        score = 0.5  # Base score

        # Adjust based on issue type
        if issue_type == "decision":
            score = (traits.get("logic", 0.5) + traits.get("risk_aversion", 0.5)) / 2
        elif issue_type == "emotional":
            score = (
                traits.get("empathy", 0.5)
                + (1 - traits.get("emotional_stability", 0.5))
            ) / 2
        elif issue_type == "long_term":
            score = traits.get("long_termism", 0.5)

        return max(0.0, min(1.0, score))

    def _calculate_user_preference(
        self, seat: SeatConfig, user_profile: Optional[UserProfile]
    ) -> float:
        """Calculate user's historical preference for a seat."""
        if not user_profile or not user_profile.resonant_seats:
            return 0.5

        if seat.seat_id in user_profile.resonant_seats:
            return 0.9
        return 0.5

    def _calculate_bell_stability(self, seat_state: dict) -> float:
        """Calculate bell stability score."""
        bell_health = seat_state.get("bell_health", 80)
        stress = seat_state.get("stress", 20)

        # Higher bell health = more stable = more likely to be selected
        stability = (bell_health / 100.0) * 0.6 + ((100 - stress) / 100.0) * 0.4
        return max(0.0, min(1.0, stability))

    def _calculate_narrative_priority(self, seat: SeatConfig) -> float:
        """Calculate narrative importance of a seat."""
        # Front 12 seats have higher narrative priority
        seat_num = int(seat.seat_id.split("_")[1])
        if seat_num <= 12:
            return 0.8
        return 0.4

    def _calculate_cut_risk(
        self, visible_states: list[dict], hidden_states: list[dict]
    ) -> float:
        """Calculate risk of the cut."""
        risk = 0.0

        # Check bell health variance in visible seats
        bell_healths = [s.get("bell_health", 80) for s in visible_states]
        if bell_healths:
            avg_health = sum(bell_healths) / len(bell_healths)
            if avg_health < 50:
                risk += 0.3

        # Check critical bells in visible
        critical_bells = sum(1 for s in visible_states if s.get("bell_health", 80) < 30)
        if critical_bells > 2:
            risk += 0.3

        # Check suppressed minority in hidden
        suppressed = sum(1 for s in hidden_states if s.get("stress", 20) > 70)
        if suppressed > 1:
            risk += 0.2

        return min(risk, 1.0)

    def _adjust_for_risk(
        self,
        visible_ids: list[str],
        hidden_ids: list[str],
        scores: list[tuple[str, float]],
        seat_states: dict[str, dict],
    ) -> tuple[list[str], list[str], float]:
        """Adjust selection to reduce risk."""
        # Swap some high-risk visible seats with more stable hidden seats
        for i in range(len(visible_ids)):
            visible_state = seat_states.get(visible_ids[i], {})
            if visible_state.get("bell_health", 80) < 30:
                # Find a stable hidden seat to swap
                for j in range(len(hidden_ids)):
                    hidden_state = seat_states.get(hidden_ids[j], {})
                    if hidden_state.get("bell_health", 80) > 60:
                        # Swap
                        visible_ids[i], hidden_ids[j] = hidden_ids[j], visible_ids[i]
                        break

        # Recalculate risk
        visible_states = [seat_states.get(sid, {}) for sid in visible_ids]
        hidden_states = [seat_states.get(sid, {}) for sid in hidden_ids]
        risk = self._calculate_cut_risk(visible_states, hidden_states)

        return visible_ids, hidden_ids, risk

    async def _lottery_cut(self, all_seats: list[SeatConfig]) -> KnifeResult:
        """Random lottery selection."""
        seat_ids = [s.seat_id for s in all_seats]
        random.shuffle(seat_ids)

        visible_ids = seat_ids[:12]
        hidden_ids = seat_ids[12:]

        return KnifeResult(
            visible_seats=visible_ids,
            hidden_seats=hidden_ids,
            cut_risk=0.5,  # Medium risk for lottery
            cut_mode="lottery",
            warnings=["抽签模式: 席位随机选择"],
        )

    def validate_cut(self, knife_result: KnifeResult) -> ValidationResult:
        """Validate cut result."""
        issues = []
        suggestions = []

        if len(knife_result.visible_seats) != 12:
            issues.append(
                f"Visible seats count {len(knife_result.visible_seats)} != 12"
            )

        if len(knife_result.hidden_seats) != 11:
            issues.append(f"Hidden seats count {len(knife_result.hidden_seats)} != 11")

        if knife_result.cut_risk > 0.8:
            suggestions.append("切割风险过高,考虑调整选席策略")

        return ValidationResult(
            is_valid=len(issues) == 0, issues=issues, suggestions=suggestions
        )


# Global instance
knife_engine = KnifeEngine()
