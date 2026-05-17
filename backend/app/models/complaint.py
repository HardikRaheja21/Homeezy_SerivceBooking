# app/models/complaint.py
"""Complaint model — tracks customer complaints about bookings for admin resolution."""

from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import uuid


class ComplaintType(str, enum.Enum):
    WORKER_BEHAVIOR = "worker_behavior"
    SERVICE_QUALITY = "service_quality"
    PAYMENT_ISSUE = "payment_issue"
    OVERCHARGING = "overcharging"
    NO_SHOW = "no_show"
    DAMAGE = "damage"
    OTHER = "other"


class ComplaintStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Parties involved
    customer_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False, index=True)
    worker_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    # Complaint content
    complaint_type = Column(SQLEnum(ComplaintType), nullable=False)
    description = Column(Text, nullable=False)

    # Lifecycle
    status = Column(SQLEnum(ComplaintStatus), default=ComplaintStatus.OPEN, nullable=False, index=True)

    # Resolution (filled by admin)
    resolution = Column(Text, nullable=True)
    refund_approved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(String, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer = relationship("User", foreign_keys=[customer_id])
    worker = relationship("User", foreign_keys=[worker_id])
    booking = relationship("Booking")
    resolver = relationship("User", foreign_keys=[resolved_by])
