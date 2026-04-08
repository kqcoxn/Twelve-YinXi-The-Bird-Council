"""Relationship Engine - Calculate and track relationships between seats based on deliberation history."""

import logging
from typing import Optional
from datetime import datetime

from ..models.seat import SeatConfig
from .memory_service import MemoryService

logger = logging.getLogger(__name__)


class RelationshipEdge:
    """Represents a relationship between two seats."""

    def __init__(
        self,
        from_seat_id: str,
        to_seat_id: str,
        agreement_score: float = 0.0,
        interaction_count: int = 0,
        last_interaction: Optional[datetime] = None,
        influence_strength: float = 0.0,
    ):
        self.from_seat_id = from_seat_id
        self.to_seat_id = to_seat_id
        self.agreement_score = agreement_score  # -1 to +1
        self.interaction_count = interaction_count
        self.last_interaction = last_interaction or datetime.now()
        self.influence_strength = influence_strength

    def to_dict(self) -> dict:
        return {
            "from_seat_id": self.from_seat_id,
            "to_seat_id": self.to_seat_id,
            "agreement_score": round(self.agreement_score, 3),
            "interaction_count": self.interaction_count,
            "last_interaction": (
                self.last_interaction.isoformat() if self.last_interaction else None
            ),
            "influence_strength": round(self.influence_strength, 3),
        }


class RelationshipGraph:
    """Complete relationship graph between all seats."""

    def __init__(self):
        self.edges: list[RelationshipEdge] = []
        self.clustering_coefficient: float = 0.0
        self.density: float = 0.0
        self.updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "edges": [edge.to_dict() for edge in self.edges],
            "clustering_coefficient": round(self.clustering_coefficient, 3),
            "density": round(self.density, 3),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RelationshipEngine:
    """Calculate and track relationships between seats based on deliberation history."""

    def __init__(self, memory_service: MemoryService):
        self.memory = memory_service
        self._graph_cache: Optional[RelationshipGraph] = None

    async def calculate_graph(
        self,
        all_seats: list[SeatConfig],
        session_ids: Optional[list[str]] = None,
    ) -> RelationshipGraph:
        """Calculate relationship graph based on deliberation history."""
        graph = RelationshipGraph()
        graph.updated_at = datetime.now()

        # Get historical cases for analysis
        cases = []
        if session_ids:
            for session_id in session_ids:
                session = await self.memory.get_session(session_id)
                if session:
                    cases.append(session)
        else:
            # Use recent sessions from database
            cases = await self._get_recent_cases(limit=50)

        if not cases:
            # No history, return empty graph with predefined alliances
            graph.edges = self._generate_predefined_relationships(all_seats)
            self._calculate_metrics(graph, len(all_seats))
            self._graph_cache = graph
            return graph

        # Calculate relationships based on voting patterns
        graph.edges = self._calculate_from_cases(all_seats, cases)
        self._calculate_metrics(graph, len(all_seats))

        self._graph_cache = graph
        return graph

    def _calculate_from_cases(
        self,
        seats: list[SeatConfig],
        cases: list,
    ) -> list[RelationshipEdge]:
        """Calculate relationships based on historical cases."""
        edges = []

        # Simple implementation: use seat alliances from config
        # In production, this would analyze actual voting patterns
        base_edges = self._generate_predefined_relationships(seats)

        # Adjust based on case outcomes
        for case in cases:
            if hasattr(case, "triggered_reconsider") and case.triggered_reconsider:
                # Cases with reconsideration indicate tension
                self._adjust_edges_for_tension(base_edges, factor=-0.05)

        edges = base_edges
        return edges

    def _generate_predefined_relationships(
        self, seats: list[SeatConfig]
    ) -> list[RelationshipEdge]:
        """Generate initial relationships based on seat configurations."""
        edges = []

        # Alliance groups (simplified - in production this would come from config)
        alliances = {
            "rational": ["seat_01", "seat_05", "seat_09"],
            "emotional": ["seat_02", "seat_06", "seat_10"],
            "pragmatic": ["seat_03", "seat_07", "seat_11"],
            "idealistic": ["seat_04", "seat_08", "seat_12"],
        }

        # Create edges within alliances (positive relationships)
        for alliance_name, seat_ids in alliances.items():
            for i, from_id in enumerate(seat_ids):
                for to_id in seat_ids[i + 1 :]:
                    if from_id in [s.seat_id for s in seats] and to_id in [
                        s.seat_id for s in seats
                    ]:
                        edges.append(
                            RelationshipEdge(
                                from_seat_id=from_id,
                                to_seat_id=to_id,
                                agreement_score=0.6,  # High agreement within alliance
                                interaction_count=5,
                                influence_strength=0.5,
                            )
                        )

        # Create some cross-alliance edges (mixed relationships)
        cross_edges = [
            ("seat_01", "seat_02", -0.2),  # Rational vs Emotional - slight tension
            ("seat_03", "seat_04", -0.1),  # Pragmatic vs Idealistic - slight tension
            ("seat_05", "seat_06", 0.3),  # Some cross-alliance agreement
        ]

        for from_id, to_id, score in cross_edges:
            if from_id in [s.seat_id for s in seats] and to_id in [
                s.seat_id for s in seats
            ]:
                edges.append(
                    RelationshipEdge(
                        from_seat_id=from_id,
                        to_seat_id=to_id,
                        agreement_score=score,
                        interaction_count=3,
                        influence_strength=0.2,
                    )
                )

        return edges

    def _adjust_edges_for_tension(self, edges: list[RelationshipEdge], factor: float):
        """Adjust edge scores based on tension events."""
        for edge in edges:
            edge.agreement_score += factor
            edge.agreement_score = max(-1.0, min(1.0, edge.agreement_score))

    def _calculate_metrics(self, graph: RelationshipGraph, seat_count: int):
        """Calculate graph metrics."""
        if seat_count < 2:
            return

        # Density: actual edges / possible edges
        possible_edges = seat_count * (seat_count - 1) / 2
        actual_edges = len(graph.edges)
        graph.density = actual_edges / possible_edges if possible_edges > 0 else 0

        # Clustering coefficient (simplified)
        # In production, this would use proper graph algorithms
        graph.clustering_coefficient = min(0.5, graph.density * 1.5)

    async def _get_recent_cases(self, limit: int = 50) -> list:
        """Get recent cases from database."""
        import aiosqlite
        from ..core.config import settings

        try:
            async with aiosqlite.connect(str(settings.DB_PATH)) as db:
                cursor = await db.execute(
                    """SELECT case_id, user_id, proposal_title, conclusion, 
                              triggered_reconsider, triggered_fracture, created_at
                       FROM cases 
                       ORDER BY created_at DESC
                       LIMIT ?""",
                    (limit,),
                )
                rows = await cursor.fetchall()

            return [
                {
                    "case_id": row[0],
                    "user_id": row[1],
                    "proposal_title": row[2],
                    "conclusion": row[3],
                    "triggered_reconsider": row[4],
                    "triggered_fracture": row[5],
                    "created_at": row[6],
                }
                for row in rows
            ]
        except Exception as e:
            logger.warning(f"Failed to get recent cases: {e}")
            return []
