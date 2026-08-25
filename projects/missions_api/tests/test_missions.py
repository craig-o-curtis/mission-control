from __future__ import annotations

import copy

import pytest
from fastapi.testclient import TestClient
from missions_api import missions as missions_module
from missions_api.missions import MISSIONS, app

ORIGINAL_MISSIONS = copy.deepcopy(MISSIONS)


@pytest.fixture
def api_client(monkeypatch):
    # Ensure each test starts with a fresh copy of the original missions
    missions = copy.deepcopy(ORIGINAL_MISSIONS)
    monkeypatch.setattr(missions_module, "MISSIONS", missions)
    return TestClient(app)


class TestRoot:
    def test_health_check(self, api_client: TestClient) -> None:
        """Verify the root endpoint returns the API name and running status."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Missions API"
        assert data["status"] == "running"


class TestReadMissions:
    def test_read_all_missions(self, api_client: TestClient) -> None:
        """Verify GET /missions returns all missions with a 200 status."""
        response = api_client.get("/missions")
        assert response.status_code == 200
        missions = response.json()
        assert len(missions) == 6

    def test_filter_by_query_params(self, api_client: TestClient) -> None:
        """Verify filtering by query params returns the correct missions."""
        # Test mission_type
        response = api_client.get("/missions?mission_type=surface")
        assert response.status_code == 200
        assert len(response.json()) == 3
        # Test commander
        response = api_client.get("/missions?commander=Lovell")
        assert response.status_code == 200
        assert len(response.json()) == 2
        # Test mission_name
        response = api_client.get("/missions?mission_name=Artemis Lunar Landing")
        assert response.status_code == 200
        assert len(response.json()) == 1
        # Test description
        response = api_client.get("/missions?description=Crewed lunar landing attempt.")
        assert response.status_code == 200
        assert len(response.json()) == 1
        # Test phase
        response = api_client.get("/missions?phase=active")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_combined_query_filters(self, api_client: TestClient) -> None:
        """Verify combining multiple query filters works correctly."""
        response = api_client.get("/missions?mission_type=surface&phase=active")
        assert response.status_code == 200
        assert len(response.json()) == 1
        # Test one that doesn't exist
        response = api_client.get("/missions?mission_type=surface&phase=planning")
        assert response.status_code == 404

    def test_filter_by_category_case_insensitive(self, api_client: TestClient) -> None:
        """Verify mission_type filtering is case-insensitive."""
        response = api_client.get("/missions/categories/surface")
        assert response.status_code == 200
        missions = response.json()
        assert len(missions) == 3
        assert all(m["mission_type"] == "surface" for m in missions)

        response = api_client.get("/missions/categories/SURFACE")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_filter_by_author_case_insensitive(self, api_client: TestClient) -> None:
        """Verify commander filtering is case-insensitive."""
        response = api_client.get("/missions/commanders/Lovell")
        assert response.status_code == 200
        missions = response.json()
        assert len(missions) == 2
        assert missions[0]["commander"] == "Lovell"

        response = api_client.get("/missions/commanders/lovell")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_filter_by_title_case_insensitive(self, api_client: TestClient) -> None:
        """Verify mission_name filtering is case-insensitive."""
        response = api_client.get("/missions/names/Artemis Lunar Landing")
        assert response.status_code == 200
        missions = response.json()
        assert len(missions) == 1
        assert missions[0]["mission_name"] == "Artemis Lunar Landing"

    def test_filter_no_results(self, api_client: TestClient) -> None:
        """Verify filtering with no matching results returns 404."""
        response = api_client.get("/missions/categories/fantasy")
        assert response.status_code == 404

    def test_query_filter_no_results(self, api_client: TestClient) -> None:
        """Verify query param filtering with no results returns 404."""
        response = api_client.get("/missions?mission_type=fantasy")
        assert response.status_code == 404


class TestReadMission:
    def test_read_mission_by_id_found(self, api_client: TestClient) -> None:
        """Verify GET /missions/{id} returns the matching mission when it exists."""
        response = api_client.get("/missions/1")
        assert response.status_code == 200
        mission = response.json()
        assert mission["mission_name"] == "Artemis Lunar Landing"

    def test_read_mission_by_id_not_found(self, api_client: TestClient) -> None:
        """Verify GET /missions/{id} returns 404 when the mission does not exist."""
        response = api_client.get("/missions/999")
        assert response.status_code == 404

    def test_read_mission_by_id_non_integer(self, api_client: TestClient) -> None:
        """Verify non-integer mission ID returns 422."""
        response = api_client.get("/missions/abc")
        assert response.status_code == 422

    def test_read_mission_by_id_negative(self, api_client: TestClient) -> None:
        """Verify negative mission ID returns 422."""
        response = api_client.get("/missions/-1")
        assert response.status_code == 422


class TestCreateMission:
    def test_happy_path(self, api_client: TestClient) -> None:
        """Verify creating a mission returns the created mission with all fields."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "New Commander",
                "mission_type": "orbital",
            },
        )
        assert response.status_code == 201
        mission = response.json()
        assert mission["mission_name"] == "New Mission"
        assert mission["commander"] == "New Commander"
        assert mission["mission_type"] == "orbital"
        assert mission["id"] == 7

    def test_create_mission_with_all_fields(self, api_client: TestClient) -> None:
        """Verify creating a mission with all fields returns the created mission."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "New Commander",
                "mission_type": "orbital",
                "description": "A new mission",
                "phase": "planning",
                "priority": 2,
                "launch_date": "2026-10-01",
            },
        )
        assert response.status_code == 201
        mission = response.json()
        assert mission["mission_name"] == "New Mission"
        assert mission["commander"] == "New Commander"
        assert mission["mission_type"] == "orbital"
        assert mission["description"] == "A new mission"
        assert mission["phase"] == "planning"
        assert mission["priority"] == 2
        assert mission["launch_date"] == "2026-10-01"

    def test_create_mission_name_too_short(self, api_client: TestClient) -> None:
        """Verify creating a mission with a mission_name too short returns 422."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "A",
                "commander": "New Commander",
                "mission_type": "orbital",
            },
        )
        assert response.status_code == 422

    def test_create_mission_name_too_long(self, api_client: TestClient) -> None:
        """Verify creating a mission with a mission_name too long returns 422."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "A" * 101,
                "commander": "New Commander",
                "mission_type": "orbital",
            },
        )
        assert response.status_code == 422

    def test_create_commander_too_short(self, api_client: TestClient) -> None:
        """Verify creating a mission with a commander too short returns 422."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "A",
                "mission_type": "orbital",
            },
        )
        assert response.status_code == 422

    def test_create_commander_too_long(self, api_client: TestClient) -> None:
        """Verify creating a mission with a commander too long returns 422."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "A" * 101,
                "mission_type": "orbital",
            },
        )
        assert response.status_code == 422

    def test_create_description_too_short(self, api_client: TestClient) -> None:
        """Verify creating a mission with a description too short returns 422."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "New Commander",
                "mission_type": "orbital",
                "description": "A",
            },
        )
        assert response.status_code == 422

    def test_create_description_too_long(self, api_client: TestClient) -> None:
        """Verify creating a mission with a description too long returns 422."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "New Commander",
                "mission_type": "orbital",
                "description": "A" * 1001,
            },
        )
        assert response.status_code == 422

    def test_duplicate_mission_returns_409(self, api_client: TestClient) -> None:
        """Verify creating a duplicate mission returns 409."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "Artemis Lunar Landing",
                "commander": "Lovell",
                "mission_type": "surface",
            },
        )
        assert response.status_code == 409

    def test_create_missing_required_fields_422(self, api_client: TestClient) -> None:
        """Verify creating a mission without required fields returns 422."""
        # Missing mission_name
        response = api_client.post(
            "/missions", json={"commander": "New Commander", "mission_type": "orbital"}
        )
        assert response.status_code == 422
        # Missing commander
        response = api_client.post(
            "/missions", json={"mission_name": "New Mission", "mission_type": "orbital"}
        )
        assert response.status_code == 422
        # Missing mission_type
        response = api_client.post(
            "/missions",
            json={"mission_name": "New Mission", "commander": "New Commander"},
        )
        assert response.status_code == 422

    def test_exceeds_min_max_priority_422(self, api_client: TestClient) -> None:
        """Verify creating a mission with an invalid priority returns 422."""
        # Above max
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "New Commander",
                "mission_type": "orbital",
                "priority": 5,
            },
        )
        assert response.status_code == 422
        # Below min, zero
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "New Commander",
                "mission_type": "orbital",
                "priority": 0,
            },
        )
        assert response.status_code == 422
        # Below min, negative
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "New Commander",
                "mission_type": "orbital",
                "priority": -1,
            },
        )
        assert response.status_code == 422

    def test_invalid_phase_422(self, api_client: TestClient) -> None:
        """Verify creating a mission with an invalid phase returns 422."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "New Commander",
                "mission_type": "orbital",
                "phase": "blastoff",
            },
        )
        assert response.status_code == 422

    def test_create_mission_type_too_short(self, api_client: TestClient) -> None:
        """Verify creating a mission with mission_type too short returns 422."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "New Commander",
                "mission_type": "A",
            },
        )
        assert response.status_code == 422

    def test_create_mission_type_too_long(self, api_client: TestClient) -> None:
        """Verify creating a mission with mission_type too long returns 422."""
        response = api_client.post(
            "/missions",
            json={
                "mission_name": "New Mission",
                "commander": "New Commander",
                "mission_type": "A" * 51,
            },
        )
        assert response.status_code == 422


