# app/schemas/complaint.py
"""Pydantic V2 schemas for Complaint entity."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from app.models.complaint import ComplaintStatus, ComplaintType


class ComplaintCreate(BaseModel):
    """Customer request to raise a complaint about a booking."""
    booking_id: str
    complaint_type: ComplaintType
    description: str = Field(min_length=10, max_length=2000,
                             description="Describe the issue in detail")


class ComplaintResolve(BaseModel):
    """Admin action to resolve a complaint."""
    resolution: str = Field(min_length=10, max_length=1000)
    refund_approved: bool = False


class ComplaintResponse(BaseModel):
    """Complaint detail returned from API."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_id: str
    customer_id: str
    worker_id: Optional[str] = None
    complaint_type: ComplaintType
    description: str
    status: ComplaintStatus
    resolution: Optional[str] = None
    refund_approved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None
