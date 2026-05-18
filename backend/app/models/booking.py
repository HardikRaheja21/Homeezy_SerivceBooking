from sqlalchemy import Column, String, ForeignKey, DateTime, Float, JSON, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import uuid

class BookingStatus(str, enum.Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    WORKER_ENROUTE = "worker_enroute"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Parties
    customer_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    worker_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    
    # Service Details
    service_category = Column(String, nullable=False)
    service_description = Column(Text, nullable=False)
    skills_required = Column(JSON, default=list)
    
    # Location
    service_address = Column(JSON, nullable=False)  # {address, city, pincode, lat, lng}
    
    # Scheduling
    preferred_date = Column(DateTime(timezone=True), nullable=False)
    preferred_time_slot = Column(String, nullable=False)
    estimated_duration_hours = Column(Float, default=2.0)
    
    # Pricing
    estimated_price = Column(Float, nullable=False)
    final_price = Column(Float, nullable=True)
    platform_commission = Column(Float, default=0.0)
    worker_payout = Column(Float, nullable=True)
    
    # Status
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.REQUESTED)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Timeline
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Info
    cancellation_reason = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)
    materials_required = Column(JSON, default=list)
    customer_attachments = Column(JSON, default=list)
    
    # AI Features
    ai_recommended_workers = Column(JSON, default=list)
    ai_price_confidence = Column(Float, default=0.0)
    fraud_detection_score = Column(Float, default=0.0)
    
    # Relationships
    customer = relationship("User", foreign_keys=[customer_id], back_populates="bookings_as_customer")
    worker = relationship("User", foreign_keys=[worker_id], back_populates="bookings_as_worker")
    reviews = relationship("Review", back_populates="booking")
    payment = relationship("Payment", back_populates="booking", uselist=False)
