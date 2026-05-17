from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from app.models.worker import WorkerProfile, WorkerStatus


class ProviderMatchingAgent:
    def match(
        self,
        db: Session,
        service_category: str,
        skills_required: list[str],
        user_requirements: dict[str, Any],
    ) -> list[dict[str, Any]]:
        workers = (
            db.query(WorkerProfile)
            .join(WorkerProfile.user)
            .filter(
                WorkerProfile.service_category == service_category,
                WorkerProfile.verification_status == WorkerStatus.APPROVED,
                WorkerProfile.is_available.is_(True),
            )
            .all()
        )

        matches: list[dict[str, Any]] = []
        required_skills = {s.strip().lower() for s in skills_required if s and s.strip()}

        for worker in workers:
            skill_overlap = 0.0
            if required_skills:
                worker_skills = {s.strip().lower() for s in (worker.skills or []) if isinstance(s, str)}
                skill_overlap = len(required_skills.intersection(worker_skills)) / len(required_skills)

            score = 0.0
            score += min(worker.average_rating / 5.0, 1.0) * 40
            score += min(worker.experience_years / 15.0, 1.0) * 20
            score += min(worker.total_jobs_completed / 300.0, 1.0) * 15
            score += skill_overlap * 20
            score += 5 if worker.emergency_available and user_requirements.get("urgency") == "high" else 0

            matches.append(
                {
                    "worker_id": worker.id,
                    "worker_name": worker.user.full_name,
                    "rating": worker.average_rating,
                    "experience_years": worker.experience_years,
                    "base_charge_per_hour": worker.base_charge_per_hour,
                    "skills": worker.skills or [],
                    "match_score": round(score, 2),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        return sorted(matches, key=lambda item: item["match_score"], reverse=True)

