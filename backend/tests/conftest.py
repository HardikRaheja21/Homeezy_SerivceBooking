# tests/conftest.py
"""
Pytest fixtures for Homeezy integration tests.

Uses SQLite in-memory via the full FastAPI app with get_db overridden.
All tests run in isolation — tables are created fresh per session.
"""

import os
import pytest

# ── Set env vars BEFORE any app imports ──────────────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///./homeezy_test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_USER", "test@homeezy.local")
os.environ.setdefault("SMTP_PASSWORD", "test")
os.environ.setdefault("SMTP_FROM", "noreply@homeezy.local")
os.environ.setdefault("ADMIN_EMAIL", "admin@homeezy.local")
os.environ.setdefault("ADMIN_PASSWORD", "Admin@1234")
os.environ.setdefault("DEV_MODE", "True")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
import app.models  # noqa: F401 — register all ORM models


# ── DB engine (SQLite, session-scoped) ────────────────────────────────────────

TEST_DB_URL = "sqlite:///./homeezy_test.db"

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def db_session(engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


# ── Full-app TestClient ───────────────────────────────────────────────────────

@pytest.fixture()
def client(db_session):
    """
    TestClient wired to the full FastAPI app with get_db overridden
    to use the test SQLite session.
    """
    import main as app_module

    def override_get_db():
        yield db_session

    app_module.app.dependency_overrides[get_db] = override_get_db

    # Starlette 0.27 TestClient — positional app arg, no raise_server_exceptions kwarg
    with TestClient(app_module.app) as c:
        yield c

    app_module.app.dependency_overrides.clear()



# ── Auth helpers ──────────────────────────────────────────────────────────────

CUSTOMER_PAYLOAD = {
    "full_name": "Test Customer",
    "email": "customer@testmail.com",
    "phone": "+911234567890",
    "password": "Customer@123",
    "city": "Delhi",
    "area": "Connaught Place",
    "pincode": "110001",
}

WORKER_PAYLOAD = {
    "full_name": "Test Worker",
    "email": "worker@test.homeezy",
    "phone": "+911234567891",
    "password": "Worker@123",
    "city": "Delhi",
    "area": "Lajpat Nagar",
    "pincode": "110024",
    "service_category": "Plumbing",
    "skills": ["Pipe repair", "Leak fixing"],
    "experience_years": 3,
    "government_id_type": "Aadhar",
    "government_id_number": "123456789012",
    "working_radius_km": 10,
    "base_charge_per_hour": 350.0,
    "emergency_available": True,
    "bank_name": "SBI",
    "account_number": "12345678901",
    "ifsc_code": "SBIN0001234",
    "emergency_contact_name": "Jane Worker",
    "emergency_contact_phone": "+911234567899",
}


@pytest.fixture()
def customer_token(client):
    """Register + login a customer, return access token."""
    client.post("/api/v1/auth/register/customer", json=CUSTOMER_PAYLOAD)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": CUSTOMER_PAYLOAD["email"], "password": CUSTOMER_PAYLOAD["password"]},
    )
    return resp.json().get("access_token", "")


@pytest.fixture()
def customer_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}


@pytest.fixture()
def worker_token(client):
    """Register a worker (stays PENDING — for testing rejection paths)."""
    client.post("/api/v1/auth/register/worker", json=WORKER_PAYLOAD)
    # Workers cannot login until admin approves — return empty token for pending tests
    return ""
