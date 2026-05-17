from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.notifications.service import NotificationService

router = APIRouter()

@router.get("/")
def get_notifications(limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "items": NotificationService.get_user_notifications(db, current_user.id, limit)
    }

@router.put("/{notification_id}/read")
def mark_notification_read(notification_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = NotificationService.mark_as_read(db, notification_id, current_user.id)
    return {
        "success": success
    }
