"""Remediation Routing Planner tests."""

from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.agents.core_policy_agent import normalize_policy_finding
from app.agents.enrichment_agent import EnrichmentAgent
from app.agents.routing_planner import RoutingPlanner
from app.agents.scorer_agent import ScorerAgent
from app.connectors.defender import FixtureDefender
from app.connectors.owner_map import FixtureOwnerMap
from app.connectors.repo_map import FixtureRepoMap
from app.connectors.resource_inventory import FixtureResourceInventory
from app.connectors.verification_source import FixtureVerificationSource
from app.domain.enums import ActionStatus, BlockerCode, RoutePath
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.routing import ExceptionRequest, plan_route
from tests.conftest import FIXTURES


@pytest.fixture
def pipeline(policy_fixture: dict[str, Any]) -> dict[str, CanonicalEvidence]:
    enrichment = EnrichmentAgent(
        inventory=FixtureResourceInventory(FIXTURES),
        owners=FixtureOwnerMap(FIXTURES),
        repos=FixtureRepoMap(FIXTURES),
        defender=FixtureDefender(FIXTURES),
        verification=FixtureVerificationSource(FIXTURES),
    )
    result = {}
    for record in policy_fixture["findings"]:
        evidence = normalize_policy_finding(record).evidence
        enrichment.enrich(evidence)
        ScorerAgent().score(evidence)
        RoutingPlanner().route(evidence)
        result[evidence.violation_id] = evidence
    return result


def test_pol001_routes_to_source_pr_plus_change_ticket(
    pipeline: dict[str, CanonicalEvidence],
) -> None:
    decision = pipeline["POL-001"].decision
    assert decision.recommended_path is RoutePath.SOURCE_PR_PLUS_CHANGE_TICKET
    assert decision.approval_required is True
    assert decision.approver_role == "Cloud Governance Approver"
    assert decision.rollback_or_next_action


def test_pol002_routes_to_owner_ticket(
    pipeline: dict[str, CanonicalEvidence],
) -> None:
    # Owner exists but downtime risk is unknown on a production NSG:
    # automation is not safe, so the owner ticket / change request path wins.
    decision = pipeline["POL-002"].decision
    assert decision.recommended_path is RoutePath.OWNER_TICKET_OR_CHANGE_REQUEST
    assert BlockerCode.UNKNOWN_DOWNTIME_RISK in decision.blockers
    assert BlockerCode.PRODUCTION_RUNTIME_CHANGE in decision.blockers


def test_pol003_routes_to_remediation_dry_run_with_approval(
    pipeline: dict[str, CanonicalEvidence],
) -> None:
    decision = pipeline["POL-003"].decision
    assert decision.recommended_path is RoutePath.REMEDIATION_DRY_RUN
    assert decision.approval_required is True
    assert decision.approver_role == "Change Approver"


def test_pol004_routes_to_owner_ticket_change_review(
    pipeline: dict[str, CanonicalEvidence],
) -> None:
    decision = pipeline["POL-004"].decision
    assert decision.recommended_path is RoutePath.OWNER_TICKET_OR_CHANGE_REQUEST


def test_pol005_routes_to_blocked_manual_review(
    pipeline: dict[str, CanonicalEvidence],
) -> None:
    decision = pipeline["POL-005"].decision
    assert decision.recommended_path is RoutePath.BLOCKED_MANUAL_REVIEW
    assert BlockerCode.MISSING_OWNER in decision.blockers


def test_missing_resource_id_is_invalid_finding() -> None:
    evidence = normalize_policy_finding({"findingRef": "POL-EMPTY"}).evidence
    decision = plan_route(evidence)
    assert decision.route is RoutePath.INVALID_FINDING


def test_valid_exception_request_routes_to_time_bound_exception(
    pipeline: dict[str, CanonicalEvidence],
) -> None:
    evidence = pipeline["POL-004"].model_copy(deep=True)
    request = ExceptionRequest(
        owner="Analytics Engineering",
        justification="Broad range needed for one-off migration",
        compensating_control="Firewall logging plus weekly review",
        expiry=datetime(2026, 8, 15, tzinfo=UTC),
        review_date=datetime(2026, 8, 1, tzinfo=UTC),
    )
    decision = plan_route(evidence, request)
    assert decision.route is RoutePath.TIME_BOUND_EXCEPTION
    assert decision.approval_required is True


def test_exception_without_expiry_is_rejected(
    pipeline: dict[str, CanonicalEvidence],
) -> None:
    evidence = pipeline["POL-004"].model_copy(deep=True)
    request = ExceptionRequest(
        owner="Analytics Engineering",
        justification="Broad range needed",
        compensating_control="Logging",
        expiry=None,
    )
    decision = plan_route(evidence, request)
    assert decision.route is not RoutePath.TIME_BOUND_EXCEPTION
    assert BlockerCode.EXCEPTION_WITHOUT_EXPIRY in decision.blockers


def test_production_item_does_not_auto_apply(
    pipeline: dict[str, CanonicalEvidence],
) -> None:
    for violation_id in ("POL-001", "POL-002"):
        evidence = pipeline[violation_id]
        # Routing never executes anything: status stays Open, no artifacts.
        assert evidence.action_state.action_status is ActionStatus.OPEN
        assert evidence.action_state.remediation_task_id is None
        assert evidence.action_state.ticket_id is None
        assert evidence.action_state.pr_url is None
        # Any changing route on production requires approval first.
        if evidence.decision.recommended_path in (
            RoutePath.SOURCE_PR_PLUS_CHANGE_TICKET,
            RoutePath.REMEDIATION_DRY_RUN,
        ):
            assert evidence.decision.approval_required is True


def test_every_finding_has_a_route(pipeline: dict[str, CanonicalEvidence]) -> None:
    for evidence in pipeline.values():
        assert evidence.decision.recommended_path is not None
        assert evidence.decision.route_rule_version == "route-1.0.0"


def test_routing_is_deterministic(pipeline: dict[str, CanonicalEvidence]) -> None:
    for evidence in pipeline.values():
        first = plan_route(evidence)
        second = plan_route(evidence)
        assert first == second


def test_route_api(client: TestClient, policy_fixture: dict[str, Any]) -> None:
    client.post("/api/ingest/policy", json=policy_fixture)
    response = client.post("/api/violations/POL-001/route")
    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "source_pr_plus_change_ticket"
    assert body["approvalRequired"] is True
    assert body["sideEffects"]
    assert body["rollbackOrNextAction"]

    exception = client.post(
        "/api/violations/POL-004/route",
        json={
            "exceptionRequest": {
                "owner": "Analytics Engineering",
                "justification": "One-off migration window",
                "compensatingControl": "Firewall logging plus weekly review",
                "expiry": "2026-08-15T00:00:00+00:00",
            }
        },
    )
    assert exception.status_code == 200
    assert exception.json()["route"] == "time_bound_exception"

    missing = client.post("/api/violations/POL-404/route")
    assert missing.status_code == 404
