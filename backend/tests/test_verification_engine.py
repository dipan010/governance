"""Verification Engine tests: before/after comparison and closure enforcement."""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEventRow
from app.domain.enums import VerificationResult
from app.domain.verification import evaluate_after_state, parse_expected_clauses


class TestEvaluator:
    def test_parse_clauses(self) -> None:
        clauses = parse_expected_clauses(
            "publicNetworkAccess == Disabled and networkAcls.defaultAction == Deny"
        )
        assert clauses == [
            ("publicNetworkAccess", "Disabled"),
            ("networkAcls.defaultAction", "Deny"),
        ]

    def test_compliant_after_state(self) -> None:
        result, details, next_action = evaluate_after_state(
            {"publicNetworkAccess": "Disabled", "networkAcls.defaultAction": "Deny"},
            "publicNetworkAccess == Disabled and networkAcls.defaultAction == Deny",
        )
        assert result is VerificationResult.COMPLIANT
        assert "Close the violation" in next_action

    def test_case_insensitive_boolean_match(self) -> None:
        result, _, _ = evaluate_after_state(
            {"enablePurgeProtection": True}, "enablePurgeProtection == true"
        )
        assert result is VerificationResult.COMPLIANT

    def test_failed_after_state_gives_next_action(self) -> None:
        result, details, next_action = evaluate_after_state(
            {"publicNetworkAccess": "Enabled", "networkAcls.defaultAction": "Allow"},
            "publicNetworkAccess == Disabled and networkAcls.defaultAction == Deny",
        )
        assert result is VerificationResult.FAILED
        assert "still non-compliant" in next_action
        assert any("expected 'Disabled', found 'Enabled'" in d for d in details)

    def test_no_after_state_is_not_run(self) -> None:
        result, _, next_action = evaluate_after_state(None, "x == y")
        assert result is VerificationResult.NOT_RUN
        assert "no after-state" in next_action.lower()

    def test_prose_expectation_requires_manual_verification(self) -> None:
        result, _, next_action = evaluate_after_state(
            {"something": "value"}, "no inbound allow from broad ranges"
        )
        assert result is VerificationResult.FAILED
        assert "manually" in next_action


class TestVerificationApi:
    def _ingest(self, client: TestClient, policy_fixture: dict[str, Any]) -> None:
        client.post("/api/ingest/policy", json=policy_fixture)

    def test_pol001_before_after_and_close(
        self,
        client: TestClient,
        policy_fixture: dict[str, Any],
        db_session: Session,
    ) -> None:
        self._ingest(client, policy_fixture)

        # Closure without verification is blocked.
        blocked = client.post("/api/violations/POL-001/close")
        assert blocked.status_code == 409
        assert blocked.json()["detail"]["error"] == "closure_blocked"
        assert blocked.json()["detail"]["nextAction"]

        verified = client.post("/api/violations/POL-001/verify")
        assert verified.status_code == 200
        body = verified.json()
        assert body["result"] == "Compliant"
        assert body["beforeState"]["publicNetworkAccess"] == "Enabled"
        assert body["afterState"]["publicNetworkAccess"] == "Disabled"
        assert body["verificationQuery"]
        assert body["actionStatus"] == "Verified"

        # Verified fix wrote an audit event.
        events = list(
            db_session.scalars(
                select(AuditEventRow).where(AuditEventRow.violation_id == "POL-001")
            )
        )
        assert any(e.event_type == "verification.completed" for e in events)
        assert all(e.correlation_id for e in events)

        closed = client.post("/api/violations/POL-001/close")
        assert closed.status_code == 200
        assert closed.json()["actionStatus"] == "Closed"
        close_events = list(
            db_session.scalars(
                select(AuditEventRow).where(
                    AuditEventRow.event_type == "violation.closed"
                )
            )
        )
        assert close_events

    def test_failed_verification_keeps_item_open(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        self._ingest(client, policy_fixture)
        failed = client.post(
            "/api/violations/POL-001/verify",
            json={
                "afterState": {
                    "publicNetworkAccess": "Enabled",
                    "networkAcls.defaultAction": "Allow",
                }
            },
        )
        assert failed.status_code == 200
        body = failed.json()
        assert body["result"] == "Failed"
        assert body["nextAction"]
        assert body["actionStatus"] != "Closed"

        still_blocked = client.post("/api/violations/POL-001/close")
        assert still_blocked.status_code == 409

    def test_no_after_state_cannot_close(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        self._ingest(client, policy_fixture)
        outcome = client.post("/api/violations/POL-002/verify").json()
        assert outcome["result"] == "NotRun"
        assert client.post("/api/violations/POL-002/close").status_code == 409

    def test_ticket_or_pr_alone_does_not_close(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        self._ingest(client, policy_fixture)
        artifacts = client.post("/api/violations/POL-001/artifact")
        assert artifacts.status_code == 200

        detail = client.get("/api/violations/POL-001").json()
        assert detail["evidence"]["actionState"]["actionStatus"] == "ArtifactCreated"

        blocked = client.post("/api/violations/POL-001/close")
        assert blocked.status_code == 409
        assert "after-state proof" in blocked.json()["detail"]["reason"]

    def test_verification_query_stored_on_outcome(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        self._ingest(client, policy_fixture)
        outcome = client.post("/api/violations/POL-001/verify").json()
        assert "publicNetworkAccess" in outcome["verificationQuery"]
        assert outcome["ruleVersion"] == "verification-1.0.0"
