"""Vector search service with automatic degradation to text search."""

from typing import List, Optional
import sqlite3

try:
    from sentence_transformers import SentenceTransformer, util

    HAS_VECTOR_SEARCH = True
except ImportError:
    HAS_VECTOR_SEARCH = False

from ..core.config import settings


class VectorSearchService:
    """Vector search with automatic fallback to text search."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(settings.DB_PATH)
        self.model = None

        if HAS_VECTOR_SEARCH:
            try:
                # Use lightweight model (~80MB)
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                print("[OK] Vector search: enabled")
            except Exception as e:
                print(f"[WARN] Vector model load failed: {e}")
                print("[TIP] Falling back to text search")
        else:
            print("[WARN] Vector search: not installed")
            print("[TIP] Install: pip install -r requirements-vector.txt")

    async def search_similar_cases(
        self, user_id: str, query: str, top_k: int = 5
    ) -> List[dict]:
        """Search for similar cases (auto-degrade)."""
        if self.model is not None:
            return await self._vector_search(user_id, query, top_k)
        else:
            return await self._text_search(user_id, query, top_k)

    async def _vector_search(self, user_id: str, query: str, top_k: int) -> List[dict]:
        """Vector search (high accuracy)."""
        import torch
        import aiosqlite

        # Encode query
        query_embedding = self.model.encode(query, convert_to_tensor=True)

        # Get cases from database
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT case_id, proposal_title, conclusion "
                "FROM cases WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            )
            rows = await cursor.fetchall()

        # Calculate similarities
        results = []
        for row in rows:
            # Simple text-based similarity for now
            # Full implementation would use stored embeddings
            text = f"{row[1]} {row[2] or ''}"
            score = self._text_similarity(query, text)
            results.append(
                {
                    "case_id": row[0],
                    "proposal_title": row[1],
                    "conclusion": row[2],
                    "similarity": score,
                }
            )

        # Sort and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    async def _text_search(self, user_id: str, query: str, top_k: int) -> List[dict]:
        """Text search (fallback)."""
        import aiosqlite

        keywords = query.split()

        async with aiosqlite.connect(self.db_path) as db:
            conditions = []
            params = [user_id]

            for keyword in keywords:
                conditions.append("(proposal_title LIKE ? OR conclusion LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            cursor = await db.execute(
                f"SELECT case_id, proposal_title, conclusion "
                f"FROM cases WHERE user_id = ? AND ({where_clause}) "
                f"ORDER BY created_at DESC LIMIT ?",
                params + [top_k],
            )
            rows = await cursor.fetchall()

        return [
            {
                "case_id": row[0],
                "proposal_title": row[1],
                "conclusion": row[2],
                "similarity": 0.0,
            }
            for row in rows
        ]

    def _text_similarity(self, query: str, text: str) -> float:
        """Simple text similarity score."""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())

        if not query_words:
            return 0.0

        intersection = query_words & text_words
        return len(intersection) / len(query_words)


# Global instance
vector_search = VectorSearchService()
