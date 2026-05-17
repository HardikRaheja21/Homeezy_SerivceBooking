from fastapi import WebSocket, WebSocketException, status, Query
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings

async def get_current_user_ws(websocket: WebSocket, token: str = Query(...)) -> dict:
    credentials_exception = WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Could not validate credentials")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None or role is None:
            raise credentials_exception
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise credentials_exception
