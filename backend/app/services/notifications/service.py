import uuid
from typing import List
from fastapi import WebSocket
from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType
from app.websockets.manager import manager
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    async def create_notification(
        db: Session,
        user_id: str,
        type: NotificationType,
        title: str,
        message: str,
        reference_id: str = None
    ) -> Notification:
        # 1. Save to DB
        notif = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            reference_id=reference_id
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        
        # 2. Push via WebSocket
        await manager.send_personal_message(
            {
                "type": type.value,
                "message": message,
                "data": {
                    "id": notif.id,
                    "title": title,
                    "reference_id": reference_id
                }
            },
            user_id
        )
        return notif

    @staticmethod
    def get_user_notifications(db: Session, user_id: str, limit: int = 50) -> List[Notification]:
        return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def mark_as_read(db: Session, notification_id: str, user_id: str) -> bool:
        notif = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
        if notif:
            notif.is_read = True
            db.commit()
            return True
        return False
