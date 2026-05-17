# app/schemas/admin.py
"""Pydantic V2 schemas for Admin operations and dashboard."""

from pydantic import BaseModel
from typing import Optional


class AdminDashboardStats(BaseModel):
    """Platform-wide statistics for the admin dashboard."""
    total_users: int
    total_customers: int
    total_workers: int
    pending_worker_approvals: int
    total_bookings: int
    completed_bookings: int
    todays_bookings: int
    total_platform_revenue: float


class ApproveWorkerRequest(BaseModel):
    """Admin action to approve or reject a worker's KYC application."""
    worker_id: str
    approved: bool
    rejection_reason: Optional[str] = None


class BlockUserRequest(BaseModel):
    """Admin action to block a user account with a mandatory reason."""
    user_id: str
    reason: str


class WorkerApprovalResponse(BaseModel):
    message: str
    worker_id: str


class UserBlockResponse(BaseModel):
    message: str
    user_id: str
