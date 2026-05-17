from app.core.redis import redis_client
from datetime import datetime, timezone

class NotificationService:
    async def send_booking_request(self, worker_id: str, booking_id: str, service_category: str):
        """Send notification to worker about new booking"""
        # In production: Push notification, SMS, Email
        notification_key = f"notification:worker:{worker_id}"
        notification = {
            "type": "booking_request",
            "booking_id": booking_id,
            "service_category": service_category,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await redis_client.set(notification_key, str(notification), ex=3600)
        print(f"Notification sent to worker {worker_id} for booking {booking_id}")
    
    async def send_booking_accepted(self, customer_id: str, worker_name: str, booking_id: str):
        """Notify customer that booking was accepted"""
        notification_key = f"notification:customer:{customer_id}"
        notification = {
            "type": "booking_accepted",
            "worker_name": worker_name,
            "booking_id": booking_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await redis_client.set(notification_key, str(notification), ex=3600)
        print(f"Notification sent to customer {customer_id}: Booking accepted by {worker_name}")
