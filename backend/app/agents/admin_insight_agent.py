from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.worker import WorkerProfile
from app.models.booking import Booking, BookingStatus


class AdminInsightAgent:
    def generate(self, db: Session) -> dict:
        low_rated_workers = (
            db.query(WorkerProfile)
            .filter(WorkerProfile.total_reviews >= 5, WorkerProfile.average_rating < 3.0)
            .order_by(WorkerProfile.average_rating.asc())
            .limit(20)
            .all()
        )

        suspicious_bookings = (
            db.query(Booking)
            .filter(Booking.fraud_detection_score >= 0.7)
            .order_by(Booking.fraud_detection_score.desc())
            .limit(50)
            .all()
        )

        high_cancellation_workers = (
            db.query(WorkerProfile)
            .filter(WorkerProfile.cancellation_rate > 0.25)
            .order_by(WorkerProfile.cancellation_rate.desc())
            .limit(20)
            .all()
        )

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        completed_last_week = (
            db.query(Booking)
            .filter(Booking.status == BookingStatus.COMPLETED, Booking.completed_at >= week_ago)
            .count()
        )

        return {
            "completed_last_7_days": completed_last_week,
            "low_rated_providers": [
                {"worker_id": worker.id, "rating": worker.average_rating, "reviews": worker.total_reviews}
                for worker in low_rated_workers
            ],
            "suspicious_bookings": [
                {"booking_id": booking.id, "fraud_score": booking.fraud_detection_score}
                for booking in suspicious_bookings
            ],
            "high_cancellation_providers": [
                {"worker_id": worker.id, "cancellation_rate": worker.cancellation_rate}
                for worker in high_cancellation_workers
            ],
        }

