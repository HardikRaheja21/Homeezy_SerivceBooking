from datetime import datetime, timezone
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from typing import Dict

router = APIRouter()

# Simple in-memory chat store (use Redis in production)
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    active_connections[user_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Forward message to recipient
            recipient_id = data.get("to")
            message = data.get("message")
            
            if recipient_id in active_connections:
                await active_connections[recipient_id].send_json({
                    "from": user_id,
                    "message": message,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    except WebSocketDisconnect:
        del active_connections[user_id]
