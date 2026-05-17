from sqlalchemy import Column, String, Boolean, JSON, ForeignKey, Integer, Float, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class WorkerStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class WorkerProfile(Base):
    __tablename__ = "worker_profiles"

    id = Column(String, ForeignKey("users.id"), primary_key=True)
    
    # Service Details
    service_category = Column(String, nullable=False)  # Plumber, Electrician, etc.
    skills = Column(JSON, default=list)  # ["Pipe repair", "Fixture installation"]
    experience_years = Column(Integer, default=0)
    
    # Verification (MANDATORY)
    government_id_type = Column(String, nullable=True)  # Aadhar, PAN
    government_id_number = Column(String, nullable=True)
    government_id_document = Column(String, nullable=True)  # S3 URL
    police_verification_document = Column(String, nullable=True)
    address_proof_document = Column(String, nullable=True)
    verification_status = Column(SQLEnum(WorkerStatus), default=WorkerStatus.PENDING_APPROVAL)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Work Details
    working_radius_km = Column(Integer, default=5)
    available_timings = Column(JSON, default=dict)  # {monday: ["9-12", "14-18"]}
    base_charge_per_hour = Column(Float, default=0.0)
    emergency_available = Column(Boolean, default=False)
    emergency_charge_multiplier = Column(Float, default=1.5)
    
    # Banking
    bank_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    upi_id = Column(String, nullable=True)
    
    # Emergency Contact
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    
    # Profile Enhancement
    self_intro_video = Column(String, nullable=True)
    certifications = Column(JSON, default=list)
    languages_spoken = Column(JSON, default=["en"])
    
    # Performance Metrics
    total_jobs_completed = Column(Integer, default=0)
    total_earnings = Column(Float, default=0.0)
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    response_time_avg = Column(Float, default=0.0)  # in minutes
    cancellation_rate = Column(Float, default=0.0)
    
    # AI Score
    ai_profile_score = Column(Float, default=0.0)  # 0-100
    ai_recommendations = Column(JSON, default=list)
    
    # Availability
    is_available = Column(Boolean, default=False)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="worker_profile")
    availability_slots = relationship("AvailabilitySlot", back_populates="worker")
