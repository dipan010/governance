"""Canonical evidence schema (Pydantic v2).

This is the stable contract between agents (RULES.md section 8). JSON uses
camelCase field names; Python uses snake_case with camelCase aliases.
Schema changes require a version bump.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.domain.enums import (
    ActionStatus,
    BlockerCode,
    ComplianceState,
    ConfidenceLevel,
    DataClassification,
    EnvironmentType,
    FocusedSignal,
    ImpactLevel,
    PolicyEffect,
    RiskBand,
    RoutePath,
    Severity,
    VerificationResult,
)

SCHEMA_VERSION = "1.0.0"


class CamelModel(BaseModel):
    """Base model: camelCase JSON aliases, strict extras policy."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        use_enum_values=False,
    )


class PolicyEvidence(CamelModel):
    policy_id: str
    policy_name: str
    assignment_id: str | None = None
    initiative: str | None = None
    compliance_state: ComplianceState
    failure_reason: str | None = None
    evaluated_at: datetime


class ResourceFacts(CamelModel):
    resource_id: str
    resource_type: str | None = None
    subscription_id: str | None = None
    resource_group: str | None = None
    location: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    environment: EnvironmentType = EnvironmentType.UNKNOWN
    production_criticality: str | None = None

    @property
    def resource_id_normalized(self) -> str:
        """Lowercase resource ID for lookups; original casing kept for display."""
        return self.resource_id.lower()


class RiskSignals(CamelModel):
    severity: Severity = Severity.UNKNOWN
    data_classification: DataClassification = DataClassification.UNKNOWN
    internet_exposure: bool | None = None
    identity_impact: bool | None = None
    dependency_count: int | None = None
    regulatory_control: str | None = None
    focused_signals: list[FocusedSignal] = Field(default_factory=list)


class Ownership(CamelModel):
    owner_team: str | None = None
    owner_email: str | None = None
    support_group: str | None = None
    business_app: str | None = None
    repo_url: str | None = None
    repo_path: str | None = None
    code_owner: str | None = None
    owner_confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN


class RemediationEligibility(CamelModel):
    policy_effect: PolicyEffect | None = None
    remediation_supported: bool | None = None
    required_permission: str | None = None
    permission_available: bool | None = None
    restart_risk: ImpactLevel = ImpactLevel.UNKNOWN
    downtime_risk: ImpactLevel = ImpactLevel.UNKNOWN
    cost_impact: ImpactLevel = ImpactLevel.UNKNOWN


class History(CamelModel):
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    previous_fix: str | None = None
    recurrence_count: int = 0
    source_drift_likely: bool | None = None
    source_confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN


class Decision(CamelModel):
    risk_score: int | None = Field(default=None, ge=0, le=100)
    risk_band: RiskBand | None = None
    score_factors: list[str] = Field(default_factory=list)
    blockers: list[BlockerCode] = Field(default_factory=list)
    recommended_path: RoutePath | None = None
    approval_required: bool | None = None
    approver_role: str | None = None
    rollback_or_next_action: str | None = None
    score_rule_version: str | None = None
    route_rule_version: str | None = None


class ActionState(CamelModel):
    approver: str | None = None
    approved_at: datetime | None = None
    ticket_id: str | None = None
    pr_url: str | None = None
    remediation_task_id: str | None = None
    action_status: ActionStatus = ActionStatus.OPEN


class Verification(CamelModel):
    before_state: dict[str, object] | None = None
    after_state: dict[str, object] | None = None
    verification_query: str | None = None
    expected_compliant_value: str | None = None
    verification_result: VerificationResult = VerificationResult.NOT_RUN
    next_action: str | None = None
    verification_rule_version: str | None = None


class CanonicalEvidence(CamelModel):
    """One normalized violation. The stable contract between all agents."""

    schema_version: str = SCHEMA_VERSION
    violation_id: str
    policy_evidence: PolicyEvidence
    resource_facts: ResourceFacts
    risk_signals: RiskSignals = Field(default_factory=RiskSignals)
    ownership: Ownership = Field(default_factory=Ownership)
    remediation_eligibility: RemediationEligibility = Field(
        default_factory=RemediationEligibility
    )
    history: History = Field(default_factory=History)
    decision: Decision = Field(default_factory=Decision)
    action_state: ActionState = Field(default_factory=ActionState)
    verification: Verification = Field(default_factory=Verification)
    missing_evidence: list[str] = Field(default_factory=list)
