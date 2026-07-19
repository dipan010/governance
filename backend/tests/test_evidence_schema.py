"""Schema validation tests for the canonical evidence schema and P02 fixtures."""

import csv
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.domain.enums import (
    ComplianceState,
    FocusedSignal,
    RoutePath,
    Severity,
    VerificationResult,
)
from app.domain.evidence_schema import (
    SCHEMA_VERSION,
    CanonicalEvidence,
    PolicyEvidence,
    ResourceFacts,
)

FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures"

REQUIRED_RAW_FIELDS = [
    "policyId",
    "resourceId",
    "complianceState",
    "failureReason",
    "evaluatedAt",
]


def load_findings() -> list[dict[str, Any]]:
    payload = json.loads((FIXTURES / "policy_findings.json").read_text())
    findings: list[dict[str, Any]] = payload["findings"]
    return findings


def load_owner_map() -> dict[str, dict[str, str]]:
    with (FIXTURES / "owner_map.csv").open() as fh:
        return {row["resourceId"].lower(): row for row in csv.DictReader(fh)}


def make_minimal_evidence(**overrides: object) -> CanonicalEvidence:
    base: dict[str, object] = {
        "violationId": "POL-001",
        "policyEvidence": {
            "policyId": "storage-public-network-disabled",
            "policyName": "Storage accounts should restrict public network access",
            "complianceState": "NonCompliant",
            "failureReason": "publicNetworkAccess is Enabled",
            "evaluatedAt": "2026-07-18T10:00:00+00:00",
        },
        "resourceFacts": {
            "resourceId": "/subscriptions/x/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/StPayProd01",
        },
    }
    base.update(overrides)
    return CanonicalEvidence.model_validate(base)


class TestCanonicalSchema:
    def test_minimal_evidence_validates(self) -> None:
        evidence = make_minimal_evidence()
        assert evidence.schema_version == SCHEMA_VERSION
        assert (
            evidence.policy_evidence.compliance_state is ComplianceState.NON_COMPLIANT
        )
        assert evidence.verification.verification_result is VerificationResult.NOT_RUN

    def test_missing_required_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CanonicalEvidence.model_validate({"violationId": "POL-999"})
        with pytest.raises(ValidationError):
            PolicyEvidence.model_validate({"policyId": "p", "policyName": "n"})
        with pytest.raises(ValidationError):
            ResourceFacts.model_validate({})

    def test_invalid_enum_values_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_minimal_evidence(
                policyEvidence={
                    "policyId": "p",
                    "policyName": "n",
                    "complianceState": "SortOfCompliant",
                    "evaluatedAt": "2026-07-18T10:00:00+00:00",
                }
            )
        with pytest.raises(ValidationError):
            make_minimal_evidence(riskSignals={"severity": "Catastrophic"})
        with pytest.raises(ValidationError):
            make_minimal_evidence(decision={"recommendedPath": "just_fix_it"})

    def test_risk_score_bounds_enforced(self) -> None:
        with pytest.raises(ValidationError):
            make_minimal_evidence(decision={"riskScore": 101})

    def test_unknown_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_minimal_evidence(surpriseField=True)

    def test_camel_case_round_trip(self) -> None:
        evidence = make_minimal_evidence()
        dumped = evidence.model_dump(by_alias=True, mode="json")
        assert "policyEvidence" in dumped
        assert "failureReason" in dumped["policyEvidence"]
        assert CanonicalEvidence.model_validate(dumped) == evidence

    def test_resource_id_normalized_for_lookup_preserves_display(self) -> None:
        evidence = make_minimal_evidence()
        assert "StPayProd01" in evidence.resource_facts.resource_id
        assert evidence.resource_facts.resource_id_normalized.endswith("stpayprod01")

    def test_route_and_signal_enums_cover_spec(self) -> None:
        assert {r.value for r in RoutePath} >= {
            "source_pr_plus_change_ticket",
            "remediation_dry_run",
            "owner_ticket_or_change_request",
            "time_bound_exception",
            "blocked_manual_review",
            "escalation",
            "observe",
            "invalid_finding",
        }
        assert {s.value for s in FocusedSignal} >= {
            "storage_public_network_access",
            "broad_source_cidr",
            "sensitive_port_exposed",
            "source_drift_likely",
        }


class TestFixtures:
    def test_five_findings_with_required_fields(self) -> None:
        findings = load_findings()
        assert len(findings) >= 5
        for finding in findings:
            for field in REQUIRED_RAW_FIELDS:
                assert finding.get(field), f"{finding['findingRef']} missing {field}"
            assert finding["complianceState"] == ComplianceState.NON_COMPLIANT.value
            assert Severity(finding["severity"])

    def test_expected_finding_refs_present(self) -> None:
        refs = {f["findingRef"] for f in load_findings()}
        assert refs >= {"POL-001", "POL-002", "POL-003", "POL-004", "POL-005"}

    def test_at_least_one_finding_missing_owner(self) -> None:
        owner_map = load_owner_map()
        unowned = [
            f["findingRef"]
            for f in load_findings()
            if f["resourceId"].lower() not in owner_map
        ]
        assert "POL-005" in unowned

    def test_at_least_two_findings_have_repo_mappings(self) -> None:
        repo_map = json.loads((FIXTURES / "repo_map.json").read_text())
        mapped_ids = {m["resourceId"].lower() for m in repo_map["mappings"]}
        mapped_refs = [
            f["findingRef"]
            for f in load_findings()
            if f["resourceId"].lower() in mapped_ids
        ]
        assert len(mapped_refs) >= 2
        assert "POL-001" in mapped_refs

    def test_pol001_has_before_and_after_state(self) -> None:
        states = json.loads((FIXTURES / "before_after_state.json").read_text())
        by_ref = {s["findingRef"]: s for s in states["states"]}
        pol001 = by_ref["POL-001"]
        assert pol001["beforeState"]["publicNetworkAccess"] == "Enabled"
        assert pol001["afterState"]["publicNetworkAccess"] == "Disabled"
        assert pol001["verificationQuery"]
        assert pol001["expectedCompliantValue"]

    def test_every_finding_has_verification_entry(self) -> None:
        states = json.loads((FIXTURES / "before_after_state.json").read_text())
        state_refs = {s["findingRef"] for s in states["states"]}
        assert state_refs >= {f["findingRef"] for f in load_findings()}

    def test_owner_map_rows_have_owner_and_escalation(self) -> None:
        for row in load_owner_map().values():
            assert row["ownerTeam"]
            assert row["ownerEmail"]
            assert row["escalationPath"]

    def test_pol001_source_drift_mapping_has_bad_source_value(self) -> None:
        repo_map = json.loads((FIXTURES / "repo_map.json").read_text())
        storage = next(
            m for m in repo_map["mappings"] if "storageAccounts" in m["resourceId"]
        )
        prop = storage["properties"]["public_network_access_enabled"]
        assert prop["currentSourceValue"] != prop["expectedSourceValue"]
