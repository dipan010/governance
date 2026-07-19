"""Deterministic risk scoring, safety blockers, and actionability.

Pure functions only (RULES.md 6.4): no I/O, no LLM. Risk and actionability
are separate views — a high-risk finding can still be blocked. Rule versions
are stored with every derived decision.
"""

from pydantic import BaseModel

from app.domain.enums import (
    BlockerCode,
    ConfidenceLevel,
    DataClassification,
    EnvironmentType,
    ImpactLevel,
    RiskBand,
    Severity,
)
from app.domain.evidence_schema import CanonicalEvidence

SCORE_RULE_VERSION = "risk-1.0.0"
ACTIONABILITY_RULE_VERSION = "actionability-1.0.0"

SCORE_CAP = 100
BLOCKER_WEIGHT = 10

SENSITIVE_DATA_CLASSES = {
    DataClassification.RESTRICTED,
    DataClassification.CONFIDENTIAL,
}

_SEVERITY_RANK = {
    Severity.CRITICAL: 4,
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
    Severity.UNKNOWN: 0,
}


class ScoreFactor(BaseModel):
    factor: str
    points: int


class RiskScore(BaseModel):
    score: int
    band: RiskBand
    factors: list[ScoreFactor]
    rule_version: str = SCORE_RULE_VERSION


class ActionabilityScore(BaseModel):
    score: int
    components: list[ScoreFactor]
    blocker_weight: int
    rule_version: str = ACTIONABILITY_RULE_VERSION


def severity_rank(severity: Severity) -> int:
    return _SEVERITY_RANK[severity]


def band_for_score(score: int) -> RiskBand:
    if score >= 80:
        return RiskBand.CRITICAL
    if score >= 60:
        return RiskBand.HIGH
    if score >= 40:
        return RiskBand.MEDIUM
    return RiskBand.LOW


def compute_blockers(evidence: CanonicalEvidence) -> list[BlockerCode]:
    """Safety blockers restrict actionability; they never lower risk and are
    always surfaced (RULES.md: blockers are first-class information)."""
    blockers: list[BlockerCode] = []
    if not evidence.resource_facts.resource_id:
        blockers.append(BlockerCode.MISSING_RESOURCE_IDENTITY)
    if evidence.ownership.owner_team is None:
        blockers.append(BlockerCode.MISSING_OWNER)
    if not evidence.policy_evidence.failure_reason:
        blockers.append(BlockerCode.MISSING_FAILURE_REASON)
    if not evidence.verification.verification_query:
        blockers.append(BlockerCode.MISSING_VERIFICATION_QUERY)
    if evidence.remediation_eligibility.downtime_risk is ImpactLevel.UNKNOWN:
        blockers.append(BlockerCode.UNKNOWN_DOWNTIME_RISK)
    if evidence.risk_signals.dependency_count is None:
        blockers.append(BlockerCode.UNKNOWN_DEPENDENCY_IMPACT)
    if evidence.remediation_eligibility.permission_available is None:
        blockers.append(BlockerCode.MISSING_PERMISSION_CHECK)
    if evidence.resource_facts.environment is EnvironmentType.PRODUCTION:
        blockers.append(BlockerCode.PRODUCTION_RUNTIME_CHANGE)
    return blockers


def compute_risk_score(evidence: CanonicalEvidence) -> RiskScore:
    factors: list[ScoreFactor] = []

    def add(condition: bool, factor: str, points: int) -> None:
        if condition:
            factors.append(ScoreFactor(factor=factor, points=points))

    signals = evidence.risk_signals
    add(
        signals.severity in (Severity.CRITICAL, Severity.HIGH),
        "high or critical severity",
        20,
    )
    add(
        evidence.resource_facts.environment is EnvironmentType.PRODUCTION,
        "production or shared platform resource",
        15,
    )
    add(
        signals.data_classification in SENSITIVE_DATA_CLASSES,
        f"sensitive data classification ({signals.data_classification.value})",
        20,
    )
    add(signals.internet_exposure is True, "internet exposure", 20)
    add(
        signals.identity_impact is True,
        "identity, secrets, or privileged impact",
        15,
    )
    add(
        evidence.history.recurrence_count > 0
        or evidence.history.previous_fix is not None,
        "recurrence: previous fix failed or violation reintroduced",
        15,
    )
    add(evidence.history.source_drift_likely is True, "source drift likely", 10)
    add(
        evidence.ownership.owner_confidence is ConfidenceLevel.HIGH,
        "strong owner confidence",
        5,
    )

    score = min(sum(f.points for f in factors), SCORE_CAP)
    return RiskScore(score=score, band=band_for_score(score), factors=factors)


def compute_actionability(
    evidence: CanonicalEvidence, blockers: list[BlockerCode]
) -> ActionabilityScore:
    components: list[ScoreFactor] = []

    def add(factor: str, points: int) -> None:
        if points:
            components.append(ScoreFactor(factor=factor, points=points))

    owner_points = {
        ConfidenceLevel.HIGH: 20,
        ConfidenceLevel.MEDIUM: 10,
    }.get(evidence.ownership.owner_confidence, 0)
    add("owner confidence", owner_points)

    source_points = {
        ConfidenceLevel.HIGH: 15,
        ConfidenceLevel.MEDIUM: 8,
    }.get(evidence.history.source_confidence, 0)
    add("source map confidence", source_points)

    if evidence.remediation_eligibility.remediation_supported is True:
        add("remediation supported", 15)
    if evidence.remediation_eligibility.permission_available is True:
        add("permission available", 15)
    if evidence.verification.verification_query:
        add("verification query ready", 15)

    blocker_weight = BLOCKER_WEIGHT * len(blockers)
    raw = sum(c.points for c in components) - blocker_weight
    return ActionabilityScore(
        score=max(0, min(raw, SCORE_CAP)),
        components=components,
        blocker_weight=blocker_weight,
    )
