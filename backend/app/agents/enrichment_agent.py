"""Enrichment agent: attaches resource facts, owner, repo map, Defender
severity, history, and verification query to normalized violations.

Deterministic only. Confidence is always explicit: owner confidence is High
for an exact resource match, Medium for an app-tag inference, Low when no
owner is found; source confidence comes from the repo mapping or stays
Unknown when the resource is unmapped.
"""

from datetime import datetime

from app.connectors.defender import DefenderConnector
from app.connectors.owner_map import OwnerMapConnector, OwnerRecord
from app.connectors.repo_map import RepoMapConnector
from app.connectors.resource_inventory import ResourceInventoryConnector
from app.connectors.verification_source import VerificationSourceConnector
from app.domain.enums import (
    ConfidenceLevel,
    DataClassification,
    EnvironmentType,
    ImpactLevel,
    Severity,
    coerce_enum,
)
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.validation import MissingEvidence


class EnrichmentAgent:
    def __init__(
        self,
        inventory: ResourceInventoryConnector,
        owners: OwnerMapConnector,
        repos: RepoMapConnector,
        defender: DefenderConnector,
        verification: VerificationSourceConnector,
    ) -> None:
        self._inventory = inventory
        self._owners = owners
        self._repos = repos
        self._defender = defender
        self._verification = verification

    def enrich(self, evidence: CanonicalEvidence) -> CanonicalEvidence:
        """Enrich in place and return the evidence. Raw evidence is untouched."""
        resource_id = evidence.resource_facts.resource_id
        if resource_id:
            self._apply_inventory(evidence, resource_id)
            self._apply_owner(evidence, resource_id)
            self._apply_repo_map(evidence, resource_id)
            self._apply_defender(evidence, resource_id)
            self._apply_verification(evidence, resource_id)
        evidence.history.last_seen = evidence.policy_evidence.evaluated_at
        return evidence

    def _clear_flag(self, evidence: CanonicalEvidence, flag: MissingEvidence) -> None:
        if flag.value in evidence.missing_evidence:
            evidence.missing_evidence.remove(flag.value)

    def _apply_inventory(self, evidence: CanonicalEvidence, resource_id: str) -> None:
        record = self._inventory.get_resource(resource_id)
        if record is None:
            return
        facts = evidence.resource_facts
        facts.location = record.location or facts.location
        facts.tags = record.tags or facts.tags
        facts.environment = coerce_enum(
            EnvironmentType, record.environment, EnvironmentType.UNKNOWN
        )
        facts.production_criticality = record.production_criticality

        signals = evidence.risk_signals
        signals.data_classification = coerce_enum(
            DataClassification, record.data_classification, DataClassification.UNKNOWN
        )
        signals.internet_exposure = record.internet_exposure
        signals.identity_impact = record.identity_impact
        signals.dependency_count = record.dependency_count

        if record.remediation is not None:
            elig = evidence.remediation_eligibility
            elig.remediation_supported = record.remediation.remediation_supported
            elig.required_permission = record.remediation.required_permission
            elig.permission_available = record.remediation.permission_available
            elig.restart_risk = coerce_enum(
                ImpactLevel, record.remediation.restart_risk, ImpactLevel.UNKNOWN
            )
            elig.downtime_risk = coerce_enum(
                ImpactLevel, record.remediation.downtime_risk, ImpactLevel.UNKNOWN
            )
            elig.cost_impact = coerce_enum(
                ImpactLevel, record.remediation.cost_impact, ImpactLevel.UNKNOWN
            )

        if record.history is not None:
            history = evidence.history
            if record.history.first_seen:
                history.first_seen = datetime.fromisoformat(record.history.first_seen)
            history.previous_fix = record.history.previous_fix
            history.recurrence_count = record.history.recurrence_count

    def _set_owner(
        self, evidence: CanonicalEvidence, record: OwnerRecord, confidence: str
    ) -> None:
        ownership = evidence.ownership
        ownership.owner_team = record.owner_team
        ownership.owner_email = record.owner_email
        ownership.support_group = record.support_group
        ownership.business_app = record.business_app
        ownership.owner_confidence = ConfidenceLevel(confidence)
        self._clear_flag(evidence, MissingEvidence.MISSING_OWNER)

    def _apply_owner(self, evidence: CanonicalEvidence, resource_id: str) -> None:
        exact = self._owners.get_owner(resource_id)
        if exact is not None:
            self._set_owner(evidence, exact, ConfidenceLevel.HIGH.value)
            return
        app_tag = evidence.resource_facts.tags.get("app")
        if app_tag:
            inferred = self._owners.find_owner_by_app(app_tag)
            if inferred is not None:
                self._set_owner(evidence, inferred, ConfidenceLevel.MEDIUM.value)
                return
        # Owner gap stays visible: flag remains, confidence explicit.
        evidence.ownership.owner_confidence = ConfidenceLevel.LOW

    def _apply_repo_map(self, evidence: CanonicalEvidence, resource_id: str) -> None:
        mapping = self._repos.get_mapping(resource_id)
        if mapping is None:
            evidence.history.source_confidence = ConfidenceLevel.UNKNOWN
            return
        ownership = evidence.ownership
        ownership.repo_url = mapping.repo_url
        ownership.repo_path = mapping.repo_path
        ownership.code_owner = mapping.code_owner
        evidence.history.source_confidence = coerce_enum(
            ConfidenceLevel, mapping.source_confidence, ConfidenceLevel.UNKNOWN
        )
        evidence.history.source_drift_likely = bool(mapping.drifted_properties())
        self._clear_flag(evidence, MissingEvidence.MISSING_REPO_MAP)

    def _apply_defender(self, evidence: CanonicalEvidence, resource_id: str) -> None:
        assessment = self._defender.get_assessment(
            resource_id, evidence.policy_evidence.policy_id
        )
        if assessment is None:
            return
        # Defender is the severity authority when it has assessed the resource.
        evidence.risk_signals.severity = coerce_enum(
            Severity, assessment.severity, evidence.risk_signals.severity
        )
        if assessment.regulatory_control:
            evidence.risk_signals.regulatory_control = assessment.regulatory_control
        self._clear_flag(evidence, MissingEvidence.MISSING_SEVERITY)

    def _apply_verification(
        self, evidence: CanonicalEvidence, resource_id: str
    ) -> None:
        template = self._verification.get_template(evidence.violation_id, resource_id)
        if template is None:
            return
        verification = evidence.verification
        verification.verification_query = template.verification_query
        verification.expected_compliant_value = template.expected_compliant_value
        verification.before_state = template.before_state
        self._clear_flag(evidence, MissingEvidence.MISSING_VERIFICATION_QUERY)
