from fastapi.testclient import TestClient


class TestRoot:
    def test_health_check(self, api_client: TestClient) -> None:
        """Verify the root endpoint returns the API name and running status."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Checklist App"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert data["docs"] == "/docs"


class TestReadChecklists:
    def test_get_all_checklists(self, api_client: TestClient) -> None:
        """Verify that all checklist items can be retrieved."""
        response = api_client.get("/checklists")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestReadChecklist:
    def test_get_checklist(self, api_client: TestClient) -> None:
        """Verify that a checklist can be retrieved."""
        response = api_client.get("/checklists/1")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_checklist_not_found(self, api_client: TestClient) -> None:
        """Verify that a non-existent checklist returns 404."""
        response = api_client.get("/checklists/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Checklist item not found"

    def test_get_checklist_invalid_id(self, api_client: TestClient) -> None:
        """Verify that an invalid checklist id returns 422."""
        response = api_client.get("/checklists/abc")
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Input should be a valid integer, unable to parse string as an integer"
        )


class TestCreateChecklist:
    def test_create_checklist(self, api_client: TestClient) -> None:
        """Verify that a checklist can be created."""
        new_checklist_item = {
            "checklist_item": "New Checklist Item",
            "description": "A new checklist item to do.",
        }
        response = api_client.post("/checklists", json=new_checklist_item)
        assert response.status_code == 201
        data = response.json()
        assert data["checklist_item"] == new_checklist_item["checklist_item"]
        assert data["description"] == new_checklist_item["description"]
        # Confirm is in the db
        response = api_client.get("/checklists")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_create_checklist_invalid_data(self, api_client: TestClient) -> None:
        """Verify that a checklist without required fields returns 422."""
        desc_only = {"description": "A new checklist to do."}
        response = api_client.post("/checklists", json=desc_only)
        assert response.status_code == 422
        assert response.json()["detail"][0]["msg"] == "Field required"

        criticality_only = {"criticality": 3}
        response = api_client.post("/checklists", json=criticality_only)
        assert response.status_code == 422

        executed_only = {"executed": False}
        response = api_client.post("/checklists", json=executed_only)
        assert response.status_code == 422

        all_optional = {
            "description": "A new checklist to do.",
            "criticality": 3,
            "executed": False,
        }
        response = api_client.post("/checklists", json=all_optional)
        assert response.status_code == 422


class TestUpdateChecklist:
    def test_update_checklist(self, api_client: TestClient) -> None:
        """Verify that a checklist can be updated."""
        update_data = {
            "checklist_item": "Updated checklist",
            "description": "An updated checklist.",
        }
        response = api_client.put("/checklists/1", json=update_data)
        assert response.status_code == 204
        assert response.content == b""  # <-- 204 has no body
        # Now check db to confirm update
        response = api_client.get("/checklists/1")
        assert response.status_code == 200
        data = response.json()
        assert data["checklist_item"] == update_data["checklist_item"]
        assert data["description"] == update_data["description"]

    def test_update_checklist_not_found(self, api_client: TestClient) -> None:
        """Verify that updating a non-existent checklist returns 404."""
        update_data = {
            "checklist_item": "Updated checklist",
            "description": "An updated checklist.",
        }
        response = api_client.put("/checklists/999", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Checklist item not found"

    def test_update_checklist_invalid_id(self, api_client: TestClient) -> None:
        """Verify that an invalid checklist id on update returns 422."""
        update_data = {
            "checklist_item": "Updated checklist",
            "description": "An updated checklist.",
        }
        response = api_client.put("/checklists/abc", json=update_data)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Input should be a valid integer, unable to parse string as an integer"
        )


class TestDeleteChecklist:
    def test_delete_checklist(self, api_client: TestClient) -> None:
        """Verify that a checklist can be deleted."""
        response = api_client.delete("/checklists/1")
        assert response.status_code == 204
        assert response.content == b""  # <-- 204 has no body
        # Now check db to confirm deletion
        response = api_client.get("/checklists/1")
        assert response.status_code == 404

    def test_delete_checklist_not_found(self, api_client: TestClient) -> None:
        """Verify that deleting a non-existent checklist returns 404."""
        response = api_client.delete("/checklists/999")
        assert response.status_code == 404


class TestOwnerIsolation:
    def test_user_cannot_see_other_checklists(
        self, isolation_client: TestClient
    ) -> None:
        """User 1 should not see checklist items owned by user 2."""
        response = isolation_client.get("/checklists")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_user_cannot_get_other_checklist(
        self, isolation_client: TestClient
    ) -> None:
        """User 1 should get 404 when trying to get user 2's checklist."""
        response = isolation_client.get("/checklists/1")
        assert response.status_code == 404
        assert response.json()["detail"] == "Checklist item not found"

    def test_user_cannot_update_other_checklist(
        self, isolation_client: TestClient
    ) -> None:
        """User 1 should get 404 when trying to update user 2's checklist."""
        update_data = {"checklist_item": "Hacked"}
        response = isolation_client.put("/checklists/1", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Checklist item not found"

    def test_user_cannot_delete_other_checklist(
        self, isolation_client: TestClient
    ) -> None:
        """User 1 should get 404 when trying to delete user 2's checklist."""
        response = isolation_client.delete("/checklists/1")
        assert response.status_code == 404
        assert response.json()["detail"] == "Checklist item not found"

    def test_partial_update(self, api_client: TestClient) -> None:
        """User can update only some fields of a checklist."""
        update_data = {"checklist_item": "Updated Item Only"}
        response = api_client.put("/checklists/1", json=update_data)
        assert response.status_code == 204

    def test_empty_checklist(self, api_client: TestClient) -> None:
        """GET /checklists returns empty list when no checklist items exist."""
        # Delete the existing checklist
        api_client.delete("/checklists/1")
        response = api_client.get("/checklists")
        assert response.status_code == 200
        assert response.json() == []

    def test_delete_checklist_invalid_id(self, api_client: TestClient) -> None:
        """Verify that an invalid checklist id on delete returns 422."""
        response = api_client.delete("/checklists/abc")
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Input should be a valid integer, unable to parse string as an integer"
        )
