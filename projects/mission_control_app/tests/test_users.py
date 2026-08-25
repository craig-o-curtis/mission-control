"""Tests for user self-service endpoints."""

from fastapi.testclient import TestClient


class TestGetCurrentUserProfile:
    def test_user_gets_own_profile(self, api_client: TestClient) -> None:
        """Authenticated user can read own profile."""
        # This works because the api_client fixture is set up with fake_user id 1
        # in file conftest.py
        response = api_client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["username"] == "testuser"
        assert "hashed_password" not in data

    def test_user_profile_excludes_password(self, api_client: TestClient) -> None:
        """User profile does not include hashed_password."""
        response = api_client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert "hashed_password" not in data


class TestUpdateCurrentUser:
    def test_user_updates_own_profile(self, api_client: TestClient) -> None:
        """Authenticated user can update own profile."""
        update_data = {"first_name": "Updated", "last_name": "User"}
        response = api_client.put("/users/me", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "User"
        # Confirm user is in db
        response = api_client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "User"

    def test_user_cannot_change_role(self, api_client: TestClient) -> None:
        """User cannot change their own role."""
        update_data = {"role": "admin"}
        response = api_client.put("/users/me", json=update_data)
        assert response.status_code == 403
        assert response.json()["detail"] == "Cannot change your own role"

    def test_user_cannot_change_role_via_other_fields(
        self, api_client: TestClient
    ) -> None:
        """User cannot sneak role change via other fields."""
        update_data = {"username": "newname", "role": "admin"}
        response = api_client.put("/users/me", json=update_data)
        assert response.status_code == 403

    def test_user_can_update_own_phone_number(self, api_client: TestClient) -> None:
        """Authenticated user can update own phone_number."""
        update_data = {"phone_number": "555-1234"}
        response = api_client.put("/users/me", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == "555-1234"


class TestUpdateCurrentUserPhone:
    def test_user_updates_own_phone_number(self, api_client: TestClient) -> None:
        """PATCH /users/me/phone-number updates the user's phone number."""
        response = api_client.patch(
            "/users/me/phone-number", json={"phone_number": "555-4321"}
        )
        assert response.status_code == 204
        assert response.content == b""
        # Confirm is in db
        profile = api_client.get("/users/me")
        assert profile.status_code == 200
        assert profile.json()["phone_number"] == "555-4321"

    def test_user_update_phone_number_missing(self, api_client: TestClient) -> None:
        """PATCH /users/me/phone-number without phone_number returns 422."""
        response = api_client.patch("/users/me/phone-number", json={})
        assert response.status_code == 422

    def test_user_update_phone_number_too_short(self, api_client: TestClient) -> None:
        """PATCH /users/me/phone-number with empty phone_number returns 422."""
        response = api_client.patch("/users/me/phone-number", json={"phone_number": ""})
        assert response.status_code == 422

    def test_user_update_phone_number_too_long(self, api_client: TestClient) -> None:
        """PATCH /users/me/phone-number exceeding max_length returns 422."""
        response = api_client.patch(
            "/users/me/phone-number", json={"phone_number": "1" * 21}
        )
        assert response.status_code == 422


class TestDeleteCurrentUser:
    def test_user_deletes_own_account(self, api_client: TestClient) -> None:
        """Authenticated user can delete own account."""
        response = api_client.delete("/users/me")
        assert response.status_code == 204
        # b"" is the empty body for 204 No Content
        # b stands for bytes, which is what response.content returns
        assert response.content == b""


class TestAdminSelfService:
    def test_admin_can_read_own_profile(self, admin_client: TestClient) -> None:
        """Admin can read own profile via /users/me."""
        response = admin_client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 2
        assert data["username"] == "adminuser"
        assert data["role"] == "admin"

    def test_admin_can_update_own_profile(self, admin_client: TestClient) -> None:
        """Admin can update own profile via /users/me."""
        update_data = {"first_name": "AdminUpdated"}
        response = admin_client.put("/users/me", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "AdminUpdated"
        # Confirm updated profile
        profile = admin_client.get("/users/me")
        assert profile.status_code == 200
        assert profile.json()["first_name"] == "AdminUpdated"

    def test_admin_can_delete_own_account(self, admin_client: TestClient) -> None:
        """Admin can delete own account via /users/me."""
        response = admin_client.delete("/users/me")
        assert response.status_code == 204
        assert response.content == b""


class TestAdminUserUpdate:
    def test_admin_can_update_user_phone_number(self, admin_client: TestClient) -> None:
        """Admin can update another user's phone_number."""
        # Create a user first
        new_user = {
            "username": "phonetest",
            "email": "phonetest@example.com",
            "first_name": "Phone",
            "last_name": "Test",
            "phone_number": "555-0007",
            "password": "password123",
        }
        create_resp = admin_client.post("/users", json=new_user)
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]

        # Update phone_number
        update_data = {"phone_number": "555-9999"}
        response = admin_client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == "555-9999"

        # Confirm updated phone_number
        profile = admin_client.get(f"/users/{user_id}")
        assert profile.status_code == 200
        assert profile.json()["phone_number"] == "555-9999"


class TestPasswordHashing:
    def test_user_password_hashed_on_update(self, api_client: TestClient) -> None:
        """PUT /users/me with password stores hashed value, not plaintext."""
        update_data = {"password": "newpassword123"}
        response = api_client.put("/users/me", json=update_data)
        assert response.status_code == 200
        # Password should not be in response (ReadUserPublic excludes it)
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data

    def test_admin_password_hashed_on_update(self, admin_client: TestClient) -> None:
        """Admin PUT /users/{id} with password stores hashed value."""
        # Create a user first
        new_user = {
            "username": "pwtest",
            "email": "pwtest@example.com",
            "first_name": "PW",
            "last_name": "Test",
            "phone_number": "555-0008",
            "password": "password123",
        }
        create_resp = admin_client.post("/users", json=new_user)
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]

        # Update password
        update_data = {"password": "newpassword456"}
        response = admin_client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == 200
        # Password should not be in response
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data

    def test_user_update_invalid_data(self, api_client: TestClient) -> None:
        """PUT /users/me with invalid data returns 422."""
        update_data = {"username": "ab"}  # min_length=3
        response = api_client.put("/users/me", json=update_data)
        assert response.status_code == 422

    def test_admin_update_user_invalid_data(self, admin_client: TestClient) -> None:
        """Admin PUT /users/{id} with invalid data returns 422."""
        update_data = {"username": "ab"}  # min_length=3
        response = admin_client.put("/users/2", json=update_data)
        assert response.status_code == 422


class TestUpdatePassword:
    def test_password_change_success(self, api_client: TestClient) -> None:
        """PATCH /users/me/password with correct current password returns 204."""
        response = api_client.patch(
            "/users/me/password",
            json={
                "current_password": "fakepass123",
                "new_password": "brandnewpass123",
            },
        )
        assert response.status_code == 204
        assert response.content == b""

    def test_password_change_wrong_current(self, api_client: TestClient) -> None:
        """PATCH /users/me/password with wrong current password returns 401."""
        response = api_client.patch(
            "/users/me/password",
            json={
                "current_password": "wrongpassword",
                "new_password": "brandnewpass123",
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Current password is incorrect"

    def test_password_change_same_password(self, api_client: TestClient) -> None:
        """PATCH /users/me/password with same password returns 400."""
        response = api_client.patch(
            "/users/me/password",
            json={
                "current_password": "fakepass123",
                "new_password": "fakepass123",
            },
        )
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "New password must differ from current password"
        )

    def test_password_change_missing_new(self, api_client: TestClient) -> None:
        """PATCH /users/me/password with short new password returns 422."""
        response = api_client.patch(
            "/users/me/password",
            json={
                "current_password": "fakepass123",
                "new_password": "short",
            },
        )
        assert response.status_code == 422

    def test_password_change_missing_current(self, api_client: TestClient) -> None:
        """PATCH /users/me/password with short current password returns 422."""
        response = api_client.patch(
            "/users/me/password",
            json={
                "current_password": "short",
                "new_password": "brandnewpass123",
            },
        )
        assert response.status_code == 422
