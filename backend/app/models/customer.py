from sqlalchemy import Column, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    id = Column(String, ForeignKey("users.id"), primary_key=True)
    addresses = Column(JSON, default=list)  # [{name, address, pincode, is_default}]
    payment_preferences = Column(JSON, default=dict)  # {preferred_method, saved_cards}
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    notifications_enabled = Column(Boolean, default=True)
    
    # Wallet
    wallet_balance = Column(String, default="0.00")
    
    # AI Preferences
    preferred_worker_ids = Column(JSON, default=list)
    service_history = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", back_populates="customer_profile")
