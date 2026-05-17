from typing import Any


class UserRequirementAgent:
    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        notes = (payload.get("service_description") or "").lower()
        price_sensitivity = "normal"
        urgency = "normal"

        if any(word in notes for word in ["cheap", "budget", "lowest", "affordable"]):
            price_sensitivity = "high"
        elif any(word in notes for word in ["premium", "expert", "best"]):
            price_sensitivity = "low"

        if any(word in notes for word in ["urgent", "asap", "immediately", "now"]):
            urgency = "high"

        return {
            "urgency": urgency,
            "price_sensitivity": price_sensitivity,
            "distance_preference_km": float(payload.get("distance_preference_km", 10)),
        }

