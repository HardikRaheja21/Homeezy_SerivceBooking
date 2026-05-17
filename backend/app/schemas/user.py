# app/schemas/user.py
"""Pydantic V2 schemas for User entity — request validation and API response shaping."""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, AccountStatus


class UserUpdate(BaseModel):
    """Fields a user can update on their own profile."""
    full_name: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None
    pincode: Optional[str] = None
    preferred_language: Optional[str] = None


class UserResponse(BaseModel):
    """Public user representation returned from API endpoints."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: str
    phone: str
    role: UserRole
    account_status: AccountStatus
    profile_photo: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None
    pincode: Optional[str] = None
    preferred_language: str
    email_verified: bool
    phone_verified: bool
    created_at: datetime


class TokenData(BaseModel):
    """Decoded JWT payload structure."""
    sub: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class TokenResponse(BaseModel):
    """Response returned after successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
