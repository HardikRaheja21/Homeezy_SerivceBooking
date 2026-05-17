from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.customer import CustomerProfile
from app.models.worker import WorkerProfile

router = APIRouter()

class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    city: str | None = None
    area: str | None = None
    pincode: str | None = None
    preferred_language: str | None = None

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
        "profile_photo": current_user.profile_photo,
        "city": current_user.city,
        "area": current_user.area,
        "account_status": current_user.account_status,
        "email_verified": current_user.email_verified,
        "phone_verified": current_user.phone_verified
    }

@router.put("/profile")
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if data.full_name:
        current_user.full_name = data.full_name
    if data.city:
        current_user.city = data.city
    if data.area:
        current_user.area = data.area
    if data.pincode:
        current_user.pincode = data.pincode
    if data.preferred_language:
        current_user.preferred_language = data.preferred_language
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Profile updated successfully"}

@router.post("/upload-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile photo"""
    # Validate file
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # In production, upload to S3
    # import boto3
    # s3_client = boto3.client('s3')
    # file_key = f"profiles/{current_user.id}/{file.filename}"
    # s3_client.upload_fileobj(file.file, settings.AWS_BUCKET_NAME, file_key)
    # photo_url = f"https://{settings.AWS_BUCKET_NAME}.s3.amazonaws.com/{file_key}"
    
    # Mock URL for now
    photo_url = f"/uploads/profiles/{current_user.id}.jpg"
    
    current_user.profile_photo = photo_url
    db.commit()
    
    return {"message": "Photo uploaded successfully", "photo_url": photo_url}
