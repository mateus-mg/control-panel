"""Tests for auth API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAuthAPI:
    """Test auth API endpoints."""

    def test_login_missing_body(self):
        """Test login without credentials."""
        response = client.post("/api/auth/login")
        assert response.status_code == 422  # Validation error

    def test_login_wrong_credentials(self):
        """Test login with wrong credentials."""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"}
        )
        assert response.status_code == 401

    def test_get_me_without_token(self):
        """Test /me endpoint without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 403  # No auth header

    def test_logout_without_token(self):
        """Test logout without token."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 403