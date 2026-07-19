"""NSG Drift Management Agent detection tests."""

import copy
from typing import Any

import pytest

from app.agents.core_policy_agent import normalize_policy_finding
from app.agents.enrichment_agent import EnrichmentAgent
from app.agents.nsg_drift_agent import NsgDriftAgent, _range_is_sensitive
from app.connectors.defender import FixtureDefender
from app.connectors.owner_map import FixtureOwnerMap
from app.connectors.repo_map import FixtureRepoMap
from app.connectors.resource_inventory import FixtureResourceInventory
from app.connectors.verification_source import FixtureVerificationSource
from app.domain.enums import BlockerCode, FocusedSignal
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.focused_signals import merge_signals
from tests.conftest import FIXTURES


@pytest.fixture
def agent() -> NsgDriftAgent:
    return NsgDriftAgent()


@pytest.fixture
def pol002(policy_fixture: dict[str, Any]) -> tuple[CanonicalEvidence, dict[str, Any]]:
    record = policy_fixture["findings"][1]
    evidence = normalize_policy_finding(record).evidence
    EnrichmentAgent(
        inventory=FixtureResourceInventory(FIXTURES),
        owners=FixtureOwnerMap(FIXTURES),
        repos=FixtureRepoMap(FIXTURES),
        defender=FixtureDefender(FIXTURES),
        verification=FixtureVerificationSource(FIXTURES),
    ).enrich(evidence)
    return evidence, record["properties"]


def test_applies_only_to_nsgs(
    agent: NsgDriftAgent, policy_fixture: dict[str, Any]
) -> None:
    storage = normalize_policy_finding(policy_fixture["findings"][0]).evidence
    nsg = normalize_policy_finding(policy_fixture["findings"][1]).evidence
    assert agent.applies_to(nsg) is True
    assert agent.applies_to(storage) is False


def test_pol002_emits_cidr_port_and_priority_signals(
    agent: NsgDriftAgent, pol002: tuple[CanonicalEvidence, dict[str, Any]]
) -> None:
    evidence, properties = pol002
    result = agent.detect(evidence, properties)
    signals = {d.signal for d in result.signals}
    assert FocusedSignal.BROAD_SOURCE_CIDR in signals
    assert FocusedSignal.SENSITIVE_PORT_EXPOSED in signals
    assert FocusedSignal.PRIORITY_DRIFT in signals
    assert all(d.evidence for d in result.signals)


def test_pol002_blocker_candidates_are_side_effect_gaps(
    agent: NsgDriftAgent, pol002: tuple[CanonicalEvidence, dict[str, Any]]
) -> None:
    evidence, properties = pol002
    result = agent.detect(evidence, properties)
    # Owner exists for POL-002, so no missing_owner; but downtime risk is
    # unknown and the NSG is production — both restrict actionability.
    assert BlockerCode.MISSING_OWNER not in result.blocker_candidates
    assert BlockerCode.UNKNOWN_DOWNTIME_RISK in result.blocker_candidates
    assert BlockerCode.PRODUCTION_RUNTIME_CHANGE in result.blocker_candidates


def test_missing_owner_becomes_blocker_candidate_not_route(
    agent: NsgDriftAgent, pol002: tuple[CanonicalEvidence, dict[str, Any]]
) -> None:
    evidence, properties = pol002
    ownerless = evidence.model_copy(deep=True)
    ownerless.ownership.owner_team = None
    result = agent.detect(ownerless, properties)
    assert BlockerCode.MISSING_OWNER in result.blocker_candidates
    # Candidate only: the agent never selects the final route.
    merge_signals(ownerless, result)
    assert ownerless.decision.recommended_path is None
    assert ownerless.decision.blockers == []


def test_outbound_and_deny_rules_are_ignored(agent: NsgDriftAgent) -> None:
    evidence = normalize_policy_finding(
        {
            "findingRef": "POL-NSG-OK",
            "policyId": "nsg-restrict-management-ports",
            "policyName": "NSG policy",
            "complianceState": "NonCompliant",
            "failureReason": "n/a",
            "evaluatedAt": "2026-07-18T10:00:00+00:00",
            "resourceId": "/subscriptions/s/resourceGroups/rg/providers/Microsoft.Network/networkSecurityGroups/nsg-ok",
            "resourceType": "Microsoft.Network/networkSecurityGroups",
            "severity": "Low",
        }
    ).evidence
    properties = {
        "securityRules": [
            {
                "name": "deny-ssh",
                "direction": "Inbound",
                "access": "Deny",
                "sourceAddressPrefix": "0.0.0.0/0",
                "destinationPortRange": "22",
                "priority": 100,
            },
            {
                "name": "allow-outbound-all",
                "direction": "Outbound",
                "access": "Allow",
                "sourceAddressPrefix": "*",
                "destinationPortRange": "*",
                "priority": 200,
            },
        ]
    }
    result = agent.detect(evidence, properties)
    assert result.signals == []


@pytest.mark.parametrize(
    ("port_range", "expected"),
    [
        ("22", True),
        ("3389", True),
        ("1433", True),
        ("5432", True),
        ("8080", False),
        ("20-30", True),  # contains SSH
        ("8000-8080", False),
        ("1-65535", True),  # broad range
        ("*", True),
        ("not-a-port", False),
    ],
)
def test_port_range_sensitivity(port_range: str, expected: bool) -> None:
    assert _range_is_sensitive(port_range) is expected


def test_agent_does_not_auto_remediate(
    agent: NsgDriftAgent, pol002: tuple[CanonicalEvidence, dict[str, Any]]
) -> None:
    evidence, properties = pol002
    properties_before = copy.deepcopy(properties)
    result = agent.detect(evidence, properties)
    merge_signals(evidence, result)
    # Runtime properties untouched, no action recorded, no score or route.
    assert properties == properties_before
    assert evidence.action_state.remediation_task_id is None
    assert evidence.action_state.action_status.value == "Open"
    assert evidence.decision.risk_score is None
    assert evidence.decision.recommended_path is None
