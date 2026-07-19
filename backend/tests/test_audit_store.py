"""Audit store tests: coverage, prompt-run ID, masking, append-only."""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.audit import (
    AppendOnlyViolationError,
    AuditEventType,
    current_prompt_run_id,
)
from app.repositories.audit_repo import AuditRepository


def _events(client: TestClient, violation_id: str) -> list[dict[str, Any]]:
    response = client.get(f"/api/audit/{violation_id}")
    assert response.status_code == 200
    events: list[dict[str, Any]] = response.json()
    return events


class TestPipelineCoverage:
    def test_every_major_decision_has_audit_event(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        client.post("/api/ingest/policy", json=policy_fixture)
        types = {e["eventType"] for e in _events(client, "POL-001")}
        assert {
            "finding.ingested",
            "finding.normalized",
            "finding.enriched",
            "focused_agent.signals_detected",
            "risk.scored",
            "route.planned",
        } <= types

    def test_approval_and_artifact_and_verification_events(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        client.post("/api/ingest/policy", json=policy_fixture)
        client.post("/api/violations/POL-003/approval-request")
        client.post(
            "/api/violations/POL-003/approve",
            json={"decision": "approve", "approver": "cloudgov-approver"},
        )
        client.post("/api/violations/POL-003/artifact")
        types = {e["eventType"] for e in _events(client, "POL-003")}
        assert "approval.requested" in types
        assert "approval.approved" in types
        assert "artifact.generated" in types

        client.post("/api/violations/POL-001/verify")
        types001 = {e["eventType"] for e in _events(client, "POL-001")}
        assert "verification.completed" in types001

    def test_blocked_and_exception_events(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        client.post("/api/ingest/policy", json=policy_fixture)
        client.post("/api/violations/POL-005/artifact")
        assert "violation.blocked" in {
            e["eventType"] for e in _events(client, "POL-005")
        }

        client.post(
            "/api/violations/POL-004/artifact",
            json={
                "kind": "exception_request",
                "exceptionRequest": {
                    "owner": "Analytics Engineering",
                    "justification": "Migration window",
                    "compensatingControl": "Firewall logging",
                    "expiry": "2026-08-15T00:00:00+00:00",
                },
            },
        )
        assert "exception.created" in {
            e["eventType"] for e in _events(client, "POL-004")
        }

    def test_events_have_correlation_and_prompt_run_id(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        client.post("/api/ingest/policy", json=policy_fixture)
        events = _events(client, "POL-001")
        assert events
        expected_prompt = current_prompt_run_id()
        assert expected_prompt != "unknown"
        for event in events:
            assert event["correlationId"]
            assert event["promptRunId"] == expected_prompt
        # Pipeline events for one record share a correlation ID.
        pipeline = [e for e in events if e["eventType"].startswith("finding.")]
        assert len({e["correlationId"] for e in pipeline}) == 1

    def test_verification_event_stores_evidence_packet(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        client.post("/api/ingest/policy", json=policy_fixture)
        client.post("/api/violations/POL-001/verify")
        completed = [
            e
            for e in _events(client, "POL-001")
            if e["eventType"] == "verification.completed"
        ]
        assert completed
        location = completed[-1]["evidencePacket"]
        assert location and location.startswith("local://evidence_packets/POL-001/")
        # The packet file exists and holds before/after proof.
        relative = location.removeprefix("local://evidence_packets/")
        packet_path = get_settings().evidence_packets_dir / relative
        packet = json.loads(Path(packet_path).read_text())
        assert packet["beforeState"]["publicNetworkAccess"] == "Enabled"
        assert packet["afterState"]["publicNetworkAccess"] == "Disabled"


class TestMaskingAndAppendOnly:
    def test_secrets_are_masked_in_audit_payloads(self, db_session: Session) -> None:
        repo = AuditRepository(db_session)
        row = repo.add_event(
            "POL-TEST",
            AuditEventType.FINDING_INGESTED,
            {
                "clientSecret": "super-secret-value",
                "connectionString": "Server=...;Password=hunter2",
                "nested": {"sasToken": "sv=abc", "safe": "visible"},
                "resourceId": "/subscriptions/x",
            },
        )
        db_session.flush()
        assert row.payload["clientSecret"] == "***MASKED***"
        assert row.payload["connectionString"] == "***MASKED***"
        assert row.payload["nested"]["sasToken"] == "***MASKED***"
        assert row.payload["nested"]["safe"] == "visible"
        assert row.payload["resourceId"] == "/subscriptions/x"

    def test_audit_rows_cannot_be_updated(self, db_session: Session) -> None:
        repo = AuditRepository(db_session)
        row = repo.add_event("POL-TEST", AuditEventType.FINDING_INGESTED, {"a": 1})
        db_session.flush()
        row.event_type = "tampered"
        with pytest.raises(AppendOnlyViolationError):
            db_session.flush()
        db_session.rollback()

    def test_audit_rows_cannot_be_deleted(self, db_session: Session) -> None:
        repo = AuditRepository(db_session)
        row = repo.add_event("POL-TEST", AuditEventType.FINDING_INGESTED, {"a": 1})
        db_session.flush()
        db_session.delete(row)
        with pytest.raises(AppendOnlyViolationError):
            db_session.flush()
        db_session.rollback()

    def test_repository_exposes_no_mutation_methods(self) -> None:
        assert not hasattr(AuditRepository, "update_event")
        assert not hasattr(AuditRepository, "delete_event")

    def test_evidence_packet_store_masks_secrets(self, tmp_path: Path) -> None:
        from app.connectors.storage import LocalEvidencePacketStore

        store = LocalEvidencePacketStore(tmp_path)
        location = store.put(
            "POL-TEST", "packet", {"accessKey": "abc123", "state": "ok"}
        )
        assert location == "local://evidence_packets/POL-TEST/packet.json"
        saved = json.loads((tmp_path / "POL-TEST" / "packet.json").read_text())
        assert saved["accessKey"] == "***MASKED***"
        assert saved["state"] == "ok"