class TestUpdateMission:
    def test_happy_path(self, api_client: TestClient) -> None:
        """Verify updating a mission returns the updated mission with all fields."""
        response = api_client.put(
            "/missions/1",
            json={
                "mission_name": "Updated Mission",
                "commander": "Updated Commander",
                "mission_type": "orbital",
            },
        )
        assert response.status_code == 200
        mission = response.json()
        assert mission["mission_name"] == "Updated Mission"
        assert mission["commander"] == "Updated Commander"
        assert mission["mission_type"] == "orbital"
        assert mission["id"] == 1

    def test_update_nonexistent_mission_returns_404(
        self, api_client: TestClient
    ) -> None:
        """Verify updating a nonexistent mission returns 404."""
        response = api_client.put(
            "/missions/999",
            json={
                "mission_name": "Updated Mission",
                "commander": "Updated Commander",
                "mission_type": "orbital",
            },
        )
        assert response.status_code == 404

    def test_update_partial_fields(self, api_client: TestClient) -> None:
        """Verify updating only mission_name leaves other fields unchanged."""
        response = api_client.put(
            "/missions/1",
            json={"mission_name": "Updated Mission"},
        )
        assert response.status_code == 200
        mission = response.json()
        assert mission["mission_name"] == "Updated Mission"
        assert mission["commander"] == "Lovell"  # unchanged
        assert mission["mission_type"] == "surface"  # unchanged

    def test_update_clear_field_with_null(self, api_client: TestClient) -> None:
        """Verify setting a field to null clears it."""
        response = api_client.put(
            "/missions/1",
            json={"description": None},
        )
        assert response.status_code == 200
        mission = response.json()
        assert mission["description"] is None

    def test_update_invalid_priority(self, api_client: TestClient) -> None:
        """Verify invalid priority on update returns 422."""
        response = api_client.put(
            "/missions/1",
            json={"priority": 10},
        )
        assert response.status_code == 422

    def test_update_invalid_field_length(self, api_client: TestClient) -> None:
        """Verify invalid field length on update returns 422."""
        response = api_client.put(
            "/missions/1",
            json={"mission_name": "A"},
        )
        assert response.status_code == 422


class TestDeleteMission:
    def test_happy_path(self, api_client: TestClient) -> None:
        """Verify deleting a mission returns 204."""
        response = api_client.delete("/missions/1")
        assert response.status_code == 204

    def test_delete_already_deleted_404(self, api_client: TestClient) -> None:
        """Verify deleting a mission twice returns 404."""
        api_client.delete("/missions/1")
        response = api_client.delete("/missions/1")
        assert response.status_code == 404
        assert response.json()["detail"] == "Mission ID 1 not found."

    def test_delete_nonexistent_mission_returns_404(
        self, api_client: TestClient
    ) -> None:
        """Verify deleting a nonexistent mission returns 404."""
        response = api_client.delete("/missions/999")
        assert response.status_code == 404

    def test_delete_then_verify_gone(self, api_client: TestClient) -> None:
        """Verify deleted mission is actually removed."""
        api_client.delete("/missions/1")
        response = api_client.get("/missions/1")
        assert response.status_code == 404
