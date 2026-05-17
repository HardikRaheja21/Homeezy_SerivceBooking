import cloudinary
import cloudinary.uploader
import cloudinary.utils
from app.core.config import settings
import time

class CloudinaryProvider:
    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )

    def generate_upload_signature(self, folder: str = "homeezy") -> dict:
        """
        Generates a signed signature for secure frontend-direct uploads.
        """
        timestamp = int(time.time())
        params_to_sign = {
            "timestamp": timestamp,
            "folder": folder
        }
        
        signature = cloudinary.utils.api_sign_request(
            params_to_sign, 
            settings.CLOUDINARY_API_SECRET
        )
        
        return {
            "timestamp": timestamp,
            "signature": signature,
            "api_key": settings.CLOUDINARY_API_KEY,
            "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
            "folder": folder
        }
