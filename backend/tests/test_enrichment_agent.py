"""Enrichment agent tests against the P02 fixtures."""

from typing import Any

import pytest

from app.agents.core_policy_agent import normalize_policy_finding
from app.agents.enrichment_agent import EnrichmentAgent
from app.connectors.defender import FixtureDefender
from app.connectors.owner_map import FixtureOwnerMap
from app.connectors.repo_map import FixtureRepoMap
from app.connectors.resource_inventory import FixtureResourceInventory
from app.connectors.verification_source import FixtureVerificationSource
from app.core.logging import mask_sensitive
from app.domain.enums import (
    ConfidenceLevel,
    DataClassification,
    EnvironmentType,
    ImpactLevel,
)
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.validation import MissingEvidence
from tests.conftest import FIXTURES


@pytest.fixture
def agent() -> EnrichmentAgent:
    return EnrichmentAgent(
        inventory=FixtureResourceInventory(FIXTURES),
        owners=FixtureOwnerMap(FIXTURES),
        repos=FixtureRepoMap(FIXTURES),
        defender=FixtureDefender(FIXTURES),
        verification=FixtureVerificationSource(FIXTURES),
    )


@pytest.fixture
def enriched(
    agent: EnrichmentAgent, policy_fixture: dict[str, Any]
) -> dict[str, CanonicalEvidence]:
    result = {}
    for record in policy_fixture["findings"]:
        evidence = normalize_policy_finding(record).evidence
        result[evidence.violation_id] = agent.enrich(evidence)
    return result


def test_pol001_enriches_as_hero_scenario(
    enriched: dict[str, CanonicalEvidence],
) -> None:
    pol001 = enriched["POL-001"]
    assert pol001.resource_facts.environment is EnvironmentType.PRODUCTION
    assert pol001.risk_signals.data_classification is DataClassification.RESTRICTED
    assert pol001.risk_signals.internet_exposure is True
    assert pol001.ownership.owner_team == "Payments Platform"
    assert pol001.ownership.owner_confidence is ConfidenceLevel.HIGH
    assert pol001.ownership.repo_path == "terraform/storage/payments/storage_account.tf"
    assert pol001.history.source_confidence is ConfidenceLevel.HIGH
    assert pol001.history.source_drift_likely is True
    assert pol001.history.recurrence_count == 2
    assert pol001.verification.verification_query
    assert pol001.verification.before_state == {
        "publicNetworkAccess": "Enabled",
        "networkAcls.defaultAction": "Allow",
    }
    for flag in (
        MissingEvidence.MISSING_OWNER,
        MissingEvidence.MISSING_REPO_MAP,
        MissingEvidence.MISSING_VERIFICATION_QUERY,
    ):
        assert flag.value not in pol001.missing_evidence


def test_pol005_stays_ownerless_blocker_candidate(
    enriched: dict[str, CanonicalEvidence],
) -> None:
    pol005 = enriched["POL-005"]
    assert pol005.ownership.owner_team is None
    assert MissingEvidence.MISSING_OWNER.value in pol005.missing_evidence
    assert pol005.ownership.owner_confidence is ConfidenceLevel.LOW
    assert pol005.resource_facts.environment is EnvironmentType.UNKNOWN
    # Unknown side effects keep auto-remediation blocked later in routing.
    assert pol005.remediation_eligibility.downtime_risk is ImpactLevel.UNKNOWN
    assert MissingEvidence.MISSING_REPO_MAP.value in pol005.missing_evidence


def test_pol003_repo_mapped_without_source_drift(
    enriched: dict[str, CanonicalEvidence],
) -> None:
    pol003 = enriched["POL-003"]
    assert pol003.ownership.repo_path == "terraform/keyvault/governance/key_vault.tf"
    assert pol003.history.source_drift_likely is False
    assert pol003.history.source_confidence is ConfidenceLevel.HIGH
    # Dry-run candidate evidence from inventory remediation facts.
    assert pol003.remediation_eligibility.remediation_supported is True
    assert pol003.remediation_eligibility.permission_available is True
    assert pol003.remediation_eligibility.downtime_risk is ImpactLevel.NONE
    assert pol003.resource_facts.environment is EnvironmentType.DEVELOPMENT


def test_confidence_is_always_explicit(
    enriched: dict[str, CanonicalEvidence],
) -> None:
    for evidence in enriched.values():
        assert evidence.ownership.owner_confidence is not None
        assert evidence.history.source_confidence is not None


def test_defender_enrichment_sets_regulatory_control(
    enriched: dict[str, CanonicalEvidence],
) -> None:
    assert enriched["POL-004"].risk_signals.regulatory_control == "Network Security"
    assert enriched["POL-004"].risk_signals.severity.value == "Medium"
    # POL-005 has no Defender assessment; severity stays from raw evidence.
    assert enriched["POL-005"].risk_signals.severity.value == "Medium"


def test_verification_query_attached_to_all(
    enriched: dict[str, CanonicalEvidence],
) -> None:
    for evidence in enriched.values():
        assert evidence.verification.verification_query
        assert evidence.verification.expected_compliant_value
        assert (
            MissingEvidence.MISSING_VERIFICATION_QUERY.value
            not in evidence.missing_evidence
        )


def test_history_last_seen_tracks_evaluation(
    enriched: dict[str, CanonicalEvidence],
) -> None:
    pol001 = enriched["POL-001"]
    assert pol001.history.last_seen == pol001.policy_evidence.evaluated_at
    assert pol001.history.first_seen is not None
    assert pol001.history.previous_fix is not None


def test_no_connector_leaks_secrets(enriched: dict[str, CanonicalEvidence]) -> None:
    """Enriched evidence must contain no secret-like keys anywhere."""
    for evidence in enriched.values():
        dumped = evidence.model_dump(by_alias=True, mode="json")
        assert mask_sensitive(dumped) == dumped
