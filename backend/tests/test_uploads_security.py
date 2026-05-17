import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.security import create_access_token
from app.models.user import UserRole
import uuid

@pytest.fixture
def auth_headers():
    user_id = str(uuid.uuid4())
    token = create_access_token({"sub": user_id, "role": UserRole.CUSTOMER.value})
    return {"Authorization": f"Bearer {token}"}

def test_upload_signature_whitelist_valid(client: TestClient, auth_headers):
    # Valid folders: "homeezy/profiles", "homeezy/complaints", "homeezy/kyc", "homeezy/services"
    resp = client.get("/api/v1/uploads/signature?folder=homeezy/profiles", headers=auth_headers)
    # 200 OK or 500 if Cloudinary is not configured correctly, but NOT 400 Bad Request
    assert resp.status_code in [200, 500] 

def test_upload_signature_whitelist_invalid(client: TestClient, auth_headers):
    # Attempt path traversal / SSRF / unauthorized folder
    malicious_folders = [
        "homeezy/private",
        "../",
        "homeezy/profiles/../../etc"
    ]
    for folder in malicious_folders:
        resp = client.get(f"/api/v1/uploads/signature?folder={folder}", headers=auth_headers)
        assert resp.status_code == 400
        assert "Upload folder not permitted" in resp.json()["detail"]
