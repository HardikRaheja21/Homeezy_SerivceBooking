# app/schemas/booking.py
"""Pydantic V2 schemas for Booking entity — creation, status, and list views."""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.booking import BookingStatus, PaymentStatus


class BookingCreate(BaseModel):
    """Request body for creating a new service booking."""
    service_category: str
    service_description: str
    skills_required: List[str]
    service_address: Dict[str, Any]   # {address, city, pincode, lat, lng}
    preferred_date: datetime
    preferred_time_slot: str
    estimated_duration_hours: float = 2.0
    special_instructions: Optional[str] = None
    materials_required: List[str] = []


class BookingStatusUpdate(BaseModel):
    """Request body for updating booking lifecycle status."""
    status: BookingStatus
    reason: Optional[str] = None


class BookingListItem(BaseModel):
    """Compact booking representation for list views."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    service_category: str
    status: BookingStatus
    payment_status: PaymentStatus
    preferred_date: datetime
    estimated_price: float
    requested_at: datetime


class BookingResponse(BaseModel):
    """Full booking detail returned for single-booking views."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    service_category: str
    service_description: str
    skills_required: List[str]
    service_address: Dict[str, Any]
    preferred_date: datetime
    preferred_time_slot: str
    estimated_duration_hours: float
    estimated_price: float
    final_price: Optional[float] = None
    status: BookingStatus
    payment_status: PaymentStatus
    special_instructions: Optional[str] = None
    cancellation_reason: Optional[str] = None
    requested_at: datetime
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


class BookingCreateResponse(BaseModel):
    """Response returned immediately after creating a booking."""
    booking_id: str
    status: BookingStatus
    estimated_price: float
    recommended_workers: List[Dict[str, Any]]
    message: str
