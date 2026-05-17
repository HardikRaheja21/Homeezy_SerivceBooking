from app.worker import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="storage.process_image")
def process_image_task(image_id: str):
    # TODO: Implement image processing (resize, watermark, etc.)
    logger.info(f"Processing image {image_id}")
    return {"status": "success", "image_id": image_id}
