# tests/test_auth.py
"""
Integration tests for the Authentication API.

Covers:
- Customer registration (DEV_MODE auto-activation)
- Duplicate registration rejection
- Login success
- Login failure (wrong password)
- Token refresh
- Invalid token rejection
"""

import pytest


class TestCustomerRegistration:
    def test_register_success(self, client):
        resp = client.post(
            "/api/v1/auth/register/customer",
            json={
                "full_name": "Alice Reg",
                "email": "alice.reg@gmail.com",
                "phone": "+911111111111",
                "password": "Alice@123",
                "city": "Mumbai",
                "area": "Bandra",
                "pincode": "400050",
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["user_id"]
        assert body["email"] == "alice.reg@gmail.com"

    def test_register_duplicate_email(self, client):
        payload = {
            "full_name": "Dup User",
            "email": "dup@gmail.com",
            "phone": "+911111111112",
            "password": "Dup@12345",
            "city": "Delhi",
            "area": "CP",
            "pincode": "110001",
        }
        client.post("/api/v1/auth/register/customer", json=payload)
        resp = client.post("/api/v1/auth/register/customer", json={**payload, "phone": "+911111111113"})
        assert resp.status_code == 409

    def test_register_weak_password(self, client):
        resp = client.post(
            "/api/v1/auth/register/customer",
            json={
                "full_name": "Weak Pass",
                "email": "weak@gmail.com",
                "phone": "+911111111114",
                "password": "weak",
                "city": "Delhi",
                "area": "CP",
                "pincode": "110001",
            },
        )
        # 400 if app validates password strength, 422 if Pydantic catches it
        assert resp.status_code in (400, 422)


class TestLogin:
    EMAIL = "login.test@gmail.com"
    PASSWORD = "Login@123"

    @pytest.fixture(autouse=True)
    def register(self, client):
        client.post(
            "/api/v1/auth/register/customer",
            json={
                "full_name": "Login Test",
                "email": self.EMAIL,
                "phone": "+912222222221",
                "password": self.PASSWORD,
                "city": "Pune",
                "area": "Koregaon",
                "pincode": "411001",
            },
        )

    def test_login_success_returns_tokens(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": self.EMAIL, "password": self.PASSWORD},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["user"]["email"] == self.EMAIL
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": self.EMAIL, "password": "Wrong@999"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@gmail.com", "password": "Pass@123"},
        )
        assert resp.status_code == 401


class TestProtectedEndpoints:
    def test_get_me_with_valid_token(self, client, customer_headers):
        resp = client.get("/api/v1/users/me", headers=customer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "email" in body
        assert "role" in body

    def test_get_me_without_token(self, client):
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 403

    def test_get_me_with_bad_token(self, client):
        resp = client.get("/api/v1/users/me", headers={"Authorization": "Bearer bad-token"})
        assert resp.status_code in (401, 403)


class TestTokenRefresh:
    def test_refresh_token(self, client):
        client.post(
            "/api/v1/auth/register/customer",
            json={
                "full_name": "Refresh User",
                "email": "refresh@gmail.com",
                "phone": "+913333333331",
                "password": "Refresh@123",
                "city": "Hyderabad",
                "area": "Hitech",
                "pincode": "500081",
            },
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@gmail.com", "password": "Refresh@123"},
        )
        refresh_token = login.json()["refresh_token"]
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert resp.json()["access_token"]
