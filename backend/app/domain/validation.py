"""Deterministic validation of raw findings and missing-evidence flagging.

Incomplete findings are never discarded (P04 requirement); they are ingested
with warnings and missing-evidence flags so routing can send them to
enrichment or manual review later.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class MissingEvidence(StrEnum):
    MISSING_RESOURCE_IDENTITY = "missing_resource_identity"
    MISSING_POLICY_ID = "missing_policy_id"
    MISSING_COMPLIANCE_STATE = "missing_compliance_state"
    MISSING_FAILURE_REASON = "missing_failure_reason"
    MISSING_EVALUATED_AT = "missing_evaluated_at"
    MISSING_SEVERITY = "missing_severity"
    MISSING_OWNER = "missing_owner"
    MISSING_REPO_MAP = "missing_repo_map"
    MISSING_VERIFICATION_QUERY = "missing_verification_query"


class IssueSeverity(StrEnum):
    WARNING = "warning"
    ERROR = "error"


class ValidationIssue(BaseModel):
    field: str
    code: MissingEvidence
    severity: IssueSeverity
    message: str


def _issue(
    field: str,
    code: MissingEvidence,
    message: str,
    severity: IssueSeverity = IssueSeverity.WARNING,
) -> ValidationIssue:
    return ValidationIssue(field=field, code=code, severity=severity, message=message)


def check_raw_policy_record(raw: dict[str, Any]) -> list[ValidationIssue]:
    """Flag missing required evidence on a raw policy/Defender record."""
    issues: list[ValidationIssue] = []
    if not raw.get("resourceId"):
        issues.append(
            _issue(
                "resourceId",
                MissingEvidence.MISSING_RESOURCE_IDENTITY,
                "Resource identity is missing; finding cannot be routed",
            )
        )
    if not raw.get("policyId"):
        issues.append(
            _issue(
                "policyId",
                MissingEvidence.MISSING_POLICY_ID,
                "Policy identity is missing",
            )
        )
    if not raw.get("complianceState"):
        issues.append(
            _issue(
                "complianceState",
                MissingEvidence.MISSING_COMPLIANCE_STATE,
                "Compliance state is missing; treated as Unknown",
            )
        )
    if not raw.get("failureReason"):
        issues.append(
            _issue(
                "failureReason",
                MissingEvidence.MISSING_FAILURE_REASON,
                "Failure reason is missing; route to enrichment",
            )
        )
    if not raw.get("evaluatedAt"):
        issues.append(
            _issue(
                "evaluatedAt",
                MissingEvidence.MISSING_EVALUATED_AT,
                "Evaluation timestamp is missing; ingestion time used",
            )
        )
    if not raw.get("severity"):
        issues.append(
            _issue(
                "severity",
                MissingEvidence.MISSING_SEVERITY,
                "Severity is missing; treated as Unknown",
            )
        )
    return issues


def enrichment_gap_flags() -> list[MissingEvidence]:
    """Evidence that ingestion can never provide; enrichment (P05) fills it."""
    return [
        MissingEvidence.MISSING_OWNER,
        MissingEvidence.MISSING_REPO_MAP,
        MissingEvidence.MISSING_VERIFICATION_QUERY,
    ]
