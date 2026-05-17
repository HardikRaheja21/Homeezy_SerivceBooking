from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, JSON, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import uuid

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    WORKER = "worker"
    ADMIN = "admin"

class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    account_status = Column(SQLEnum(AccountStatus), default=AccountStatus.PENDING)
    
    # Profile
    profile_photo = Column(String, nullable=True)
    city = Column(String, nullable=True)
    area = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    preferred_language = Column(String, default="en")
    
    # Security
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String, nullable=True)
    
    # Tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_history = Column(JSON, default=list)
    device_tokens = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer_profile = relationship("CustomerProfile", back_populates="user", uselist=False)
    worker_profile = relationship("WorkerProfile", back_populates="user", uselist=False)
    bookings_as_customer = relationship("Booking", foreign_keys="Booking.customer_id", back_populates="customer")
    bookings_as_worker = relationship("Booking", foreign_keys="Booking.worker_id", back_populates="worker")
    reviews_given = relationship("Review", foreign_keys="Review.reviewer_id", back_populates="reviewer")
    reviews_received = relationship("Review", foreign_keys="Review.reviewed_user_id", back_populates="reviewed_user")
    admin_actions = relationship("AdminAction", back_populates="admin")
