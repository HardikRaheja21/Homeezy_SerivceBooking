import json
from typing import Dict, Set, List
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # user_id -> set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # role -> set of active user_ids
        self.role_rooms: Dict[str, Set[str]] = {
            "customer": set(),
            "worker": set(),
            "admin": set()
        }
        # booking_id -> set of active user_ids (involved in booking)
        self.booking_rooms: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, role: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        if role in self.role_rooms:
            self.role_rooms[role].add(user_id)
            
        logger.info(f"WebSocket connected: user_id={user_id}, role={role}")

    def disconnect(self, websocket: WebSocket, user_id: str, role: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if role in self.role_rooms:
                    self.role_rooms[role].discard(user_id)
                # Remove from booking rooms
                for booking_id in list(self.booking_rooms.keys()):
                    self.leave_booking_room(user_id, booking_id)
                    
        logger.info(f"WebSocket disconnected: user_id={user_id}")

    def join_booking_room(self, user_id: str, booking_id: str):
        if booking_id not in self.booking_rooms:
            self.booking_rooms[booking_id] = set()
        self.booking_rooms[booking_id].add(user_id)

    def leave_booking_room(self, user_id: str, booking_id: str):
        if booking_id in self.booking_rooms:
            self.booking_rooms[booking_id].discard(user_id)
            if not self.booking_rooms[booking_id]:
                del self.booking_rooms[booking_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            # Create a copy of the set to iterate safely
            for connection in list(self.active_connections[user_id]):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")

    async def broadcast_to_role(self, message: dict, role: str):
        if role in self.role_rooms:
            # Create a copy of the set to iterate safely
            for user_id in list(self.role_rooms[role]):
                await self.send_personal_message(message, user_id)

    async def broadcast_to_booking(self, message: dict, booking_id: str):
        if booking_id in self.booking_rooms:
            # Create a copy of the set to iterate safely
            for user_id in list(self.booking_rooms[booking_id]):
                await self.send_personal_message(message, user_id)

manager = ConnectionManager()
