from datetime import datetime, timedelta
from app.models.user import User, UserRole, AccountStatus
from app.models.booking import Booking


async def _estimate_price(*args, **kwargs):
    return {"amount": 799.0, "confidence": 0.9}


async def _recommend_workers(*args, **kwargs):
    return [{"worker_id": "worker-1", "worker_name": "Worker One", "score": 91.0}]


async def _detect_fraud(*args, **kwargs):
    return 0.1


async def _noop_notify(*args, **kwargs):
    return None


def test_booking_create_success(booking_client, db_session, monkeypatch):
    from app.api.v1 import bookings

    customer = User(
        full_name="Booking Customer",
        email="booking.customer@example.com",
        phone="+15550000021",
        password_hash="x",
        role=UserRole.CUSTOMER,
        account_status=AccountStatus.ACTIVE,
    )
    db_session.add(customer)
    db_session.commit()

    booking_client.app.state.set_current_user(customer)

    monkeypatch.setattr(bookings.ai_service, "estimate_price", _estimate_price)
    monkeypatch.setattr(bookings.ai_service, "recommend_workers", _recommend_workers)
    monkeypatch.setattr(bookings.ai_service, "detect_fraud", _detect_fraud)
    monkeypatch.setattr(bookings.notification_service, "send_booking_request", _noop_notify)

    payload = {
        "service_category": "Plumber",
        "service_description": "Kitchen sink leakage, urgent",
        "skills_required": ["Pipe repair"],
        "service_address": {"address": "A-10", "city": "Delhi", "pincode": "110001", "lat": 28.61, "lng": 77.21},
        "preferred_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "preferred_time_slot": "10:00-12:00",
        "estimated_duration_hours": 2,
        "special_instructions": "Call before arrival",
        "materials_required": ["Pipe seal tape"],
    }

    response = booking_client.post("/api/v1/bookings/create", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body.get("booking_id")
    saved = db_session.query(Booking).filter(Booking.id == body["booking_id"]).first()
    assert saved is not None
    assert float(saved.estimated_price) == 799.0
