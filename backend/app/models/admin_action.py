from sqlalchemy import Column, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class AdminAction(Base):
    __tablename__ = "admin_actions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    action_type = Column(String, nullable=False, index=True)
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False, index=True)
    reason = Column(String, nullable=True)
    details = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    admin = relationship("User", back_populates="admin_actions")

