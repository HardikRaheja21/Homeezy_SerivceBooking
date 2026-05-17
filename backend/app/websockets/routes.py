from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import logging
from app.websockets.manager import manager
from app.websockets.auth import get_current_user_ws

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_info: dict = Depends(get_current_user_ws)):
    user_id = user_info["user_id"]
    role = user_info["role"]
    
    await manager.connect(websocket, user_id, role)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle client-sent actions (like joining a booking room)
            action = data.get("action")
            if action == "join_booking":
                booking_id = data.get("booking_id")
                if booking_id:
                    manager.join_booking_room(user_id, booking_id)
                    await manager.send_personal_message(
                        {"type": "system", "message": f"Joined updates for booking {booking_id}"}, 
                        user_id
                    )
            elif action == "leave_booking":
                booking_id = data.get("booking_id")
                if booking_id:
                    manager.leave_booking_room(user_id, booking_id)
            elif action == "ping":
                await manager.send_personal_message({"type": "pong"}, user_id)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, role)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id, role)
