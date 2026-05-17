# app/schemas/worker.py
"""Pydantic V2 schemas for WorkerProfile entity."""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from app.models.worker import WorkerStatus


class WorkerProfileResponse(BaseModel):
    """Full worker profile — returned to the worker themselves and admin."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    service_category: str
    skills: List[str]
    experience_years: int
    verification_status: WorkerStatus
    working_radius_km: int
    base_charge_per_hour: float
    emergency_available: bool
    emergency_charge_multiplier: float
    total_jobs_completed: int
    average_rating: float
    total_reviews: int
    total_earnings: float
    ai_profile_score: float
    is_available: bool
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None


class WorkerPublicResponse(BaseModel):
    """Public-facing worker card — shown to customers during booking. No banking info."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    service_category: str
    skills: List[str]
    experience_years: int
    base_charge_per_hour: float
    average_rating: float
    total_reviews: int
    total_jobs_completed: int
    emergency_available: bool
    is_available: bool


class WorkerEarningsResponse(BaseModel):
    """Earnings summary for worker dashboard."""
    total_earnings: float
    jobs_completed: int
    average_rating: float
    pending_payout: float
