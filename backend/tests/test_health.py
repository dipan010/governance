"""Health and version endpoint tests."""

from fastapi.testclient import TestClient

from app.core.config import APP_NAME, APP_VERSION
from app.domain.evidence_schema import SCHEMA_VERSION
from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["environment"] == "local"


def test_version_reports_app_and_schema_version() -> None:
    response = client.get("/api/version")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == APP_NAME
    assert body["version"] == APP_VERSION
    assert body["schemaVersion"] == SCHEMA_VERSION
