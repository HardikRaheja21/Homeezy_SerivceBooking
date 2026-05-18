# app/api/v1/bookings.py
"""
Bookings API — full service booking lifecycle for Homeezy.

Business rules enforced here:
- Bookings cannot be in the past
- Workers cannot accept already-accepted bookings
- Status transitions are strictly validated
- Pagination on list endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.logging_config import get_logger
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus
from app.services.ai_service import AIService
from app.services.notification_service import NotificationService
from app.utils.realtime import notify_booking_event

router = APIRouter()
ai_service = AIService()
notification_service = NotificationService()
logger = get_logger(__name__)


def _format_address(service_address: dict | None) -> str:
    if not service_address:
        return "Address not provided"
    if isinstance(service_address, dict) and service_address.get("full_address"):
        return str(service_address["full_address"])
    parts = [
        service_address.get("address") if isinstance(service_address, dict) else None,
        service_address.get("city") if isinstance(service_address, dict) else None,
        service_address.get("pincode") if isinstance(service_address, dict) else None,
    ]
    return ", ".join(p for p in parts if p) or "Address not provided"


def _can_view_booking(booking: Booking, user: User) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    if booking.customer_id == user.id:
        return True
    if booking.worker_id and booking.worker_id == user.id:
        return True
    if user.role == UserRole.WORKER and user.id in (booking.ai_recommended_workers or []):
        return True
    return False


def _serialize_booking_detail(booking: Booking, current_user: User) -> dict:
    status = booking.status.value if hasattr(booking.status, "value") else booking.status
    payment_status = (
        booking.payment_status.value
        if hasattr(booking.payment_status, "value")
        else booking.payment_status
    )
    is_customer = booking.customer_id == current_user.id
    is_worker = booking.worker_id == current_user.id
    return {
        "id": booking.id,
        "customer_id": booking.customer_id,
        "worker_id": booking.worker_id,
        "service_category": booking.service_category,
        "service_description": booking.service_description,
        "problem_description": booking.service_description,
        "skills_required": booking.skills_required or [],
        "service_address": booking.service_address,
        "address": _format_address(
            booking.service_address if isinstance(booking.service_address, dict) else None
        ),
        "preferred_date": booking.preferred_date,
        "preferred_time_slot": booking.preferred_time_slot,
        "estimated_duration_hours": booking.estimated_duration_hours,
        "estimated_price": booking.estimated_price,
        "final_price": booking.final_price,
        "status": status,
        "payment_status": payment_status,
        "special_instructions": booking.special_instructions,
        "cancellation_reason": booking.cancellation_reason,
        "materials_required": booking.materials_required or [],
        "customer_attachments": booking.customer_attachments or [],
        "customer": {
            "id": booking.customer.id,
            "name": booking.customer.full_name,
            "email": booking.customer.email if is_worker or current_user.role == UserRole.ADMIN else None,
            "phone": booking.customer.phone if is_worker or current_user.role == UserRole.ADMIN else None,
        },
        "worker": {
            "id": booking.worker.id,
            "name": booking.worker.full_name,
            "phone": booking.worker.phone,
        }
        if booking.worker
        else None,
        "timeline": {
            "requested_at": booking.requested_at,
            "accepted_at": booking.accepted_at,
            "started_at": booking.started_at,
            "completed_at": booking.completed_at,
            "cancelled_at": booking.cancelled_at,
        },
        "permissions": {
            "is_customer": is_customer,
            "is_worker": is_worker,
            "is_admin": current_user.role == UserRole.ADMIN,
            "can_accept": (
                current_user.role == UserRole.WORKER
                and status == BookingStatus.REQUESTED.value
                and booking.worker_id is None
                and (
                    not booking.ai_recommended_workers
                    or current_user.id in booking.ai_recommended_workers
                )
            ),
            "can_decline": (
                current_user.role == UserRole.WORKER
                and status == BookingStatus.REQUESTED.value
                and booking.worker_id is None
            ),
            "can_cancel": is_customer
            and status in (BookingStatus.REQUESTED.value, BookingStatus.ACCEPTED.value),
            "can_review": is_customer and status == BookingStatus.COMPLETED.value,
            "can_upload_photos": is_customer
            and status in (BookingStatus.REQUESTED.value, BookingStatus.ACCEPTED.value),
        },
    }


def _serialize_booking_summary(b: Booking) -> dict:
    status = b.status.value if hasattr(b.status, "value") else b.status
    return {
        "id": b.id,
        "service_category": b.service_category,
        "service_description": b.service_description,
        "problem_description": b.service_description,
        "status": status,
        "preferred_date": b.preferred_date,
        "preferred_time_slot": b.preferred_time_slot,
        "estimated_price": b.estimated_price,
        "service_address": b.service_address,
        "address": _format_address(b.service_address if isinstance(b.service_address, dict) else None),
        "requested_at": b.requested_at,
        "worker_id": b.worker_id,
    }


# ── Request schemas (inline — full schemas in app/schemas/booking.py) ─────────

class CreateBookingRequest(BaseModel):
    service_category: str
    service_description: str
    skills_required: list[str]
    service_address: dict
    preferred_date: datetime
    preferred_time_slot: str
    estimated_duration_hours: float = 2.0
    special_instructions: str | None = None
    materials_required: list[str] = []
    customer_attachments: list[str] = []


class UpdateBookingStatusRequest(BaseModel):
    status: BookingStatus
    reason: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/create",
    summary="Create a new service booking",
    description="Customer creates a booking. AI estimates price, recommends workers, and checks for fraud.",
)
async def create_booking(
    data: CreateBookingRequest,
    current_user: User = Depends(require_role([UserRole.CUSTOMER])),
    db: Session = Depends(get_db),
):
    # ── Business rule: booking date cannot be in the past ────────────────────
    now = datetime.now(timezone.utc)
    preferred = data.preferred_date
    if preferred.tzinfo is None:
        preferred = preferred.replace(tzinfo=timezone.utc)
    if preferred <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking date must be in the future.",
        )

    # AI Price Estimation
    price_estimate = await ai_service.estimate_price(
        db=db,
        service_category=data.service_category,
        skills=data.skills_required,
        duration=data.estimated_duration_hours,
        location=data.service_address,
    )

    # AI Worker Recommendations
    recommended_workers = await ai_service.recommend_workers(
        service_category=data.service_category,
        skills_required=data.skills_required,
        location=data.service_address,
        preferred_date=data.preferred_date,
        db=db,
    )

    # Fraud Detection
    fraud_score = await ai_service.detect_fraud(
        user_id=current_user.id,
        booking_data=data.dict(),
        db=db,
    )

    if fraud_score > 0.8:
        logger.warning("High fraud score %.2f for user %s", fraud_score, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Suspicious activity detected. Please contact support.",
        )

    booking = Booking(
        customer_id=current_user.id,
        service_category=data.service_category,
        service_description=data.service_description,
        skills_required=data.skills_required,
        service_address=data.service_address,
        preferred_date=data.preferred_date,
        preferred_time_slot=data.preferred_time_slot,
        estimated_duration_hours=data.estimated_duration_hours,
        estimated_price=price_estimate["amount"],
        special_instructions=data.special_instructions,
        materials_required=data.materials_required,
        customer_attachments=data.customer_attachments[:10],
        ai_recommended_workers=[w["worker_id"] for w in recommended_workers[:5]],
        ai_price_confidence=price_estimate["confidence"],
        fraud_detection_score=fraud_score,
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)
    logger.info("Booking %s created by customer %s", booking.id, current_user.id)

    for worker_data in recommended_workers[:5]:
        await notification_service.send_booking_request(
            worker_id=worker_data["worker_id"],
            booking_id=booking.id,
            service_category=data.service_category,
        )

    await notify_booking_event(
        booking.id,
        "BOOKING_CREATED",
        f"New {data.service_category} booking created",
        customer_id=current_user.id,
    )

    return {
        "booking_id": booking.id,
        "status": booking.status,
        "estimated_price": booking.estimated_price,
        "recommended_workers": recommended_workers[:5],
        "message": "Booking created successfully. Workers have been notified.",
    }


@router.get(
    "/my-bookings",
    summary="List my bookings",
    description="Returns paginated list of bookings for the authenticated user (customer or worker).",
)
async def get_my_bookings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    booking_status: BookingStatus | None = Query(default=None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.CUSTOMER:
        query = db.query(Booking).filter(Booking.customer_id == current_user.id)
    else:
        query = db.query(Booking).filter(Booking.worker_id == current_user.id)

    if booking_status:
        query = query.filter(Booking.status == booking_status)

    total = query.count()
    bookings = (
        query.order_by(Booking.requested_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [_serialize_booking_summary(b) for b in bookings],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get(
    "/available",
    summary="List available booking requests for workers",
    description="Returns unassigned REQUESTED bookings recommended for the current worker.",
)
async def get_available_bookings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.WORKER])),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Booking)
        .filter(Booking.status == BookingStatus.REQUESTED, Booking.worker_id.is_(None))
        .order_by(Booking.requested_at.desc())
    )
    all_requested = query.all()
    worker_id = current_user.id
    filtered = [
        b
        for b in all_requested
        if not b.ai_recommended_workers or worker_id in (b.ai_recommended_workers or [])
    ]
    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    return {
        "items": [_serialize_booking_summary(b) for b in page_items],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get(
    "/{booking_id}",
    summary="Get booking details",
    description="Returns full booking details. Only parties involved and admins can view.",
)
async def get_booking_details(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .options(joinedload(Booking.customer), joinedload(Booking.worker))
        .filter(Booking.id == booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if not _can_view_booking(booking, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view this booking")

    return _serialize_booking_detail(booking, current_user)


@router.post(
    "/{booking_id}/accept",
    summary="Worker accepts a booking",
    description="Worker accepts a booking. Only workers in the AI-recommended list can accept.",
)
async def accept_booking(
    booking_id: str,
    current_user: User = Depends(require_role([UserRole.WORKER])),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Business rule: only accept REQUESTED bookings
    if booking.status != BookingStatus.REQUESTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking cannot be accepted — current status is '{booking.status.value}'.",
        )

    # Business rule: worker must be in the recommended list when recommendations exist
    recommended = booking.ai_recommended_workers or []
    if recommended and current_user.id not in recommended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You were not recommended for this booking.",
        )

    booking.worker_id = current_user.id
    booking.status = BookingStatus.ACCEPTED
    booking.accepted_at = datetime.now(timezone.utc)
    db.commit()

    await notification_service.send_booking_accepted(
        customer_id=booking.customer_id,
        worker_name=current_user.full_name,
        booking_id=booking.id,
    )

    logger.info("Booking %s accepted by worker %s", booking_id, current_user.id)
    await notify_booking_event(
        booking.id,
        "BOOKING_UPDATE",
        f"Worker {current_user.full_name} accepted your booking",
        customer_id=booking.customer_id,
        worker_id=current_user.id,
    )
    return {"message": "Booking accepted successfully", "booking_id": booking.id}


@router.post(
    "/{booking_id}/update-status",
    summary="Update booking status",
    description="Advance booking through its lifecycle. Strict state machine enforced.",
)
async def update_booking_status(
    booking_id: str,
    data: UpdateBookingStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.worker_id != current_user.id and booking.customer_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")

    # ── State machine ─────────────────────────────────────────────────────────
    VALID_TRANSITIONS = {
        BookingStatus.WORKER_ENROUTE: (BookingStatus.ACCEPTED,),
        BookingStatus.IN_PROGRESS: (BookingStatus.WORKER_ENROUTE,),
        BookingStatus.COMPLETED: (BookingStatus.IN_PROGRESS,),
    }

    if data.status in VALID_TRANSITIONS:
        if booking.status not in VALID_TRANSITIONS[data.status]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from '{booking.status.value}' to '{data.status.value}'.",
            )

    if data.status == BookingStatus.WORKER_ENROUTE:
        booking.status = BookingStatus.WORKER_ENROUTE

    elif data.status == BookingStatus.IN_PROGRESS:
        booking.status = BookingStatus.IN_PROGRESS
        booking.started_at = datetime.now(timezone.utc)

    elif data.status == BookingStatus.COMPLETED:
        booking.status = BookingStatus.COMPLETED
        booking.completed_at = datetime.now(timezone.utc)

    elif data.status == BookingStatus.CANCELLED:
        if booking.status in (BookingStatus.COMPLETED, BookingStatus.DISPUTED):
            raise HTTPException(status_code=400, detail="Cannot cancel completed or disputed bookings.")
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.now(timezone.utc)
        booking.cancellation_reason = data.reason

    else:
        raise HTTPException(status_code=400, detail=f"Invalid target status: {data.status.value}")

    db.commit()
    logger.info("Booking %s status → %s by %s", booking_id, data.status, current_user.id)
    new_status = booking.status.value if hasattr(booking.status, "value") else booking.status
    await notify_booking_event(
        booking.id,
        "BOOKING_UPDATE",
        f"Booking status updated to {new_status}",
        customer_id=booking.customer_id,
        worker_id=booking.worker_id,
    )
    return {"message": "Status updated successfully", "new_status": new_status}
