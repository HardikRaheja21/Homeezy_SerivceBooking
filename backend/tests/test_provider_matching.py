from app.agents.provider_recommendation_agent import ProviderMatchingAgent
from app.models.user import User, UserRole, AccountStatus
from app.models.worker import WorkerProfile, WorkerStatus


def _create_worker(db_session, *, name, email, phone, rating, available, price, lat, lng):
    user = User(
        full_name=name,
        email=email,
        phone=phone,
        password_hash="x",
        role=UserRole.WORKER,
        account_status=AccountStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()

    profile = WorkerProfile(
        id=user.id,
        service_category="Plumber",
        skills=["Pipe repair"],
        experience_years=5,
        verification_status=WorkerStatus.APPROVED,
        working_radius_km=15,
        base_charge_per_hour=price,
        average_rating=rating,
        is_available=available,
        current_latitude=lat,
        current_longitude=lng,
    )
    db_session.add(profile)
    db_session.commit()
    return user.id


def test_provider_matching_prefers_near_high_rated_available_reasonable_price(db_session):
    best_id = _create_worker(
        db_session,
        name="Best Worker",
        email="best.worker@example.com",
        phone="+15550000011",
        rating=4.8,
        available=True,
        price=350,
        lat=28.6139,
        lng=77.2090,
    )

    _create_worker(
        db_session,
        name="Far Expensive",
        email="far.worker@example.com",
        phone="+15550000012",
        rating=4.7,
        available=True,
        price=900,
        lat=28.9000,
        lng=77.5000,
    )

    _create_worker(
        db_session,
        name="Offline Worker",
        email="offline.worker@example.com",
        phone="+15550000013",
        rating=4.9,
        available=False,
        price=300,
        lat=28.6145,
        lng=77.2085,
    )

    agent = ProviderMatchingAgent()
    result = agent.recommend(
        db=db_session,
        service_category="Plumber",
        customer_lat=28.6139,
        customer_lng=77.2090,
    )

    assert len(result) >= 1
    assert result[0]["worker_id"] == best_id
    assert result[0]["is_available"] is True
