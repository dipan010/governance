"""Approval Gate tests: payload, enforcement, and persistence."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agents.approval_gate import ApprovalGate
from app.agents.core_policy_agent import normalize_policy_finding
from app.agents.enrichment_agent import EnrichmentAgent
from app.agents.routing_planner import RoutingPlanner
from app.agents.scorer_agent import ScorerAgent
from app.connectors.defender import FixtureDefender
from app.connectors.owner_map import FixtureOwnerMap
from app.connectors.repo_map import FixtureRepoMap
from app.connectors.resource_inventory import FixtureResourceInventory
from app.connectors.verification_source import FixtureVerificationSource
from app.domain.approval import (
    ActionKind,
    ApprovalGateError,
    ApprovalRequiredError,
    ChangeCategory,
    change_categories,
    validate_action,
)
from app.domain.enums import ActionStatus, ApprovalState
from app.domain.evidence_schema import CanonicalEvidence
from app.repositories.approvals_repo import ApprovalsRepository
from app.repositories.violations_repo import ViolationsRepository
from tests.conftest import FIXTURES


def _pipeline(record: dict[str, Any]) -> CanonicalEvidence:
    evidence = normalize_policy_finding(record).evidence
    EnrichmentAgent(
        inventory=FixtureResourceInventory(FIXTURES),
        owners=FixtureOwnerMap(FIXTURES),
        repos=FixtureRepoMap(FIXTURES),
        defender=FixtureDefender(FIXTURES),
        verification=FixtureVerificationSource(FIXTURES),
    ).enrich(evidence)
    ScorerAgent().score(evidence)
    RoutingPlanner().route(evidence)
    return evidence


@pytest.fixture
def gate(db_session: Session) -> ApprovalGate:
    return ApprovalGate(
        ApprovalsRepository(db_session), ViolationsRepository(db_session)
    )


@pytest.fixture
def stored_pol003(
    db_session: Session, policy_fixture: dict[str, Any]
) -> tuple[CanonicalEvidence, str]:
    evidence = _pipeline(policy_fixture["findings"][2])
    repo = ViolationsRepository(db_session)
    raw_id = repo.add_raw_finding("policy", "ingest-1", policy_fixture["findings"][2])
    repo.upsert_violation(evidence, raw_id)
    db_session.flush()
    return evidence, raw_id


def test_approval_payload_is_complete(
    gate: ApprovalGate, stored_pol003: tuple[CanonicalEvidence, str]
) -> None:
    evidence, raw_id = stored_pol003
    row = gate.request(evidence, raw_id)
    payload = row.payload
    assert payload["violationId"] == "POL-003"
    assert payload["approverRole"] == "Change Approver"
    assert payload["resourceId"] == evidence.resource_facts.resource_id
    assert payload["route"] == "remediation_dry_run"
    assert payload["riskScore"] is not None
    assert payload["sideEffects"]
    assert payload["rollbackOrNextAction"]
    assert payload["verificationQuery"]
    assert ChangeCategory.RUNTIME_CLOUD_CHANGE.value in payload["changeCategories"]
    assert evidence.action_state.action_status is ActionStatus.AWAITING_APPROVAL


def test_dry_run_cannot_execute_without_approval(
    gate: ApprovalGate, stored_pol003: tuple[CanonicalEvidence, str]
) -> None:
    evidence, raw_id = stored_pol003
    with pytest.raises(ApprovalRequiredError):
        gate.ensure_allowed(evidence, ActionKind.REMEDIATION_DRY_RUN)
    gate.request(evidence, raw_id)
    with pytest.raises(ApprovalRequiredError):  # requested is not approved
        gate.ensure_allowed(evidence, ActionKind.REMEDIATION_DRY_RUN)
    gate.decide(evidence, raw_id, "approve", "cloudgov-approver", None)
    gate.ensure_allowed(evidence, ActionKind.REMEDIATION_DRY_RUN)  # no raise
    assert evidence.action_state.approver == "cloudgov-approver"
    assert evidence.action_state.action_status is ActionStatus.APPROVED


def test_production_cannot_auto_apply_even_with_approval(
    gate: ApprovalGate,
    db_session: Session,
    policy_fixture: dict[str, Any],
) -> None:
    evidence = _pipeline(policy_fixture["findings"][0])  # POL-001, production
    repo = ViolationsRepository(db_session)
    raw_id = repo.add_raw_finding("policy", "ingest-1", policy_fixture["findings"][0])
    repo.upsert_violation(evidence, raw_id)
    gate.request(evidence, raw_id)
    gate.decide(evidence, raw_id, "approve", "cloudgov-approver", None)
    # Hackathon mode: runtime apply and source push are refused outright.
    with pytest.raises(ApprovalGateError, match="hackathon"):
        gate.ensure_allowed(evidence, ActionKind.RUNTIME_APPLY)
    with pytest.raises(ApprovalGateError, match="hackathon"):
        gate.ensure_allowed(evidence, ActionKind.SOURCE_PUSH)
    # Ticket and PR/comment previews remain allowed.
    gate.ensure_allowed(evidence, ActionKind.TICKET)
    gate.ensure_allowed(evidence, ActionKind.PR_COMMENT_PREVIEW)


def test_rejection_reason_persists(
    gate: ApprovalGate,
    db_session: Session,
    stored_pol003: tuple[CanonicalEvidence, str],
) -> None:
    evidence, raw_id = stored_pol003
    gate.request(evidence, raw_id)
    gate.decide(evidence, raw_id, "reject", "cloudgov-approver", "Change freeze")
    row = ApprovalsRepository(db_session).latest_for("POL-003")
    assert row is not None
    assert row.status == "Rejected"
    assert row.reason == "Change freeze"
    assert row.decided_at is not None
    assert evidence.action_state.action_status is ActionStatus.REJECTED


def test_reject_without_reason_is_refused(
    gate: ApprovalGate, stored_pol003: tuple[CanonicalEvidence, str]
) -> None:
    evidence, raw_id = stored_pol003
    gate.request(evidence, raw_id)
    with pytest.raises(ApprovalGateError, match="reason"):
        gate.decide(evidence, raw_id, "reject", "approver", None)
    with pytest.raises(ApprovalGateError, match="reason"):
        gate.decide(evidence, raw_id, "defer", "approver", "")


def test_change_categories_cover_rule_2_1(policy_fixture: dict[str, Any]) -> None:
    pol001 = _pipeline(policy_fixture["findings"][0])
    categories = change_categories(pol001)
    assert ChangeCategory.SOURCE_CODE_CHANGE in categories
    assert ChangeCategory.NETWORK_EXPOSURE_CHANGE in categories
    assert ChangeCategory.PRODUCTION_BEHAVIOR_CHANGE in categories

    pol003 = _pipeline(policy_fixture["findings"][2])
    categories3 = change_categories(pol003)
    assert ChangeCategory.RUNTIME_CLOUD_CHANGE in categories3
    assert ChangeCategory.IDENTITY_CHANGE in categories3  # Key Vault


def test_validate_action_drafts_allowed_without_approval(
    policy_fixture: dict[str, Any],
) -> None:
    evidence = _pipeline(policy_fixture["findings"][1])
    for kind in (
        ActionKind.TICKET,
        ActionKind.PR_COMMENT_PREVIEW,
        ActionKind.BLOCKED_CARD,
        ActionKind.EXCEPTION_REQUEST,
        ActionKind.ESCALATION_NOTE,
    ):
        validate_action(evidence, kind, ApprovalState.NOT_REQUESTED)  # no raise


class TestApprovalApi:
    def test_full_approval_flow(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        client.post("/api/ingest/policy", json=policy_fixture)

        requested = client.post("/api/violations/POL-003/approval-request")
        assert requested.status_code == 200
        body = requested.json()
        assert body["status"] == "Requested"
        assert body["payload"]["approverRole"] == "Change Approver"
        assert body["payload"]["verificationQuery"]

        decided = client.post(
            "/api/violations/POL-003/approve",
            json={"decision": "approve", "approver": "cloudgov-approver"},
        )
        assert decided.status_code == 200
        assert decided.json()["status"] == "Approved"

        detail = client.get("/api/violations/POL-003").json()
        assert detail["approvals"]  # payload visible in finding card
        assert detail["approvals"][0]["payload"]["route"] == "remediation_dry_run"
        assert detail["evidence"]["actionState"]["actionStatus"] == "Approved"

    def test_rejection_persists_via_api(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        client.post("/api/ingest/policy", json=policy_fixture)
        client.post("/api/violations/POL-001/approval-request")
        rejected = client.post(
            "/api/violations/POL-001/approve",
            json={
                "decision": "reject",
                "approver": "cloudgov-approver",
                "reason": "Wrong change window",
            },
        )
        assert rejected.status_code == 200
        approvals = client.get("/api/violations/POL-001/approvals").json()
        assert approvals[-1]["status"] == "Rejected"
        assert approvals[-1]["reason"] == "Wrong change window"

    def test_reject_without_reason_is_403(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        client.post("/api/ingest/policy", json=policy_fixture)
        client.post("/api/violations/POL-001/approval-request")
        response = client.post(
            "/api/violations/POL-001/approve",
            json={"decision": "reject", "approver": "cloudgov-approver"},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "approval_gate"

    def test_decide_without_request_is_403(
        self, client: TestClient, policy_fixture: dict[str, Any]
    ) -> None:
        client.post("/api/ingest/policy", json=policy_fixture)
        response = client.post(
            "/api/violations/POL-002/approve",
            json={"decision": "approve", "approver": "cloudgov-approver"},
        )
        assert response.status_code == 403
