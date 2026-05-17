import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app
from app.core.redis import redis_client

@pytest.fixture
def mock_redis():
    with patch("app.api.v1.auth.redis_client", new_callable=AsyncMock) as mock:
        yield mock

def test_otp_brute_force_lockout(client: TestClient, mock_redis):
    # Setup mock to return a valid OTP string "123456" for the key, and varying attempts
    
    # We want to simulate 5 failed attempts
    mock_redis.get.side_effect = [
        "123456", "0", # attempt 1
        "123456", "1", # attempt 2
        "123456", "2", # attempt 3
        "123456", "3", # attempt 4
        "123456", "4", # attempt 5
        "123456", "5", # attempt 6 (lockout)
    ]
    
    payload = {
        "identifier": "customer@example.com",
        "type": "email",
        "otp": "000000" # wrong OTP
    }
    
    # First 5 attempts should return 400 Bad Request
    for i in range(5):
        resp = client.post("/api/v1/auth/verify-otp", json=payload)
        assert resp.status_code == 400
        assert "Incorrect OTP" in resp.json()["detail"]
        
    # The 6th attempt should return 429 Too Many Requests
    resp = client.post("/api/v1/auth/verify-otp", json=payload)
    assert resp.status_code == 429
    assert "Too many failed attempts" in resp.json()["detail"]
