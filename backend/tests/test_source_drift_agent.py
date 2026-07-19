"""Source-of-Truth Drift Agent tests."""

from typing import Any

import pytest

from app.agents.core_policy_agent import normalize_policy_finding
from app.agents.enrichment_agent import EnrichmentAgent
from app.agents.source_drift_agent import SourceDriftAgent
from app.connectors.defender import FixtureDefender
from app.connectors.owner_map import FixtureOwnerMap
from app.connectors.repo_map import FixtureRepoMap
from app.connectors.resource_inventory import FixtureResourceInventory
from app.connectors.verification_source import FixtureVerificationSource
from app.domain.enums import ConfidenceLevel
from app.domain.evidence_schema import CanonicalEvidence
from tests.conftest import FIXTURES


@pytest.fixture
def agent() -> SourceDriftAgent:
    return SourceDriftAgent(repos=FixtureRepoMap(FIXTURES))


@pytest.fixture
def enriched(policy_fixture: dict[str, Any]) -> dict[str, CanonicalEvidence]:
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
        result[evidence.violation_id] = evidence
    return result


def test_pol001_drift_analysis(
    agent: SourceDriftAgent, enriched: dict[str, CanonicalEvidence]
) -> None:
    evidence = enriched["POL-001"]
    analysis = agent.analyze(evidence)
    assert analysis is not None
    assert analysis.source_drift_likely is True
    assert analysis.source_confidence is ConfidenceLevel.HIGH
    assert analysis.repo_url == "https://github.com/dipan010/cloudgov-iac"
    assert analysis.repo_path == "terraform/storage/payments/storage_account.tf"
    assert analysis.module == "payments-storage"
    assert analysis.code_owner == "@payments-platform"

    by_name = {f.source_property: f for f in analysis.drifted_properties}
    assert by_name["public_network_access_enabled"].current_source_value == "true"
    assert by_name["public_network_access_enabled"].expected_source_value == "false"
    assert (
        by_name["public_network_access_enabled"].runtime_property
        == "publicNetworkAccess"
    )
    assert by_name["network_rules.default_action"].expected_source_value == "Deny"

    assert analysis.verification_query
    assert analysis.expected_compliant_value


def test_runtime_patch_marked_temporary_when_drift_exists(
    agent: SourceDriftAgent, enriched: dict[str, CanonicalEvidence]
) -> None:
    analysis = agent.analyze(enriched["POL-001"])
    assert analysis is not None
    assert analysis.runtime_patch_temporary is True


def test_pol003_mapped_but_no_drift(
    agent: SourceDriftAgent, enriched: dict[str, CanonicalEvidence]
) -> None:
    evidence = enriched["POL-003"]
    analysis = agent.analyze(evidence)
    assert analysis is not None
    assert analysis.source_drift_likely is False
    assert analysis.drifted_properties == []
    assert analysis.runtime_patch_temporary is False
    assert evidence.history.source_drift_likely is False


def test_unmapped_resource_returns_none(
    agent: SourceDriftAgent, enriched: dict[str, CanonicalEvidence]
) -> None:
    evidence = enriched["POL-005"]
    assert agent.analyze(evidence) is None
    assert evidence.history.source_confidence is ConfidenceLevel.UNKNOWN


def test_agent_updates_evidence_fields(
    agent: SourceDriftAgent, enriched: dict[str, CanonicalEvidence]
) -> None:
    evidence = enriched["POL-001"]
    evidence.history.source_drift_likely = None
    evidence.history.source_confidence = ConfidenceLevel.UNKNOWN
    agent.analyze(evidence)
    assert evidence.history.source_drift_likely is True
    assert evidence.history.source_confidence is ConfidenceLevel.HIGH
