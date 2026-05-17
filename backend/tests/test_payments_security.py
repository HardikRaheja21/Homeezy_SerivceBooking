import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.config import settings

def test_razorpay_webhook_invalid_signature(client: TestClient):
    # Webhook payload
    payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_12345",
                    "order_id": "order_12345",
                    "status": "captured"
                }
            }
        }
    }
    
    # Headers with an invalid signature
    headers = {
        "X-Razorpay-Signature": "invalid_signature_string"
    }
    
    resp = client.post("/api/v1/payments/webhook", json=payload, headers=headers)
    # The new secure handler returns 400 Bad Request on signature verification failure
    assert resp.status_code == 400
    assert "Invalid signature" in resp.json()["detail"]

def test_razorpay_webhook_missing_signature(client: TestClient):
    payload = {
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_12345"}}}
    }
    
    resp = client.post("/api/v1/payments/webhook", json=payload)
    # The new handler returns 400 if the signature header is completely missing
    assert resp.status_code == 400
    assert "Invalid signature" in resp.json()["detail"]
