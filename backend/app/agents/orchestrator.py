from typing import Any
from sqlalchemy.orm import Session
from app.agents.user_requirement_agent import UserRequirementAgent
from app.agents.provider_matching_agent import ProviderMatchingAgent
from app.agents.dynamic_pricing_agent import DynamicPricingAgent
from app.agents.admin_insight_agent import AdminInsightAgent
from app.models.service import ServiceCategory


class AgentOrchestrator:
    def __init__(self) -> None:
        self.requirement_agent = UserRequirementAgent()
        self.matching_agent = ProviderMatchingAgent()
        self.pricing_agent = DynamicPricingAgent()
        self.admin_agent = AdminInsightAgent()

    def recommend(self, db: Session, payload: dict[str, Any]) -> dict[str, Any]:
        requirements = self.requirement_agent.analyze(payload)

        service_category = payload.get("service_category")
        service = db.query(ServiceCategory).filter(ServiceCategory.name == service_category).first()
        if not service:
            service = db.query(ServiceCategory).filter(ServiceCategory.slug == service_category).first()

        base_price = service.base_price if service else float(payload.get("base_price", 300))
        duration_hours = float(payload.get("estimated_duration_hours", 2.0))
        demand_index = float(payload.get("demand_index", 1.0))

        matched_workers = self.matching_agent.match(
            db=db,
            service_category=service_category,
            skills_required=payload.get("skills_required", []),
            user_requirements=requirements,
        )
        pricing = self.pricing_agent.price(
            base_price=base_price,
            duration_hours=duration_hours,
            user_requirements=requirements,
            demand_index=demand_index,
        )
        return {
            "requirements": requirements,
            "pricing": pricing,
            "matched_workers": matched_workers,
        }

    def admin_insights(self, db: Session) -> dict[str, Any]:
        return self.admin_agent.generate(db)

