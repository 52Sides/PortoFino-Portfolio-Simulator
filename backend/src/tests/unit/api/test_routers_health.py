import pytest

from fastapi.testclient import TestClient

from api.main import app


@pytest.mark.unit
def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
