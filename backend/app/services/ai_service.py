from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.agents.orchestrator import AgentOrchestrator
from app.models.booking import Booking


class AIService:
    def __init__(self) -> None:
        self.orchestrator = AgentOrchestrator()

    async def estimate_price(self, db: Session, service_category: str, skills: list, duration: float, location: dict):
        recommendation = self.orchestrator.recommend(
            db=db,
            payload={
                "service_category": service_category,
                "skills_required": skills,
                "estimated_duration_hours": duration,
                "service_address": location,
                "base_price": 300,
                "demand_index": 1.0,
            },
        )
        return {
            "amount": recommendation["pricing"]["final_amount"],
            "confidence": recommendation["pricing"]["confidence"],
            "breakdown": recommendation["pricing"],
        }

    async def recommend_workers(
        self,
        service_category: str,
        skills_required: list,
        location: dict,
        preferred_date: datetime,
        db: Session,
    ):
        _ = location
        _ = preferred_date
        recommendation = self.orchestrator.recommend(
            db=db,
            payload={"service_category": service_category, "skills_required": skills_required},
        )
        return [
            {
                "worker_id": item["worker_id"],
                "worker_name": item["worker_name"],
                "rating": item["rating"],
                "total_jobs": 0,
                "base_charge": item["base_charge_per_hour"],
                "experience_years": item["experience_years"],
                "skills": item["skills"],
                "score": item["match_score"],
                "profile_photo": None,
            }
            for item in recommendation["matched_workers"]
        ]

    async def detect_fraud(self, user_id: str, booking_data: dict, db: Session):
        fraud_score = 0.0
        recent_bookings = (
            db.query(Booking)
            .filter(Booking.customer_id == user_id, Booking.requested_at >= datetime.now(timezone.utc) - timedelta(hours=1))
            .count()
        )
        if recent_bookings > 5:
            fraud_score += 0.4
        estimated_price = float(booking_data.get("estimated_price", 0) or 0)
        if estimated_price > 10000:
            fraud_score += 0.2
        return min(fraud_score, 1.0)

    async def analyze_review_sentiment(self, review_text: str):
        positive_words = ["good", "great", "excellent", "professional", "punctual", "skilled"]
        negative_words = ["bad", "poor", "late", "rude", "unprofessional", "incompetent"]
        text = review_text.lower()
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        total = pos_count + neg_count
        if total == 0:
            score, label = 0.0, "neutral"
        else:
            score = (pos_count - neg_count) / total
            label = "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"
        return {
            "sentiment_score": score,
            "sentiment_label": label,
            "key_phrases": [w for w in positive_words + negative_words if w in text],
        }
