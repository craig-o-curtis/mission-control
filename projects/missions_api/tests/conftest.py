import pytest
from fastapi.testclient import TestClient
from missions_api.missions import app


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)
