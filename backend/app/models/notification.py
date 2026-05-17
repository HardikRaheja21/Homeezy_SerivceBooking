from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum

class NotificationType(str, enum.Enum):
    BOOKING_CREATED = "BOOKING_CREATED"
    BOOKING_ASSIGNED = "BOOKING_ASSIGNED"
    BOOKING_COMPLETED = "BOOKING_COMPLETED"
    BOOKING_CANCELLED = "BOOKING_CANCELLED"
    ADMIN_ALERT = "ADMIN_ALERT"
    WORKER_APPROVED = "WORKER_APPROVED"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Optional metadata or link to relevant entity (like booking_id)
    reference_id = Column(String, nullable=True)
    
    user = relationship("User")
