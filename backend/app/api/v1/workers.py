from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.worker import WorkerProfile
from app.models.availability import AvailabilitySlot, SlotStatus

router = APIRouter()

class UpdateAvailabilityRequest(BaseModel):
    is_available: bool
    latitude: float | None = None
    longitude: float | None = None


class CreateAvailabilitySlotRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    is_recurring: bool = False

@router.get("/profile")
async def get_worker_profile(
    current_user: User = Depends(require_role([UserRole.WORKER])),
    db: Session = Depends(get_db)
):
    profile = db.query(WorkerProfile).filter(WorkerProfile.id == current_user.id).first()
    
    status = (
        profile.verification_status.value
        if hasattr(profile.verification_status, "value")
        else profile.verification_status
    )
    return {
        "id": profile.id,
        "service_category": profile.service_category,
        "skills": profile.skills,
        "experience_years": profile.experience_years,
        "verification_status": status,
        "government_id_document": profile.government_id_document,
        "address_proof_document": profile.address_proof_document,
        "police_verification_document": profile.police_verification_document,
        "profile_photo": current_user.profile_photo,
        "working_radius_km": profile.working_radius_km,
        "base_charge_per_hour": profile.base_charge_per_hour,
        "total_jobs_completed": profile.total_jobs_completed,
        "average_rating": profile.average_rating,
        "total_earnings": profile.total_earnings,
        "ai_profile_score": profile.ai_profile_score,
        "ai_recommendations": profile.ai_recommendations,
        "is_available": profile.is_available
    }

@router.post("/availability")
async def update_availability(
    data: UpdateAvailabilityRequest,
    current_user: User = Depends(require_role([UserRole.WORKER])),
    db: Session = Depends(get_db)
):
    profile = db.query(WorkerProfile).filter(WorkerProfile.id == current_user.id).first()
    
    profile.is_available = data.is_available
    if data.latitude and data.longitude:
        profile.current_latitude = data.latitude
        profile.current_longitude = data.longitude
    
    db.commit()
    
    return {"message": "Availability updated", "is_available": profile.is_available}

@router.get("/earnings")
async def get_earnings(
    current_user: User = Depends(require_role([UserRole.WORKER])),
    db: Session = Depends(get_db)
):
    profile = db.query(WorkerProfile).filter(WorkerProfile.id == current_user.id).first()
    
    return {
        "total_earnings": profile.total_earnings,
        "jobs_completed": profile.total_jobs_completed,
        "average_rating": profile.average_rating,
        "pending_payout": 0.0  # Calculate from bookings
    }


@router.post("/availability/slots")
async def create_availability_slot(
    data: CreateAvailabilitySlotRequest,
    current_user: User = Depends(require_role([UserRole.WORKER])),
    db: Session = Depends(get_db)
):
    if data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    slot = AvailabilitySlot(
        worker_id=current_user.id,
        start_time=data.start_time,
        end_time=data.end_time,
        status=SlotStatus.AVAILABLE,
        is_recurring=data.is_recurring,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return {"slot_id": slot.id, "status": slot.status}


@router.get("/availability/slots")
async def list_availability_slots(
    current_user: User = Depends(require_role([UserRole.WORKER])),
    db: Session = Depends(get_db)
):
    slots = (
        db.query(AvailabilitySlot)
        .filter(AvailabilitySlot.worker_id == current_user.id)
        .order_by(AvailabilitySlot.start_time.asc())
        .all()
    )
    return [
        {
            "id": slot.id,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "status": slot.status,
            "is_recurring": slot.is_recurring,
        }
        for slot in slots
    ]
