"""Core Policy Compliance Agent: deterministic ingestion and normalization.

Normalizes Azure Policy / Defender / fixture findings into the canonical
evidence schema, preserves raw evidence untouched, generates stable
violation IDs, and flags missing evidence. No scoring, no routing.
"""

import hashlib
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.domain.enums import (
    ComplianceState,
    EnvironmentType,
    PolicyEffect,
    Severity,
)
from app.domain.evidence_schema import (
    CanonicalEvidence,
    PolicyEvidence,
    ResourceFacts,
    RiskSignals,
)
from app.domain.validation import (
    ValidationIssue,
    check_raw_policy_record,
    enrichment_gap_flags,
)

UNKNOWN_POLICY_ID = "unknown-policy"

_DEFENDER_STATE_MAP = {
    "Unhealthy": ComplianceState.NON_COMPLIANT,
    "Healthy": ComplianceState.COMPLIANT,
}


class NormalizationResult(BaseModel):
    evidence: CanonicalEvidence
    issues: list[ValidationIssue]


def stable_violation_id(
    finding_ref: str | None, policy_id: str, resource_id: str, evaluated_at: str
) -> str:
    """Stable ID tied to policy, resource, and evaluation time (spec section 18).

    A supplied findingRef (e.g. POL-001) is honored for demo readability;
    otherwise the ID is a deterministic hash so re-ingestion is idempotent.
    """
    if finding_ref:
        return finding_ref
    digest = hashlib.sha256(
        f"{policy_id}|{resource_id.lower()}|{evaluated_at}".encode()
    ).hexdigest()
    return f"VIO-{digest[:12]}"


def _parse_segment(resource_id: str, key: str) -> str | None:
    parts = resource_id.split("/")
    lowered = [p.lower() for p in parts]
    if key.lower() in lowered:
        index = lowered.index(key.lower())
        if index + 1 < len(parts):
            return parts[index + 1]
    return None


def _coerce_enum[E](enum_cls: type[E], value: Any, default: E) -> E:
    try:
        return enum_cls(value)  # type: ignore[call-arg]
    except (ValueError, TypeError):
        return default


def _parse_evaluated_at(raw: dict[str, Any], now: datetime) -> datetime:
    value = raw.get("evaluatedAt")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return now
    return now


def normalize_policy_finding(
    raw: dict[str, Any], now: datetime | None = None
) -> NormalizationResult:
    """Normalize one raw Azure Policy (or fixture) record. Raw is not mutated."""
    now = now or datetime.now(UTC)
    issues = check_raw_policy_record(raw)

    policy_id = str(raw.get("policyId") or UNKNOWN_POLICY_ID)
    resource_id = str(raw.get("resourceId") or "")
    evaluated_at = _parse_evaluated_at(raw, now)

    evidence = CanonicalEvidence(
        violation_id=stable_violation_id(
            raw.get("findingRef"), policy_id, resource_id, evaluated_at.isoformat()
        ),
        policy_evidence=PolicyEvidence(
            policy_id=policy_id,
            policy_name=str(raw.get("policyName") or policy_id),
            assignment_id=raw.get("assignmentId"),
            initiative=raw.get("initiative"),
            compliance_state=_coerce_enum(
                ComplianceState, raw.get("complianceState"), ComplianceState.UNKNOWN
            ),
            failure_reason=raw.get("failureReason"),
            evaluated_at=evaluated_at,
        ),
        resource_facts=ResourceFacts(
            resource_id=resource_id,
            resource_type=raw.get("resourceType"),
            subscription_id=_parse_segment(resource_id, "subscriptions"),
            resource_group=_parse_segment(resource_id, "resourceGroups"),
            environment=EnvironmentType.UNKNOWN,
        ),
        risk_signals=RiskSignals(
            severity=_coerce_enum(Severity, raw.get("severity"), Severity.UNKNOWN),
            regulatory_control=raw.get("regulatoryControl"),
        ),
        missing_evidence=[issue.code.value for issue in issues]
        + [flag.value for flag in enrichment_gap_flags()],
    )
    effect = raw.get("effect")
    if effect is not None:
        evidence.remediation_eligibility.policy_effect = _coerce_enum(
            PolicyEffect, effect, PolicyEffect.AUDIT
        )
    return NormalizationResult(evidence=evidence, issues=issues)


def normalize_defender_finding(
    raw: dict[str, Any], now: datetime | None = None
) -> NormalizationResult:
    """Normalize a Defender for Cloud recommendation into the same schema."""
    state = raw.get("complianceState") or _DEFENDER_STATE_MAP.get(
        str(raw.get("state")), ComplianceState.UNKNOWN
    )
    translated: dict[str, Any] = {
        **raw,
        "policyId": raw.get("policyId") or raw.get("recommendationId"),
        "policyName": raw.get("policyName") or raw.get("recommendation"),
        "complianceState": state,
        "failureReason": raw.get("failureReason") or raw.get("description"),
        "evaluatedAt": raw.get("evaluatedAt") or raw.get("assessedAt"),
    }
    return normalize_policy_finding(translated, now=now)
