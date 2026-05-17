from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.storage.cloudinary_provider import CloudinaryProvider

router = APIRouter()

# Strict allowlist — prevents path traversal into unintended Cloudinary directories
ALLOWED_UPLOAD_FOLDERS = {
    "homeezy/profiles",
    "homeezy/complaints",
    "homeezy/kyc",
    "homeezy/services",
}

@router.get("/signature")
async def get_upload_signature(
    folder: str = "homeezy/profiles",
    current_user: User = Depends(get_current_user)
):
    """
    Get a secure Cloudinary upload signature.
    Only permits uploads to whitelisted folder paths.
    """
    if folder not in ALLOWED_UPLOAD_FOLDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload folder not permitted. Allowed: {sorted(ALLOWED_UPLOAD_FOLDERS)}"
        )
    provider = CloudinaryProvider()
    return provider.generate_upload_signature(folder=folder)
