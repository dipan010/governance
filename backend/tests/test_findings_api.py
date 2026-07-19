"""Ingestion and violations API contract tests."""

from typing import Any

from fastapi.testclient import TestClient


def test_ingest_policy_fixture_succeeds(
    client: TestClient, policy_fixture: dict[str, Any]
) -> None:
    response = client.post("/api/ingest/policy", json=policy_fixture)
    assert response.status_code == 200
    body = response.json()
    assert body["ingested"] == 5
    assert body["errors"] == 0
    assert body["ingestId"]
    ids = [r["violationId"] for r in body["results"]]
    assert ids == ["POL-001", "POL-002", "POL-003", "POL-004", "POL-005"]


def test_worklist_and_detail_after_ingest(
    client: TestClient, policy_fixture: dict[str, Any]
) -> None:
    client.post("/api/ingest/policy", json=policy_fixture)

    worklist = client.get("/api/violations").json()
    assert len(worklist) == 5
    by_id = {v["violationId"]: v for v in worklist}
    assert by_id["POL-001"]["severity"] == "High"
    assert "missing_owner" in by_id["POL-005"]["missingEvidence"]

    detail = client.get("/api/violations/POL-001").json()
    assert detail["evidence"]["policyEvidence"]["failureReason"] == (
        "publicNetworkAccess is Enabled"
    )
    # Raw evidence is preserved byte-for-byte alongside the normalized record.
    assert detail["rawEvidence"] == policy_fixture["findings"][0]


def test_invalid_record_returns_structured_warning(client: TestClient) -> None:
    response = client.post("/api/ingest/policy", json={"findings": [{"foo": "bar"}]})
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["status"] == "ingested_with_warnings"
    codes = {issue["code"] for issue in result["issues"]}
    assert "missing_resource_identity" in codes
    assert "missing_policy_id" in codes


def test_malformed_body_returns_structured_error(client: TestClient) -> None:
    response = client.post("/api/ingest/policy", json={"nope": True})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_unknown_violation_returns_structured_404(client: TestClient) -> None:
    response = client.get("/api/violations/POL-404")
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "violation_not_found"


def test_ingest_defender_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/ingest/defender",
        json={
            "findings": [
                {
                    "recommendationId": "defender-storage-secure-transfer",
                    "recommendation": "Secure transfer should be enabled",
                    "state": "Unhealthy",
                    "description": "supportsHttpsTrafficOnly is false",
                    "assessedAt": "2026-07-18T09:00:00+00:00",
                    "resourceId": "/subscriptions/s/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/st1",
                    "severity": "High",
                }
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["ingested"] == 1
