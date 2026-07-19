"""Storage Firewall Compliance Agent detection tests."""

from typing import Any

import pytest

from app.agents.core_policy_agent import normalize_policy_finding
from app.agents.enrichment_agent import EnrichmentAgent
from app.agents.storage_firewall_agent import StorageFirewallAgent
from app.connectors.defender import FixtureDefender
from app.connectors.owner_map import FixtureOwnerMap
from app.connectors.repo_map import FixtureRepoMap, RepoMapping, SourceProperty
from app.connectors.resource_inventory import FixtureResourceInventory
from app.connectors.verification_source import FixtureVerificationSource
from app.domain.enums import FocusedSignal
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.focused_signals import SignalSource, merge_signals
from tests.conftest import FIXTURES


@pytest.fixture
def agent() -> StorageFirewallAgent:
    return StorageFirewallAgent()


@pytest.fixture
def pol001(policy_fixture: dict[str, Any]) -> tuple[CanonicalEvidence, dict[str, Any]]:
    record = policy_fixture["findings"][0]
    evidence = normalize_policy_finding(record).evidence
    enrichment = EnrichmentAgent(
        inventory=FixtureResourceInventory(FIXTURES),
        owners=FixtureOwnerMap(FIXTURES),
        repos=FixtureRepoMap(FIXTURES),
        defender=FixtureDefender(FIXTURES),
        verification=FixtureVerificationSource(FIXTURES),
    )
    enrichment.enrich(evidence)
    return evidence, record["properties"]


def test_applies_only_to_storage_accounts(
    agent: StorageFirewallAgent, policy_fixture: dict[str, Any]
) -> None:
    storage = normalize_policy_finding(policy_fixture["findings"][0]).evidence
    nsg = normalize_policy_finding(policy_fixture["findings"][1]).evidence
    assert agent.applies_to(storage) is True
    assert agent.applies_to(nsg) is False


def test_pol001_emits_all_storage_signals(
    agent: StorageFirewallAgent,
    pol001: tuple[CanonicalEvidence, dict[str, Any]],
) -> None:
    evidence, properties = pol001
    mapping = FixtureRepoMap(FIXTURES).get_mapping(evidence.resource_facts.resource_id)
    result = agent.detect(evidence, properties, mapping)

    signals = {d.signal for d in result.signals}
    assert FocusedSignal.STORAGE_PUBLIC_NETWORK_ACCESS in signals
    assert FocusedSignal.STORAGE_FIREWALL_DEFAULT_ALLOW in signals
    assert FocusedSignal.PRIVATE_ENDPOINT_GAP in signals
    assert FocusedSignal.SOURCE_DRIFT_LIKELY in signals

    drift = next(
        d for d in result.signals if d.signal is FocusedSignal.SOURCE_DRIFT_LIKELY
    )
    assert drift.source is SignalSource.SOURCE
    assert "storage_account.tf" in drift.evidence
    # Every signal carries the backing evidence fact.
    assert all(d.evidence for d in result.signals)


def test_compliant_storage_emits_no_signals(agent: StorageFirewallAgent) -> None:
    evidence = normalize_policy_finding(
        {
            "findingRef": "POL-OK",
            "policyId": "storage-public-network-disabled",
            "policyName": "Storage restrict",
            "complianceState": "NonCompliant",
            "failureReason": "n/a",
            "evaluatedAt": "2026-07-18T10:00:00+00:00",
            "resourceId": "/subscriptions/s/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/stok",
            "resourceType": "Microsoft.Storage/storageAccounts",
            "severity": "Low",
        }
    ).evidence
    properties = {
        "publicNetworkAccess": "Disabled",
        "networkAcls": {"defaultAction": "Deny"},
        "privateEndpointConnections": [{"id": "pe1"}],
    }
    result = agent.detect(evidence, properties, None)
    assert result.signals == []


def test_no_source_drift_signal_when_source_is_compliant(
    agent: StorageFirewallAgent,
    pol001: tuple[CanonicalEvidence, dict[str, Any]],
) -> None:
    evidence, properties = pol001
    compliant_mapping = RepoMapping(
        resource_id=evidence.resource_facts.resource_id,
        repo_url="https://github.com/dipan010/cloudgov-iac",
        repo_path="terraform/storage/payments/storage_account.tf",
        source_confidence="High",
        properties={
            "public_network_access_enabled": SourceProperty(
                current_source_value="false",
                expected_source_value="false",
                runtime_property="publicNetworkAccess",
            )
        },
    )
    result = agent.detect(evidence, properties, compliant_mapping)
    signals = {d.signal for d in result.signals}
    assert FocusedSignal.SOURCE_DRIFT_LIKELY not in signals


def test_agent_emits_signals_only_no_score_or_route(
    agent: StorageFirewallAgent,
    pol001: tuple[CanonicalEvidence, dict[str, Any]],
) -> None:
    evidence, properties = pol001
    mapping = FixtureRepoMap(FIXTURES).get_mapping(evidence.resource_facts.resource_id)
    result = agent.detect(evidence, properties, mapping)
    merge_signals(evidence, result)

    # Finding card data gains signals; decision fields stay untouched.
    assert FocusedSignal.STORAGE_PUBLIC_NETWORK_ACCESS in (
        evidence.risk_signals.focused_signals
    )
    assert evidence.decision.risk_score is None
    assert evidence.decision.risk_band is None
    assert evidence.decision.recommended_path is None
    assert result.blocker_candidates == []


def test_merge_signals_is_idempotent(
    agent: StorageFirewallAgent,
    pol001: tuple[CanonicalEvidence, dict[str, Any]],
) -> None:
    evidence, properties = pol001
    result = agent.detect(evidence, properties, None)
    merge_signals(evidence, result)
    first = list(evidence.risk_signals.focused_signals)
    merge_signals(evidence, result)
    assert evidence.risk_signals.focused_signals == first
