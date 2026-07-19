"""Action artifact composer and API tests."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

REQUIRED_SECTIONS = (
    "Violation ID",
    "Failure Reason",
    "Risk Score",
    "Recommended Route",
    "Approval",
    "Side Effects",
    "Verification",
)


def _ingest(client: TestClient, policy_fixture: dict[str, Any]) -> None:
    client.post("/api/ingest/policy", json=policy_fixture)


def _assert_required_sections(body: str, violation_id: str) -> None:
    for section in REQUIRED_SECTIONS:
        assert section in body, f"{violation_id}: missing section '{section}'"
    assert violation_id in body


def test_pol001_pr_comment_plus_ticket(
    client: TestClient, policy_fixture: dict[str, Any]
) -> None:
    _ingest(client, policy_fixture)
    response = client.post("/api/violations/POL-001/artifact")
    assert response.status_code == 200
    artifacts = {a["kind"]: a for a in response.json()}
    assert set(artifacts) == {"pr_comment_preview", "ticket"}

    pr = artifacts["pr_comment_preview"]
    _assert_required_sections(pr["body"], "POL-001")
    assert pr["isDraft"] is True
    # Source fix section is filled for the drifted storage account.
    assert "terraform/storage/payments/storage_account.tf" in pr["body"]
    assert "public_network_access_enabled" in pr["body"]
    assert "TEMPORARY" in pr["body"]

    ticket = artifacts["ticket"]
    _assert_required_sections(ticket["body"], "POL-001")
    assert "Payments Platform" in ticket["body"]


def test_pol002_ticket(client: TestClient, policy_fixture: dict[str, Any]) -> None:
    _ingest(client, policy_fixture)
    response = client.post("/api/violations/POL-002/artifact")
    assert response.status_code == 200
    (ticket,) = response.json()
    assert ticket["kind"] == "ticket"
    _assert_required_sections(ticket["body"], "POL-002")
    assert "Not applicable" in ticket["body"]  # no source drift mapping


def test_pol003_dry_run_requires_approval(
    client: TestClient, policy_fixture: dict[str, Any]
) -> None:
    _ingest(client, policy_fixture)

    denied = client.post("/api/violations/POL-003/artifact")
    assert denied.status_code == 403
    assert denied.json()["detail"]["error"] == "approval_gate"

    client.post("/api/violations/POL-003/approval-request")
    still_denied = client.post("/api/violations/POL-003/artifact")
    assert still_denied.status_code == 403

    client.post(
        "/api/violations/POL-003/approve",
        json={"decision": "approve", "approver": "cloudgov-approver"},
    )
    approved = client.post("/api/violations/POL-003/artifact")
    assert approved.status_code == 200
    (dry_run,) = approved.json()
    assert dry_run["kind"] == "remediation_dry_run"
    assert dry_run["requiresApproval"] is True
    assert dry_run["approvalState"] == "Approved"
    _assert_required_sections(dry_run["body"], "POL-003")
    assert "NO live change" in dry_run["body"]


def test_pol004_exception_request(
    client: TestClient, policy_fixture: dict[str, Any]
) -> None:
    _ingest(client, policy_fixture)

    invalid = client.post(
        "/api/violations/POL-004/artifact",
        json={
            "kind": "exception_request",
            "exceptionRequest": {
                "owner": "Analytics Engineering",
                "justification": "Migration window",
                "compensatingControl": "Firewall logging",
            },
        },
    )
    assert invalid.status_code == 403  # no expiry

    valid = client.post(
        "/api/violations/POL-004/artifact",
        json={
            "kind": "exception_request",
            "exceptionRequest": {
                "owner": "Analytics Engineering",
                "justification": "Migration window",
                "compensatingControl": "Firewall logging plus weekly review",
                "expiry": "2026-08-15T00:00:00+00:00",
                "reviewDate": "2026-08-01T00:00:00+00:00",
            },
        },
    )
    assert valid.status_code == 200
    (exception,) = valid.json()
    assert exception["kind"] == "exception_request"
    _assert_required_sections(exception["body"], "POL-004")
    assert "2026-08-15" in exception["body"]
    assert "Firewall logging plus weekly review" in exception["body"]


def test_pol005_blocked_card(
    client: TestClient, policy_fixture: dict[str, Any]
) -> None:
    _ingest(client, policy_fixture)
    response = client.post("/api/violations/POL-005/artifact")
    assert response.status_code == 200
    (card,) = response.json()
    assert card["kind"] == "blocked_card"
    _assert_required_sections(card["body"], "POL-005")
    # Blocked path states the rule and a safe alternative.
    assert "RULES.md 2.7: missing owner blocks auto-action" in card["body"]
    assert "Safe alternative" in card["body"]
    assert "owner discovery" in card["body"]

    detail = client.get("/api/violations/POL-005").json()
    assert detail["evidence"]["actionState"]["actionStatus"] == "Blocked"


def test_no_real_external_write(
    client: TestClient, policy_fixture: dict[str, Any]
) -> None:
    _ingest(client, policy_fixture)
    client.post("/api/violations/POL-001/artifact")
    detail = client.get("/api/violations/POL-001").json()
    state = detail["evidence"]["actionState"]
    # Draft ticket reference exists, but no real PR URL is ever set.
    assert state["ticketId"] is not None
    assert state["prUrl"] is None
    artifacts = client.get("/api/violations/POL-001/artifacts").json()
    assert all(a["isDraft"] for a in artifacts)


def test_forbidden_kind_rejected(
    client: TestClient, policy_fixture: dict[str, Any]
) -> None:
    _ingest(client, policy_fixture)
    response = client.post(
        "/api/violations/POL-001/artifact", json={"kind": "runtime_apply"}
    )
    assert response.status_code == 403
    assert "hackathon" in response.json()["detail"]["reason"]


def test_unknown_kind_rejected(
    client: TestClient, policy_fixture: dict[str, Any]
) -> None:
    _ingest(client, policy_fixture)
    response = client.post(
        "/api/violations/POL-001/artifact", json={"kind": "carrier_pigeon"}
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("violation_id", "expected_kinds"),
    [
        ("POL-001", {"pr_comment_preview", "ticket"}),
        ("POL-002", {"ticket"}),
        ("POL-004", {"ticket"}),
        ("POL-005", {"blocked_card"}),
    ],
)
def test_route_to_artifact_mapping(
    client: TestClient,
    policy_fixture: dict[str, Any],
    violation_id: str,
    expected_kinds: set[str],
) -> None:
    _ingest(client, policy_fixture)
    response = client.post(f"/api/violations/{violation_id}/artifact")
    assert response.status_code == 200
    assert {a["kind"] for a in response.json()} == expected_kinds
