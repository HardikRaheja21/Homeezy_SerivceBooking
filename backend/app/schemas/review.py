# app/schemas/review.py
"""Pydantic V2 schemas for Review entity."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class ReviewCreate(BaseModel):
    """Request body for submitting a review after a completed booking."""
    booking_id: str
    rating: int = Field(ge=1, le=5, description="Rating from 1 (worst) to 5 (best)")
    review_text: str


class ReviewResponse(BaseModel):
    """Full review record."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_id: str
    rating: int
    review_text: Optional[str] = None
    sentiment_label: Optional[str] = None
    key_phrases: List[str] = []
    helpful_count: int
    created_at: datetime


class ReviewListItem(BaseModel):
    """Review in a list — includes reviewer name for display."""
    id: str
    rating: int
    review_text: Optional[str] = None
    sentiment_label: Optional[str] = None
    key_phrases: List[str] = []
    helpful_count: int
    reviewer_name: str
    created_at: datetime
