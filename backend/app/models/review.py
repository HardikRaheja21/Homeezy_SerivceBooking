from sqlalchemy import Column, String, ForeignKey, Integer, Text, JSON, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False)
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=False)
    reviewed_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    rating = Column(Integer, nullable=False)  # 1-5
    review_text = Column(Text, nullable=True)
    
    # AI Sentiment Analysis
    sentiment_score = Column(Float, default=0.0)  # -1 to 1
    sentiment_label = Column(String, nullable=True)  # positive, negative, neutral
    key_phrases = Column(JSON, default=list)
    is_flagged_fake = Column(Boolean, default=False)
    
    # Metadata
    helpful_count = Column(Integer, default=0)
    reported_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    booking = relationship("Booking", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewed_user = relationship("User", foreign_keys=[reviewed_user_id], back_populates="reviews_received")
