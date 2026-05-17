from datetime import datetime, timezone
from typing import Any


class DynamicPricingAgent:
    def price(
        self,
        base_price: float,
        duration_hours: float,
        user_requirements: dict[str, Any],
        demand_index: float = 1.0,
    ) -> dict[str, Any]:
        amount = base_price * duration_hours
        multiplier = 1.0
        now = datetime.now(timezone.utc)

        if now.hour >= 18 and now.hour <= 22:
            multiplier *= 1.15
        if now.weekday() >= 5:
            multiplier *= 1.1
        if user_requirements.get("urgency") == "high":
            multiplier *= 1.2

        demand_index = max(0.5, min(demand_index, 2.0))
        multiplier *= demand_index
        final_amount = round(amount * multiplier, 2)

        return {
            "base_amount": round(amount, 2),
            "surge_multiplier": round(multiplier, 2),
            "final_amount": final_amount,
            "confidence": 0.84,
        }

