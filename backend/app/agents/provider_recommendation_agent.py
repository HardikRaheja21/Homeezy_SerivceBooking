from math import asin, cos, radians, sin, sqrt
from sqlalchemy.orm import Session
from app.models.worker import WorkerProfile, WorkerStatus


class ProviderMatchingAgent:
    """Rule-based provider matcher, designed for future LLM plug-in orchestration."""

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return radius * c

    def _normalize(self, value: float, min_v: float, max_v: float) -> float:
        if max_v <= min_v:
            return 0.0
        bounded = max(min(value, max_v), min_v)
        return (bounded - min_v) / (max_v - min_v)

    def recommend(
        self,
        db: Session,
        service_category: str,
        customer_lat: float,
        customer_lng: float,
        max_candidates: int = 20,
    ) -> list[dict]:
        workers = (
            db.query(WorkerProfile)
            .join(WorkerProfile.user)
            .filter(
                WorkerProfile.service_category == service_category,
                WorkerProfile.verification_status == WorkerStatus.APPROVED,
            )
            .all()
        )

        scored: list[dict] = []
        for worker in workers:
            available_score = 1.0 if worker.is_available else 0.0

            distance_km = None
            distance_score = 0.2
            if worker.current_latitude is not None and worker.current_longitude is not None:
                distance_km = self._haversine_km(customer_lat, customer_lng, worker.current_latitude, worker.current_longitude)
                radius = max(float(worker.working_radius_km or 5), 1.0)
                distance_score = max(0.0, 1.0 - (distance_km / radius))

            rating_score = self._normalize(float(worker.average_rating or 0.0), 0.0, 5.0)
            price_score = 1.0 - self._normalize(float(worker.base_charge_per_hour or 0.0), 100.0, 2000.0)

            final_score = (
                distance_score * 0.35
                + rating_score * 0.30
                + available_score * 0.20
                + price_score * 0.15
            )

            scored.append(
                {
                    "worker_id": worker.id,
                    "worker_name": worker.user.full_name,
                    "distance_km": round(distance_km, 2) if distance_km is not None else None,
                    "rating": float(worker.average_rating or 0.0),
                    "is_available": bool(worker.is_available),
                    "price_per_hour": float(worker.base_charge_per_hour or 0.0),
                    "score": round(final_score, 4),
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:max_candidates]
