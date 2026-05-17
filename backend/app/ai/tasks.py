from app.worker import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="ai.categorize_service")
def categorize_service_task(description: str):
    # TODO: Implement actual AI categorisation
    logger.info(f"Categorizing service for description: {description}")
    return {"status": "success", "category": "unknown"}
