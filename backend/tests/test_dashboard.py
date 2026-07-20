"""Dashboard summary API tests (deferred from P15)."""

from typing import Any

from fastapi.testclient import TestClient


def test_summary_counts_after_full_flow(
    client: TestClient, policy_fixture: dict[str, Any]
) -> None:
    client.post("/api/ingest/policy", json=policy_fixture)
    client.post("/api/violations/POL-001/artifact")  # PR preview + ticket
    client.post("/api/violations/POL-005/artifact")  # blocked card
    client.post("/api/violations/POL-001/verify")

    summary = client.get("/api/dashboard/summary").json()
    assert summary["totalFindings"] == 5
    assert summary["criticalFindings"] == 1  # POL-001 band Critical
    assert summary["repeatViolations"] == 2  # POL-001, POL-004
    assert summary["autoRemediable"] == 1  # POL-003 dry-run route
    assert summary["tickets"] == 1
    assert summary["prComments"] == 1
    assert summary["blockedUnsafeActions"] == 1  # POL-005
    assert summary["verifiedFixes"] == 1  # POL-001 verified


def test_summary_empty_database(client: TestClient) -> None:
    summary = client.get("/api/dashboard/summary").json()
    assert summary["totalFindings"] == 0
    assert summary["verifiedFixes"] == 0
