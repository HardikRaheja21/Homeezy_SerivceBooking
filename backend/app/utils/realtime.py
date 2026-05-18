"""WebSocket broadcast helpers for live dashboard updates."""
import logging
from app.websockets.manager import manager

logger = logging.getLogger(__name__)


async def notify_booking_event(
    booking_id: str,
    event_type: str,
    message: str,
    customer_id: str | None = None,
    worker_id: str | None = None,
):
    payload = {
        "type": event_type,
        "message": message,
        "booking_id": booking_id,
    }
    try:
        await manager.broadcast_to_booking(payload, booking_id)
        if customer_id:
            await manager.send_personal_message(payload, customer_id)
        if worker_id:
            await manager.send_personal_message(payload, worker_id)
        await manager.broadcast_to_role(
            {"type": event_type, "message": message, "booking_id": booking_id},
            "admin",
        )
    except Exception:
        logger.exception("Failed to broadcast booking event %s", event_type)
