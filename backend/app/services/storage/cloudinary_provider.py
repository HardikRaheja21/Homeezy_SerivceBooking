import logging
import time
from typing import BinaryIO

import cloudinary
import cloudinary.uploader
import cloudinary.utils

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_cloudinary_configured() -> bool:
    return bool(
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    )


class CloudinaryProvider:
    def __init__(self):
        if is_cloudinary_configured():
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True,
            )

    def generate_upload_signature(self, folder: str = "homeezy") -> dict:
        if not is_cloudinary_configured():
            raise ValueError("Cloudinary is not configured")
        timestamp = int(time.time())
        params_to_sign = {"timestamp": timestamp, "folder": folder}
        signature = cloudinary.utils.api_sign_request(
            params_to_sign, settings.CLOUDINARY_API_SECRET
        )
        return {
            "timestamp": timestamp,
            "signature": signature,
            "api_key": settings.CLOUDINARY_API_KEY,
            "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
            "folder": folder,
        }

    def upload_image(
        self,
        file_bytes: bytes,
        folder: str,
        public_id: str,
    ) -> dict:
        if not is_cloudinary_configured():
            raise ValueError("Cloudinary is not configured")
        result = cloudinary.uploader.upload(
            file_bytes,
            folder=folder,
            public_id=public_id,
            resource_type="image",
            overwrite=True,
        )
        return {
            "url": result.get("secure_url") or result.get("url"),
            "public_id": result.get("public_id"),
        }
