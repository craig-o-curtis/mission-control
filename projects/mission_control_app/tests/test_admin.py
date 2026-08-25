"""Tests for admin endpoints."""

from fastapi.testclient import TestClient


class TestAdminGetAllChecklists:
    def test_admin_gets_all_checklists(self, admin_client: TestClient) -> None:
        """Admin can retrieve all checklists."""
        response = admin_client.get("/admin/checklists")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_admin_gets_all_checklists_pagination(
        self, admin_client: TestClient
    ) -> None:
        """Admin can paginate through all checklists."""
        response = admin_client.get("/admin/checklists?skip=0&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_non_admin_cannot_get_all_checklists(self, api_client: TestClient) -> None:
        """Non-admin user gets 403 on admin checklists endpoint."""
        response = api_client.get("/admin/checklists")
        assert response.status_code == 403


class TestAdminGetChecklist:
    def test_admin_gets_checklist_by_id(self, admin_client: TestClient) -> None:
        """Admin can retrieve a single checklist by ID."""
        response = admin_client.get("/admin/checklists/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_admin_gets_checklist_not_found(self, admin_client: TestClient) -> None:
        """Admin gets 404 for non-existent checklist."""
        response = admin_client.get("/admin/checklists/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Checklist item not found"

    def test_non_admin_cannot_get_checklist(self, api_client: TestClient) -> None:
        """Non-admin user gets 403 on admin checklist endpoint."""
        response = api_client.get("/admin/checklists/1")
        assert response.status_code == 403


class TestAdminCreateChecklist:
    def test_admin_creates_checklist(self, admin_client: TestClient) -> None:
        """Admin can create a checklist item."""
        new_checklist_item = {
            "checklist_item": "Admin Checklist Item",
            "description": "Created by admin.",
            "criticality": 3,
        }
        response = admin_client.post("/admin/checklists", json=new_checklist_item)
        assert response.status_code == 201
        data = response.json()
        assert data["checklist_item"] == new_checklist_item["checklist_item"]
        assert data["description"] == new_checklist_item["description"]
        assert data["criticality"] == new_checklist_item["criticality"]

    def test_admin_creates_checklist_minimal(self, admin_client: TestClient) -> None:
        """Admin can create a checklist item with minimal fields."""
        new_checklist_item = {"checklist_item": "Minimal Admin Checklist Item"}
        response = admin_client.post("/admin/checklists", json=new_checklist_item)
        assert response.status_code == 201
        data = response.json()
        assert data["checklist_item"] == new_checklist_item["checklist_item"]

    def test_non_admin_cannot_create_checklist(self, api_client: TestClient) -> None:
        """Non-admin user gets 403 on admin create checklist item."""
        new_checklist_item = {"checklist_item": "Unauthorized Checklist Item"}
        response = api_client.post("/admin/checklists", json=new_checklist_item)
        assert response.status_code == 403


class TestAdminUpdateChecklist:
    def test_admin_updates_checklist(self, admin_client: TestClient) -> None:
        """Admin can update any checklist."""
        update_data = {
            "checklist_item": "Updated by Admin",
            "description": "Admin update.",
        }
        response = admin_client.put("/admin/checklists/1", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["checklist_item"] == update_data["checklist_item"]
        assert data["description"] == update_data["description"]

    def test_admin_updates_checklist_not_found(self, admin_client: TestClient) -> None:
        """Admin gets 404 when updating non-existent checklist."""
        update_data = {"checklist_item": "Nope"}
        response = admin_client.put("/admin/checklists/999", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Checklist item not found"

    def test_non_admin_cannot_update_checklist(self, api_client: TestClient) -> None:
        """Non-admin user gets 403 on admin update checklist."""
        update_data = {"checklist_item": "Unauthorized Update"}
        response = api_client.put("/admin/checklists/1", json=update_data)
        assert response.status_code == 403


class TestAdminDeleteChecklist:
    def test_admin_deletes_checklist(self, admin_client: TestClient) -> None:
        """Admin can delete any checklist."""
        response = admin_client.delete("/admin/checklists/1")
        assert response.status_code == 204
        assert response.content == b""

    def test_admin_deletes_checklist_not_found(self, admin_client: TestClient) -> None:
        """Admin gets 404 when deleting non-existent checklist."""
        response = admin_client.delete("/admin/checklists/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Checklist item not found"

    def test_non_admin_cannot_delete_checklist(self, api_client: TestClient) -> None:
        """Non-admin user gets 403 on admin delete checklist."""
        response = api_client.delete("/admin/checklists/1")
        assert response.status_code == 403


# ── Admin User CRUD Tests ──────────────────────────────────────────


class TestAdminReadUsers:
    def test_admin_reads_all_users(self, admin_client: TestClient) -> None:
        """Admin can list all users."""
        response = admin_client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_admin_reads_user_by_id(self, admin_client: TestClient) -> None:
        """Admin can get a user by ID."""
        response = admin_client.get("/users/2")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 2
        assert data["username"] == "adminuser"

    def test_admin_reads_user_not_found(self, admin_client: TestClient) -> None:
        """Admin gets 404 for non-existent user."""
        response = admin_client.get("/users/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_non_admin_cannot_read_users(self, api_client: TestClient) -> None:
        """Non-admin user gets 403 on admin user endpoints."""
        response = api_client.get("/users")
        assert response.status_code == 403
        response = api_client.get("/users/1")
        assert response.status_code == 403


class TestAdminCreateUser:
    def test_admin_creates_user(self, admin_client: TestClient) -> None:
        """Admin can create a user with default role."""
        new_user = {
            "username": "newuser",
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "phone_number": "555-0001",
            "password": "password123",
        }
        response = admin_client.post("/users", json=new_user)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == new_user["username"]
        assert data["phone_number"] == new_user["phone_number"]
        assert data["role"] == "user"
        assert "hashed_password" not in data

    def test_admin_creates_admin_user(self, admin_client: TestClient) -> None:
        """Admin can create a user with admin role."""
        new_user = {
            "username": "superadmin",
            "email": "super@example.com",
            "first_name": "Super",
            "last_name": "Admin",
            "phone_number": "555-0002",
            "password": "password123",
            "role": "admin",
        }
        response = admin_client.post("/users", json=new_user)
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "admin"

    def test_admin_create_user_duplicate_username(
        self, admin_client: TestClient
    ) -> None:
        """Admin gets 400 when creating user with duplicate username."""
        new_user = {
            "username": "adminuser",
            "email": "other@example.com",
            "first_name": "Dup",
            "last_name": "User",
            "phone_number": "555-0003",
            "password": "password123",
        }
        response = admin_client.post("/users", json=new_user)
        assert response.status_code == 400
        assert response.json()["detail"] == "Username already registered"

    def test_admin_create_user_duplicate_email(self, admin_client: TestClient) -> None:
        """Admin gets 400 when creating user with duplicate email."""
        new_user = {
            "username": "otheruser",
            "email": "admin@example.com",
            "first_name": "Dup",
            "last_name": "User",
            "phone_number": "555-0004",
            "password": "password123",
        }
        response = admin_client.post("/users", json=new_user)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_admin_create_user_missing_phone_number(
        self, admin_client: TestClient
    ) -> None:
        """Admin gets 422 when creating a user without phone_number."""
        new_user = {
            "username": "nophone",
            "email": "nophone@example.com",
            "first_name": "No",
            "last_name": "Phone",
            "password": "password123",
        }
        response = admin_client.post("/users", json=new_user)
        assert response.status_code == 422

    def test_non_admin_cannot_create_user(self, api_client: TestClient) -> None:
        """Non-admin user gets 403 on admin create user."""
        new_user = {
            "username": "hacker",
            "email": "hacker@example.com",
            "first_name": "Hack",
            "last_name": "Me",
            "phone_number": "555-0005",
            "password": "password123",
        }
        response = api_client.post("/users", json=new_user)
        assert response.status_code == 403


class TestAdminUpdateUser:
    def test_admin_updates_user(self, admin_client: TestClient) -> None:
        """Admin can update any user."""
        update_data = {"first_name": "Updated", "last_name": "Admin"}
        response = admin_client.put("/users/2", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == update_data["first_name"]

    def test_admin_updates_user_not_found(self, admin_client: TestClient) -> None:
        """Admin gets 404 when updating non-existent user."""
        update_data = {"first_name": "Nope"}
        response = admin_client.put("/users/999", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_non_admin_cannot_update_user(self, api_client: TestClient) -> None:
        """Non-admin user gets 403 on admin update user."""
        update_data = {"first_name": "Unauthorized"}
        response = api_client.put("/users/2", json=update_data)
        assert response.status_code == 403


class TestAdminDeleteUser:
    def test_admin_deletes_user(self, admin_client: TestClient) -> None:
        """Admin can delete a user."""
        # First create a user to delete
        new_user = {
            "username": "todelete",
            "email": "delete@example.com",
            "first_name": "Delete",
            "last_name": "Me",
            "phone_number": "555-0006",
            "password": "password123",
        }
        create_resp = admin_client.post("/users", json=new_user)
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]

        # Now delete it
        response = admin_client.delete(f"/users/{user_id}")
        assert response.status_code == 204
        assert response.content == b""

    def test_admin_deletes_user_not_found(self, admin_client: TestClient) -> None:
        """Admin gets 404 when deleting non-existent user."""
        response = admin_client.delete("/users/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_non_admin_cannot_delete_user(self, api_client: TestClient) -> None:
        """Non-admin user gets 403 on admin delete user."""
        response = api_client.delete("/users/2")
        assert response.status_code == 403
