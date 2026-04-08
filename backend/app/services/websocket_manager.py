"""WebSocket manager for real-time event streaming."""

import asyncio
import logging
from typing import Any
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time council events."""

    def __init__(self):
        # session_id -> list of WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}
        # Track active connections for cleanup
        self._connection_metadata: dict[WebSocket, dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if session_id not in self._connections:
            self._connections[session_id] = []

        self._connections[session_id].append(websocket)
        self._connection_metadata[websocket] = {
            "session_id": session_id,
            "connected_at": datetime.now().isoformat(),
        }

        logger.info(f"WebSocket connected for session {session_id}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self._connection_metadata:
            session_id = self._connection_metadata[websocket]["session_id"]
            if session_id in self._connections:
                try:
                    self._connections[session_id].remove(websocket)
                    if not self._connections[session_id]:
                        del self._connections[session_id]
                except ValueError:
                    pass
            del self._connection_metadata[websocket]
            logger.info(f"WebSocket disconnected for session {session_id}")

    async def send_to_session(self, session_id: str, data: dict[str, Any]):
        """Send event to all clients subscribed to a session."""
        if session_id not in self._connections:
            return

        disconnected = []
        for websocket in self._connections[session_id]:
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast(self, data: dict[str, Any]):
        """Broadcast event to all connected clients."""
        for session_id in list(self._connections.keys()):
            await self.send_to_session(session_id, data)

    def get_active_sessions(self) -> list[str]:
        """Get list of session IDs with active connections."""
        return list(self._connections.keys())

    def get_connection_count(self, session_id: str) -> int:
        """Get number of active connections for a session."""
        if session_id not in self._connections:
            return 0
        return len(self._connections[session_id])


# Global instance
websocket_manager = WebSocketManager()
