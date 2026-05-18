from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.worker import WorkerProfile
from app.models.booking import Booking
from app.services.storage.cloudinary_provider import CloudinaryProvider, is_cloudinary_configured

router = APIRouter()

ALLOWED_UPLOAD_FOLDERS = {
    "homeezy/profiles",
    "homeezy/kyc",
    "homeezy/bookings",
}

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
MAX_FILE_BYTES = 5 * 1024 * 1024

WORKER_DOC_FIELDS = {
    "government_id": "government_id_document",
    "address_proof": "address_proof_document",
    "police_verification": "police_verification_document",
}


@router.get("/status")
async def upload_service_status():
    configured = is_cloudinary_configured()
    return {
        "cloudinary_configured": configured,
        "uploads_available": configured,
        "max_file_mb": MAX_FILE_BYTES // (1024 * 1024),
        "allowed_types": sorted(ALLOWED_IMAGE_TYPES),
    }


@router.get("/signature")
async def get_upload_signature(
    folder: str = "homeezy/profiles",
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    if not is_cloudinary_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File uploads are temporarily unavailable. Please try again later.",
        )
    if folder not in ALLOWED_UPLOAD_FOLDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload folder not permitted. Allowed: {sorted(ALLOWED_UPLOAD_FOLDERS)}",
        )
    provider = CloudinaryProvider()
    return provider.generate_upload_signature(folder=folder)


async def _validate_image_upload(file: UploadFile) -> bytes:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}",
        )
    data = await file.read()
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_BYTES // (1024 * 1024)}MB.",
        )
    if len(data) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    return data


def _require_cloudinary():
    if not is_cloudinary_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File uploads are temporarily unavailable. Your account works without uploads.",
        )


@router.post("/profile-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_cloudinary()
    data = await _validate_image_upload(file)
    provider = CloudinaryProvider()
    result = provider.upload_image(
        data,
        folder="homeezy/profiles",
        public_id=str(current_user.id),
    )
    current_user.profile_photo = result["url"]
    db.commit()
    return {"message": "Profile photo updated", "url": result["url"]}


@router.post("/worker/document")
async def upload_worker_document(
    doc_type: str = Query(..., description="government_id | address_proof | police_verification"),
    file: UploadFile = File(...),
    current_user: User = Depends(require_role([UserRole.WORKER])),
    db: Session = Depends(get_db),
):
    if doc_type not in WORKER_DOC_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid doc_type. Allowed: {list(WORKER_DOC_FIELDS.keys())}",
        )
    _require_cloudinary()
    data = await _validate_image_upload(file)
    profile = db.query(WorkerProfile).filter(WorkerProfile.id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    provider = CloudinaryProvider()
    result = provider.upload_image(
        data,
        folder="homeezy/kyc",
        public_id=f"{current_user.id}_{doc_type}",
    )
    setattr(profile, WORKER_DOC_FIELDS[doc_type], result["url"])
    db.commit()
    return {"message": "Document uploaded", "doc_type": doc_type, "url": result["url"]}


@router.post("/booking/{booking_id}/attachment")
async def upload_booking_attachment(
    booking_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role([UserRole.CUSTOMER])),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    _require_cloudinary()
    data = await _validate_image_upload(file)
    attachments = list(booking.customer_attachments or [])
    if len(attachments) >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images per booking")

    provider = CloudinaryProvider()
    result = provider.upload_image(
        data,
        folder="homeezy/bookings",
        public_id=f"{booking_id}_{len(attachments)}",
    )
    attachments.append(result["url"])
    booking.customer_attachments = attachments
    db.commit()
    return {"message": "Image attached", "url": result["url"], "attachments": attachments}
