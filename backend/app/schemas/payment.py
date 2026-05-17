# app/schemas/payment.py
"""Pydantic V2 schemas for Payment entity."""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.payment import PaymentMethod


class PaymentInitiateRequest(BaseModel):
    """Request to start a payment for a completed booking."""
    booking_id: str
    payment_method: PaymentMethod


class PaymentVerifyRequest(BaseModel):
    """Request to verify a Razorpay payment signature."""
    booking_id: str
    gateway_order_id: str
    gateway_transaction_id: str
    signature: str


class PaymentResponse(BaseModel):
    """Full payment record."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_id: str
    amount: float
    payment_method: PaymentMethod
    status: str
    gateway_order_id: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    refund_amount: float
    refund_reason: Optional[str] = None
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None


class PaymentInitiateResponse(BaseModel):
    """Response after initiating a payment — contains Razorpay order details."""
    payment_id: str
    gateway_order_id: str
    amount: float
    currency: str = "INR"
    razorpay_key_id: str
