"""
WebSocket Manager
Handles real-time communication with clients
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
from datetime import datetime
import json
import structlog

from app.database import prisma

logger = structlog.get_logger()

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        # session_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        logger.info("WebSocket connected", session_id=session_id)

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info("WebSocket disconnected", session_id=session_id)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        await websocket.send_json(message)

    async def broadcast_to_session(self, message: dict, session_id: str):
        """Broadcast message to all connections of a session"""
        if session_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error("Failed to send message", error=str(e))
                    disconnected.add(connection)

            # Clean up disconnected connections
            for connection in disconnected:
                self.active_connections[session_id].discard(connection)


manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    # Verify session exists
    session = await prisma.learningsession.find_unique(where={"id": session_id})
    if not session:
        await websocket.close(code=1008, reason="Session not found")
        return

    await manager.connect(websocket, session_id)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Echo back for now (add actual message handling later)
            await manager.send_personal_message({
                "type": "ACKNOWLEDGMENT",
                "message": "Message received",
                "original": message
            }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        logger.info("Client disconnected", session_id=session_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), session_id=session_id)
        manager.disconnect(websocket, session_id)


async def send_event_to_session(session_id: str, event_type: str, payload: dict):
    """Helper function to send events to a session"""
    message = {
        "type": event_type,
        "payload": payload,
        "timestamp": str(datetime.utcnow())
    }
    await manager.broadcast_to_session(message, session_id)


# Export manager for use in other modules
__all__ = ["router", "manager", "send_event_to_session"]
