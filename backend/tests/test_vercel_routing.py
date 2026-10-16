from fastapi.testclient import TestClient

from app.main import app


def test_api_prefix_reaches_fastapi_service() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
