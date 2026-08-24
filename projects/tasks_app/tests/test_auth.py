"""Tests for auth endpoints."""

from fastapi.testclient import TestClient


class TestLogin:
    def test_login_valid_credentials(self, no_auth_client: TestClient) -> None:
        """Login with valid credentials returns 200 and a token."""
        response = no_auth_client.post(
            "/auth/token",
            data={"username": "authtest", "password": "fakepass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, no_auth_client: TestClient) -> None:
        """Login with wrong password returns 401."""
        response = no_auth_client.post(
            "/auth/token",
            data={"username": "authtest", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate user."

    def test_login_nonexistent_user(self, no_auth_client: TestClient) -> None:
        """Login with non-existent user returns 401."""
        response = no_auth_client.post(
            "/auth/token",
            data={"username": "nobody", "password": "fakepass123"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate user."

    def test_login_missing_fields(self, no_auth_client: TestClient) -> None:
        """Login with missing fields returns 422."""
        response = no_auth_client.post(
            "/auth/token",
            data={"username": "authtest"},
        )
        assert response.status_code == 422
