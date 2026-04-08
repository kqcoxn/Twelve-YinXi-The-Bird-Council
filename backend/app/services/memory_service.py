"""Memory service for layered memory management."""

import aiosqlite
from typing import Optional
from datetime import datetime
from cachetools import TTLCache
from ..core.config import settings
from ..core.database import get_db
from ..models.memory import (
    SessionMemory,
    UserProfile,
    SeatMemoryState,
    CaseSummary,
    CaseRecord,
    MemoryContext,
)
from .vector_search import vector_search, HAS_VECTOR_SEARCH


class MemoryService:
    """Layered memory management service."""

    def __init__(self):
        # Session memory: in-memory cache with TTL
        self._session_cache: dict[str, SessionMemory] = {}
        self._session_cache_ttl = TTLCache(maxsize=100, ttl=settings.SESSION_TTL)
        self._vector_search_enabled = HAS_VECTOR_SEARCH

    # Session Memory (volatile)
    async def create_session(self, session_id: str, user_id: str) -> SessionMemory:
        """Create a new session memory."""
        session = SessionMemory(session_id=session_id, user_id=user_id)
        self._session_cache[session_id] = session
        return session

    async def get_session(self, session_id: str) -> Optional[SessionMemory]:
        """Get session memory."""
        return self._session_cache.get(session_id)

    async def update_session(self, session_id: str, updates: dict) -> None:
        """Update session memory."""
        if session_id in self._session_cache:
            session = self._session_cache[session_id]
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.updated_at = datetime.now()

    # User Profile (SQLite)
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile from SQLite."""
        async with aiosqlite.connect(str(settings.DB_PATH)) as db:
            cursor = await db.execute(
                "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            if row:
                return UserProfile(
                    user_id=row[1],
                    preferred_output_style=row[4],
                    resonant_seats=[],
                    common_issue_types=[],
                )
        return None

    async def create_user_profile(self, user_id: str) -> UserProfile:
        """Create or get user profile."""
        existing = await self.get_user_profile(user_id)
        if existing:
            return existing

        profile = UserProfile(user_id=user_id)
        async with aiosqlite.connect(str(settings.DB_PATH)) as db:
            await db.execute(
                "INSERT OR IGNORE INTO user_profiles (user_id) VALUES (?)", (user_id,)
            )
            await db.commit()
        return profile

    # Seat Memory (SQLite)
    async def get_seat_memory(
        self, user_id: str, seat_id: str
    ) -> Optional[SeatMemoryState]:
        """Get seat memory from SQLite."""
        async with aiosqlite.connect(str(settings.DB_PATH)) as db:
            cursor = await db.execute(
                "SELECT * FROM seat_memories WHERE user_id = ? AND seat_id = ?",
                (user_id, seat_id),
            )
            row = await cursor.fetchone()
            if row:
                return SeatMemoryState(
                    seat_id=row[2],
                    user_id=row[1],
                    recent_suppression_count=row[3],
                    consecutive_minority_rounds=row[4],
                )
        return None

    async def update_seat_memory(
        self, user_id: str, seat_id: str, updates: dict
    ) -> None:
        """Update seat memory in SQLite."""
        async with aiosqlite.connect(str(settings.DB_PATH)) as db:
            await db.execute(
                """INSERT OR REPLACE INTO seat_memories
                   (user_id, seat_id, recent_suppression_count, consecutive_minority_rounds, last_updated)
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (
                    user_id,
                    seat_id,
                    updates.get("suppression_count", 0),
                    updates.get("minority_rounds", 0),
                ),
            )
            await db.commit()

    # Council Archive (SQLite)
    async def archive_case(self, case_record: CaseRecord) -> str:
        """Archive a case to SQLite."""
        async with aiosqlite.connect(str(settings.DB_PATH)) as db:
            await db.execute(
                """INSERT OR REPLACE INTO cases
                   (case_id, user_id, proposal_title, conclusion, minority_opinion,
                    triggered_reconsider, triggered_fracture)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    case_record.case_id,
                    case_record.user_id,
                    case_record.proposal_title,
                    case_record.conclusion,
                    case_record.minority_opinion,
                    case_record.triggered_reconsider,
                    case_record.triggered_fracture,
                ),
            )
            await db.commit()
        return case_record.case_id

    async def search_similar_cases(
        self, user_id: str, query: str, top_k: int = 5
    ) -> list[CaseSummary]:
        """Search for similar cases using vector search with text fallback."""
        # Use vector search if available and enabled
        if self._vector_search_enabled and vector_search.model is not None:
            try:
                vector_results = await vector_search.search_similar_cases(
                    user_id, query, top_k
                )
                return [
                    CaseSummary(
                        case_id=r["case_id"],
                        proposal_title=r["proposal_title"],
                        conclusion=r.get("conclusion", ""),
                        minority_opinion=None,
                        created_at=datetime.now(),
                    )
                    for r in vector_results
                ]
            except Exception as e:
                print(f"[WARN] Vector search failed: {e}, falling back to text search")

        # Fallback to text-based search
        keywords = query.split()

        async with aiosqlite.connect(str(settings.DB_PATH)) as db:
            conditions = []
            params = [user_id]

            for keyword in keywords:
                conditions.append("(proposal_title LIKE ? OR conclusion LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            cursor = await db.execute(
                f"""SELECT case_id, proposal_title, conclusion, minority_opinion, created_at
                    FROM cases WHERE user_id = ? AND ({where_clause})
                    ORDER BY created_at DESC LIMIT ?""",
                params + [top_k],
            )
            rows = await cursor.fetchall()

        return [
            CaseSummary(
                case_id=row[0],
                proposal_title=row[1],
                conclusion=row[2] or "",
                minority_opinion=row[3],
                created_at=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
            )
            for row in rows
        ]

    # Memory context building
    async def build_context(
        self, user_id: str, user_input: str, top_k: int = 3
    ) -> dict:
        """Build memory context for deliberation."""
        user_profile = await self.get_user_profile(user_id)
        similar_cases = await self.search_similar_cases(user_id, user_input, top_k)

        return {
            "user_profile": user_profile,
            "similar_cases": similar_cases,
            "seat_memories": {},
        }

    # Memory write strategy
    async def should_write_memory(self, event_type: str, intensity: float) -> bool:
        """Decide whether to write to long-term memory."""
        # Only write significant events
        if event_type in ["final_conclusion", "fracture", "high_emotion"]:
            return intensity > 0.5
        if event_type in ["user_preference", "repeated_pattern"]:
            return intensity > 0.3
        return False


# Global instance
memory_service = MemoryService()
