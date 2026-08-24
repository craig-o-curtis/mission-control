from fastapi.testclient import TestClient


class TestRoot:
    def test_health_check(self, api_client: TestClient) -> None:
        """Verify the root endpoint returns the API name and running status."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Tasks App"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert data["docs"] == "/docs"


class TestReadTasks:
    def test_get_all_tasks(self, api_client: TestClient) -> None:
        """Verify that all tasks can be retrieved."""
        response = api_client.get("/tasks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestReadTask:
    def test_get_task(self, api_client: TestClient) -> None:
        """Verify that a task can be retrieved."""
        response = api_client.get("/tasks/1")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_task_not_found(self, api_client: TestClient) -> None:
        """Verify that a task can be retrieved."""
        response = api_client.get("/tasks/999")
        assert response.status_code == 404

        assert response.json()["detail"] == "Task not found"

    def test_get_task_invalid_id(self, api_client: TestClient) -> None:
        """Verify that a task can be retrieved."""
        response = api_client.get("/tasks/abc")
        assert response.status_code == 422

        assert (
            response.json()["detail"][0]["msg"]
            == "Input should be a valid integer, unable to parse string as an integer"
        )


class TestCreateTask:
    def test_create_task(self, api_client: TestClient) -> None:
        """Verify that a task can be created."""
        new_task = {"title": "New Task", "description": "A new task to do."}
        response = api_client.post("/tasks", json=new_task)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == new_task["title"]
        assert data["description"] == new_task["description"]
        # Confirm is in the db
        response = api_client.get("/tasks")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_create_task_invalid_data(self, api_client: TestClient) -> None:
        """Verify that a task can be created."""
        desc_only = {"description": "A new task to do."}
        response = api_client.post("/tasks", json=desc_only)
        assert response.status_code == 422

        assert response.json()["detail"][0]["msg"] == "Field required"

        priority_only = {"priority": 3}
        response = api_client.post("/tasks", json=priority_only)
        assert response.status_code == 422

        completed_only = {"completed": False}
        response = api_client.post("/tasks", json=completed_only)
        assert response.status_code == 422

        all_optional = {
            "description": "A new task to do.",
            "priority": 3,
            "completed": False,
        }
        response = api_client.post("/tasks", json=all_optional)
        assert response.status_code == 422


class TestUpdateTask:
    def test_update_task(self, api_client: TestClient) -> None:
        """Verify that a task can be updated."""
        update_data = {"title": "Updated Task", "description": "An updated task."}
        response = api_client.put("/tasks/1", json=update_data)
        assert response.status_code == 204
        assert response.content == b""  # <-- 204 has no body
        # Now check db to confirm update
        response = api_client.get("/tasks/1")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]

    def test_update_task_not_found(self, api_client: TestClient) -> None:
        """Verify that a task can be updated."""
        update_data = {"title": "Updated Task", "description": "An updated task."}
        response = api_client.put("/tasks/999", json=update_data)
        assert response.status_code == 404

        assert response.json()["detail"] == "Task not found"

    def test_update_task_invalid_id(self, api_client: TestClient) -> None:
        """Verify that a task can be updated."""
        update_data = {"title": "Updated Task", "description": "An updated task."}
        response = api_client.put("/tasks/abc", json=update_data)
        assert response.status_code == 422

        assert (
            response.json()["detail"][0]["msg"]
            == "Input should be a valid integer, unable to parse string as an integer"
        )


class TestDeleteTask:
    def test_delete_task(self, api_client: TestClient) -> None:
        """Verify that a task can be deleted."""
        response = api_client.delete("/tasks/1")
        assert response.status_code == 204
        assert response.content == b""  # <-- 204 has no body
        # Now check db to confirm deletion
        response = api_client.get("/tasks/1")
        assert response.status_code == 404

    def test_delete_task_not_found(self, api_client: TestClient) -> None:
        """Verify that a task can be deleted."""
        response = api_client.delete("/tasks/999")
        assert response.status_code == 404


class TestOwnerIsolation:
    def test_user_cannot_see_other_tasks(self, isolation_client: TestClient) -> None:
        """User 1 should not see tasks owned by user 2."""
        response = isolation_client.get("/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_user_cannot_get_other_task(self, isolation_client: TestClient) -> None:
        """User 1 should get 404 when trying to get user 2's task."""
        response = isolation_client.get("/tasks/1")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_user_cannot_update_other_task(self, isolation_client: TestClient) -> None:
        """User 1 should get 404 when trying to update user 2's task."""
        update_data = {"title": "Hacked"}
        response = isolation_client.put("/tasks/1", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_user_cannot_delete_other_task(self, isolation_client: TestClient) -> None:
        """User 1 should get 404 when trying to delete user 2's task."""
        response = isolation_client.delete("/tasks/1")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_partial_update(self, api_client: TestClient) -> None:
        """User can update only some fields of a task."""
        update_data = {"title": "Updated Title Only"}
        response = api_client.put("/tasks/1", json=update_data)
        assert response.status_code == 204

    def test_empty_task_list(self, api_client: TestClient) -> None:
        """GET /tasks returns empty list when no tasks exist."""
        # Delete the existing task
        api_client.delete("/tasks/1")
        response = api_client.get("/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_delete_task_invalid_id(self, api_client: TestClient) -> None:
        """Verify that a task can be deleted."""
        response = api_client.delete("/tasks/abc")
        assert response.status_code == 422

        assert (
            response.json()["detail"][0]["msg"]
            == "Input should be a valid integer, unable to parse string as an integer"
        )
