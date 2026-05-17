# app/api/v1/complaints.py
"""
Complaints API — customers can raise complaints about bookings;
admins can list, review, and resolve them.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.booking import Booking
from app.models.complaint import Complaint, ComplaintStatus
from app.schemas.complaint import ComplaintCreate, ComplaintResolve, ComplaintResponse

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def raise_complaint(
    data: ComplaintCreate,
    current_user: User = Depends(require_role([UserRole.CUSTOMER])),
    db: Session = Depends(get_db),
):
    """
    Customer raises a complaint about a booking.
    One complaint per type per booking is allowed to avoid spam.
    """
    # Verify booking belongs to this customer
    booking = db.query(Booking).filter(Booking.id == data.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to complain about this booking")

    # Prevent duplicate complaint for same booking + type
    existing = db.query(Complaint).filter(
        Complaint.booking_id == data.booking_id,
        Complaint.customer_id == current_user.id,
        Complaint.complaint_type == data.complaint_type,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A complaint of this type has already been raised for this booking",
        )

    complaint = Complaint(
        customer_id=current_user.id,
        booking_id=data.booking_id,
        worker_id=booking.worker_id,
        complaint_type=data.complaint_type,
        description=data.description,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return {
        "complaint_id": complaint.id,
        "status": complaint.status,
        "message": "Complaint raised successfully. Our team will review it within 24 hours.",
    }


@router.get("/my-complaints")
async def get_my_complaints(
    current_user: User = Depends(require_role([UserRole.CUSTOMER])),
    db: Session = Depends(get_db),
):
    """Customer views all their own complaints."""
    complaints = (
        db.query(Complaint)
        .filter(Complaint.customer_id == current_user.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "booking_id": c.booking_id,
            "complaint_type": c.complaint_type,
            "description": c.description,
            "status": c.status,
            "resolution": c.resolution,
            "refund_approved": c.refund_approved,
            "created_at": c.created_at,
            "resolved_at": c.resolved_at,
        }
        for c in complaints
    ]


@router.get("/admin/all")
async def admin_list_complaints(
    complaint_status: ComplaintStatus | None = None,
    limit: int = 50,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Admin views all complaints, optionally filtered by status."""
    query = db.query(Complaint)
    if complaint_status:
        query = query.filter(Complaint.status == complaint_status)
    complaints = query.order_by(Complaint.created_at.desc()).limit(limit).all()

    return [
        {
            "id": c.id,
            "booking_id": c.booking_id,
            "customer_name": c.customer.full_name if c.customer else None,
            "worker_name": c.worker.full_name if c.worker else None,
            "complaint_type": c.complaint_type,
            "description": c.description,
            "status": c.status,
            "created_at": c.created_at,
        }
        for c in complaints
    ]


@router.post("/{complaint_id}/resolve")
async def resolve_complaint(
    complaint_id: str,
    data: ComplaintResolve,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Admin resolves a complaint, optionally approving a refund."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.status == ComplaintStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Complaint is already resolved")

    complaint.status = ComplaintStatus.RESOLVED
    complaint.resolution = data.resolution
    complaint.refund_approved = data.refund_approved
    complaint.resolved_by = current_user.id
    complaint.resolved_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "complaint_id": complaint.id,
        "status": complaint.status,
        "refund_approved": complaint.refund_approved,
        "message": "Complaint resolved successfully",
    }
