# tests/test_complaints.py
"""
Integration tests for the Complaints API.

Covers:
- Customer raises a complaint
- Duplicate complaint prevention
- Customer lists their complaints
- Unauthorized access rejection
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock


FUTURE_DATE = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()


@pytest.fixture(autouse=True)
def mock_ai_and_notify(monkeypatch):
    from app.api.v1 import bookings as bookings_module
    bookings_module.ai_service.estimate_price = AsyncMock(return_value={"amount": 500.0, "confidence": 0.8})
    bookings_module.ai_service.recommend_workers = AsyncMock(return_value=[])
    bookings_module.ai_service.detect_fraud = AsyncMock(return_value=0.02)
    bookings_module.notification_service.send_booking_request = AsyncMock(return_value=None)
    bookings_module.notification_service.send_booking_accepted = AsyncMock(return_value=None)


@pytest.fixture()
def booking_id(client, customer_headers):
    """Create a booking and return its ID."""
    resp = client.post(
        "/api/v1/bookings/create",
        json={
            "service_category": "Cleaning",
            "service_description": "Full house deep clean",
            "skills_required": ["Deep cleaning"],
            "service_address": {"address": "B-5", "city": "Mumbai", "pincode": "400001"},
            "preferred_date": FUTURE_DATE,
            "preferred_time_slot": "09:00-11:00",
            "estimated_duration_hours": 3.0,
        },
        headers=customer_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["booking_id"]


class TestRaiseComplaint:
    def test_raise_complaint_success(self, client, customer_headers, booking_id):
        resp = client.post(
            "/api/v1/complaints/",
            json={
                "booking_id": booking_id,
                "complaint_type": "service_quality",
                "description": "The cleaner left the house in a worse state than before.",
            },
            headers=customer_headers,
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["complaint_id"]
        assert body["status"] == "open"

    def test_raise_duplicate_complaint_rejected(self, client, customer_headers, booking_id):
        payload = {
            "booking_id": booking_id,
            "complaint_type": "no_show",
            "description": "The worker never showed up to the appointment.",
        }
        client.post("/api/v1/complaints/", json=payload, headers=customer_headers)
        resp = client.post("/api/v1/complaints/", json=payload, headers=customer_headers)
        assert resp.status_code == 409

    def test_raise_complaint_wrong_booking(self, client, customer_headers):
        resp = client.post(
            "/api/v1/complaints/",
            json={
                "booking_id": "nonexistent-booking-id",
                "complaint_type": "payment_issue",
                "description": "I was charged twice for the same booking.",
            },
            headers=customer_headers,
        )
        assert resp.status_code == 404

    def test_raise_complaint_requires_auth(self, client, booking_id):
        resp = client.post(
            "/api/v1/complaints/",
            json={
                "booking_id": booking_id,
                "complaint_type": "damage",
                "description": "The worker damaged my furniture during the job.",
            },
        )
        assert resp.status_code == 403


class TestListComplaints:
    def test_list_my_complaints(self, client, customer_headers, booking_id):
        client.post(
            "/api/v1/complaints/",
            json={
                "booking_id": booking_id,
                "complaint_type": "overcharging",
                "description": "The final bill was much higher than the quoted estimate.",
            },
            headers=customer_headers,
        )
        resp = client.get("/api/v1/complaints/my-complaints", headers=customer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1
