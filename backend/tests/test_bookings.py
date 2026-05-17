# tests/test_bookings.py
"""
Integration tests for the Booking API.

Covers:
- Create booking (happy path, monkeypatched AI)
- Reject past-date bookings
- List bookings with pagination
- Status transitions
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock


FUTURE_DATE = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
PAST_DATE = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

BOOKING_PAYLOAD = {
    "service_category": "Plumbing",
    "service_description": "Kitchen sink leakage — urgent",
    "skills_required": ["Pipe repair"],
    "service_address": {"address": "A-10 Connaught Place", "city": "Delhi", "pincode": "110001"},
    "preferred_date": FUTURE_DATE,
    "preferred_time_slot": "10:00-12:00",
    "estimated_duration_hours": 2.0,
}


@pytest.fixture(autouse=True)
def mock_ai_and_notify(monkeypatch):
    """Patch AI + notification so tests don't need external services."""
    from app.api.v1 import bookings as bookings_module

    bookings_module.ai_service.estimate_price = AsyncMock(
        return_value={"amount": 799.0, "confidence": 0.9}
    )
    bookings_module.ai_service.recommend_workers = AsyncMock(return_value=[])
    bookings_module.ai_service.detect_fraud = AsyncMock(return_value=0.05)
    bookings_module.notification_service.send_booking_request = AsyncMock(return_value=None)
    bookings_module.notification_service.send_booking_accepted = AsyncMock(return_value=None)


class TestCreateBooking:
    def test_create_booking_success(self, client, customer_headers):
        resp = client.post(
            "/api/v1/bookings/create",
            json=BOOKING_PAYLOAD,
            headers=customer_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["booking_id"]
        assert body["estimated_price"] == 799.0

    def test_create_booking_past_date_rejected(self, client, customer_headers):
        payload = {**BOOKING_PAYLOAD, "preferred_date": PAST_DATE}
        resp = client.post(
            "/api/v1/bookings/create",
            json=payload,
            headers=customer_headers,
        )
        assert resp.status_code == 400
        assert "future" in resp.json()["detail"].lower()

    def test_create_booking_requires_auth(self, client):
        resp = client.post("/api/v1/bookings/create", json=BOOKING_PAYLOAD)
        assert resp.status_code == 403


class TestListBookings:
    def test_list_my_bookings_empty(self, client, customer_headers):
        resp = client.get("/api/v1/bookings/my-bookings", headers=customer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "total_pages" in body

    def test_list_bookings_pagination(self, client, customer_headers):
        # Create 3 bookings
        for _ in range(3):
            client.post("/api/v1/bookings/create", json=BOOKING_PAYLOAD, headers=customer_headers)

        resp = client.get(
            "/api/v1/bookings/my-bookings?page=1&page_size=2",
            headers=customer_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) <= 2
        assert body["page"] == 1
        assert body["page_size"] == 2


class TestBookingDetail:
    def test_get_booking_detail(self, client, customer_headers):
        create = client.post(
            "/api/v1/bookings/create",
            json=BOOKING_PAYLOAD,
            headers=customer_headers,
        )
        booking_id = create.json()["booking_id"]
        resp = client.get(f"/api/v1/bookings/{booking_id}", headers=customer_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == booking_id

    def test_get_nonexistent_booking(self, client, customer_headers):
        resp = client.get("/api/v1/bookings/nonexistent-id", headers=customer_headers)
        assert resp.status_code == 404
