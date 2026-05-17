from sqlalchemy import Column, String, ForeignKey, Float, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import uuid

class PaymentMethod(str, enum.Enum):
    CARD = "card"
    UPI = "upi"
    WALLET = "wallet"
    CASH = "cash"
    NET_BANKING = "net_banking"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False, unique=True)
    
    amount = Column(Float, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    
    # Gateway Details
    gateway_order_id = Column(String, nullable=True, unique=True)
    gateway_transaction_id = Column(String, nullable=True, unique=True)
    gateway_response = Column(JSON, default=dict)
    
    # Status
    status = Column(String, default="pending")  # pending, success, failed, refunded
    
    # Timestamps
    initiated_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Refund
    refund_amount = Column(Float, default=0.0)
    refund_reason = Column(String, nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    booking = relationship("Booking", back_populates="payment")
