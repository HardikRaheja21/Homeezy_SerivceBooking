from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole, AccountStatus
from app.models.worker import WorkerProfile, WorkerStatus
from app.models.booking import Booking, BookingStatus
from app.models.admin_action import AdminAction
from datetime import datetime, timezone, timedelta

router = APIRouter()

class ApproveWorkerRequest(BaseModel):
    worker_id: str
    approved: bool
    rejection_reason: str | None = None

class BlockUserRequest(BaseModel):
    user_id: str
    reason: str

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    total_customers = db.query(User).filter(User.role == UserRole.CUSTOMER).count()
    total_workers = db.query(User).filter(User.role == UserRole.WORKER).count()
    pending_workers = db.query(WorkerProfile).filter(
        WorkerProfile.verification_status == WorkerStatus.PENDING_APPROVAL
    ).count()
    
    total_bookings = db.query(Booking).count()
    completed_bookings = db.query(Booking).filter(
        Booking.status == BookingStatus.COMPLETED
    ).count()
    
    # Revenue calculation
    total_revenue = db.query(func.sum(Booking.platform_commission)).filter(
        Booking.status == BookingStatus.COMPLETED
    ).scalar() or 0
    
    # Today's bookings
    today = datetime.now(timezone.utc).date()
    todays_bookings = db.query(Booking).filter(
        func.date(Booking.requested_at) == today
    ).count()
    
    return {
        "total_users": total_users,
        "total_customers": total_customers,
        "total_workers": total_workers,
        "pending_worker_approvals": pending_workers,
        "total_bookings": total_bookings,
        "completed_bookings": completed_bookings,
        "todays_bookings": todays_bookings,
        "total_platform_revenue": round(total_revenue, 2)
    }

@router.get("/workers/pending")
async def get_pending_workers(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    workers = db.query(WorkerProfile).join(User).filter(
        WorkerProfile.verification_status == WorkerStatus.PENDING_APPROVAL
    ).all()
    
    return [
        {
            "id": w.id,
            "full_name": w.user.full_name,
            "email": w.user.email,
            "phone": w.user.phone,
            "service_category": w.service_category,
            "skills": w.skills,
            "experience_years": w.experience_years,
            "government_id_type": w.government_id_type,
            "government_id_number": w.government_id_number,
            "government_id_document": w.government_id_document,
            "address_proof_document": w.address_proof_document,
            "police_verification_document": w.police_verification_document,
            "profile_photo": w.user.profile_photo,
            "created_at": w.user.created_at,
        }
        for w in workers
    ]

@router.post("/workers/approve")
async def approve_worker(
    data: ApproveWorkerRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    worker = db.query(WorkerProfile).filter(WorkerProfile.id == data.worker_id).first()
    
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    if data.approved:
        worker.verification_status = WorkerStatus.APPROVED
        worker.verified_at = datetime.now(timezone.utc)
        worker.user.account_status = AccountStatus.ACTIVE
        message = "Worker approved successfully"
    else:
        worker.verification_status = WorkerStatus.REJECTED
        worker.user.account_status = AccountStatus.BLOCKED
        message = "Worker rejected"
    db.add(
        AdminAction(
            admin_id=current_user.id,
            action_type="worker_approval",
            target_type="worker",
            target_id=worker.id,
            reason=data.rejection_reason,
            details={"approved": data.approved},
        )
    )
    
    db.commit()
    
    return {"message": message, "worker_id": worker.id}

@router.post("/users/block")
async def block_user(
    data: BlockUserRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == data.user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Cannot block admin users")
    
    user.account_status = AccountStatus.BLOCKED
    db.add(
        AdminAction(
            admin_id=current_user.id,
            action_type="block_user",
            target_type="user",
            target_id=user.id,
            reason=data.reason,
            details={"role": user.role.value},
        )
    )
    db.commit()
    
    return {"message": "User blocked successfully", "user_id": user.id}

@router.get("/bookings/recent")
async def get_recent_bookings(
    limit: int = 50,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    bookings = db.query(Booking).order_by(
        Booking.requested_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": b.id,
            "customer_name": b.customer.full_name,
            "worker_name": b.worker.full_name if b.worker else "Pending",
            "service_category": b.service_category,
            "status": b.status.value if hasattr(b.status, "value") else b.status,
            "estimated_price": b.estimated_price,
            "requested_at": b.requested_at,
            "fraud_score": b.fraud_detection_score
        }
        for b in bookings
    ]
