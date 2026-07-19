"""Core Policy Compliance Agent normalization tests."""

from typing import Any

from sqlalchemy.orm import Session

from app.agents.core_policy_agent import (
    normalize_defender_finding,
    normalize_policy_finding,
    stable_violation_id,
)
from app.domain.enums import ComplianceState, Severity
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.validation import MissingEvidence
from app.repositories.violations_repo import ViolationsRepository


def test_all_five_fixture_findings_normalize(policy_fixture: dict[str, Any]) -> None:
    results = [normalize_policy_finding(f) for f in policy_fixture["findings"]]
    assert len(results) == 5
    ids = [r.evidence.violation_id for r in results]
    assert ids == ["POL-001", "POL-002", "POL-003", "POL-004", "POL-005"]
    for result in results:
        # Round-trips through the canonical schema without loss.
        dumped = result.evidence.model_dump(by_alias=True, mode="json")
        assert CanonicalEvidence.model_validate(dumped) == result.evidence
        assert (
            result.evidence.policy_evidence.compliance_state
            is ComplianceState.NON_COMPLIANT
        )


def test_stable_violation_id_is_deterministic() -> None:
    a = stable_violation_id(None, "p1", "/subscriptions/S/x", "2026-07-18T10:00:00Z")
    b = stable_violation_id(None, "p1", "/SUBSCRIPTIONS/s/X", "2026-07-18T10:00:00Z")
    c = stable_violation_id(None, "p2", "/subscriptions/S/x", "2026-07-18T10:00:00Z")
    assert a == b  # resource casing does not change identity
    assert a != c
    assert stable_violation_id("POL-001", "p1", "r", "t") == "POL-001"


def test_resource_group_and_subscription_parsed(
    policy_fixture: dict[str, Any],
) -> None:
    result = normalize_policy_finding(policy_fixture["findings"][0])
    facts = result.evidence.resource_facts
    assert facts.resource_group == "ghq-3-squad3-cloudgov-dev-rg"
    assert facts.subscription_id == "1a2b3c4d-0000-4000-8000-000000000001"


def test_incomplete_record_is_flagged_not_discarded() -> None:
    result = normalize_policy_finding({"findingRef": "POL-BAD"})
    evidence = result.evidence
    assert evidence.violation_id == "POL-BAD"
    assert evidence.risk_signals.severity is Severity.UNKNOWN
    flags = set(evidence.missing_evidence)
    assert MissingEvidence.MISSING_RESOURCE_IDENTITY.value in flags
    assert MissingEvidence.MISSING_SEVERITY.value in flags
    assert MissingEvidence.MISSING_FAILURE_REASON.value in flags


def test_enrichment_gaps_flagged_at_ingest(policy_fixture: dict[str, Any]) -> None:
    result = normalize_policy_finding(policy_fixture["findings"][0])
    flags = set(result.evidence.missing_evidence)
    assert MissingEvidence.MISSING_OWNER.value in flags
    assert MissingEvidence.MISSING_REPO_MAP.value in flags
    assert MissingEvidence.MISSING_VERIFICATION_QUERY.value in flags


def test_defender_record_maps_to_canonical() -> None:
    result = normalize_defender_finding(
        {
            "recommendationId": "defender-storage-secure-transfer",
            "recommendation": "Secure transfer to storage accounts should be enabled",
            "state": "Unhealthy",
            "description": "supportsHttpsTrafficOnly is false",
            "assessedAt": "2026-07-18T09:00:00+00:00",
            "resourceId": "/subscriptions/s/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/st1",
            "severity": "High",
        }
    )
    evidence = result.evidence
    assert evidence.policy_evidence.policy_id == "defender-storage-secure-transfer"
    assert evidence.policy_evidence.compliance_state is ComplianceState.NON_COMPLIANT
    assert (
        evidence.policy_evidence.failure_reason == "supportsHttpsTrafficOnly is false"
    )
    assert evidence.risk_signals.severity is Severity.HIGH


def test_raw_evidence_preserved_and_reingest_idempotent(
    db_session: Session, policy_fixture: dict[str, Any]
) -> None:
    repo = ViolationsRepository(db_session)
    for record in policy_fixture["findings"]:
        raw_id = repo.add_raw_finding("policy", "ingest-1", record)
        repo.upsert_violation(normalize_policy_finding(record).evidence, raw_id)
    db_session.flush()
    assert len(repo.list_violations()) == 5

    # Re-ingest the same batch: raw rows append, violations stay stable.
    for record in policy_fixture["findings"]:
        raw_id = repo.add_raw_finding("policy", "ingest-2", record)
        repo.upsert_violation(normalize_policy_finding(record).evidence, raw_id)
    db_session.flush()
    assert len(repo.list_violations()) == 5

    row = repo.get_violation("POL-001")
    assert row is not None
    raw = repo.get_raw_finding(row.raw_finding_id)
    assert raw is not None
    assert raw.payload == policy_fixture["findings"][0]
