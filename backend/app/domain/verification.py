"""Deterministic verification rules.

Compares after-state to the expected compliant value expression and decides
closure eligibility. No item closes without after-state proof (RULES.md 2.5).
"""

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import VerificationResult
from app.domain.evidence_schema import CanonicalEvidence

VERIFICATION_RULE_VERSION = "verification-1.0.0"

# Clauses like: publicNetworkAccess == Disabled, enablePurgeProtection == true
_CLAUSE_RE = re.compile(r"([\w.]+)\s*==\s*([\w.\-]+)")

NEXT_ACTION_NOT_RUN = (
    "Re-run the verification query after the approved change has deployed; "
    "no after-state is available yet"
)
NEXT_ACTION_COMPLIANT = (
    "Close the violation; store the evidence packet with before/after state"
)


class VerificationOutcome(BaseModel):
    violation_id: str
    result: VerificationResult
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    verification_query: str | None
    expected_compliant_value: str | None
    details: list[str] = Field(default_factory=list)
    next_action: str
    checked_at: datetime
    rule_version: str = VERIFICATION_RULE_VERSION


class ClosureBlockedError(Exception):
    def __init__(self, reason: str, next_action: str) -> None:
        self.reason = reason
        self.next_action = next_action
        super().__init__(reason)


def parse_expected_clauses(expression: str | None) -> list[tuple[str, str]]:
    if not expression:
        return []
    return _CLAUSE_RE.findall(expression)


def evaluate_after_state(
    after_state: dict[str, Any] | None,
    expected_expression: str | None,
) -> tuple[VerificationResult, list[str], str]:
    """Pure evaluation of an after-state against the expected expression.
    Returns (result, detail lines, next action)."""
    if after_state is None:
        return (VerificationResult.NOT_RUN, ["No after-state"], NEXT_ACTION_NOT_RUN)

    clauses = parse_expected_clauses(expected_expression)
    if not clauses:
        return (
            VerificationResult.FAILED,
            [
                "Expected compliant value is not machine-checkable; "
                "manual verification required"
            ],
            "Verify manually against the expected compliant value; "
            "do not close until confirmed",
        )

    details: list[str] = []
    failed = False
    for prop, expected in clauses:
        actual = after_state.get(prop)
        if actual is None or str(actual).lower() != expected.lower():
            failed = True
            details.append(f"{prop}: expected '{expected}', found '{actual}'")
        else:
            details.append(f"{prop}: '{actual}' matches expected '{expected}'")

    if failed:
        mismatches = "; ".join(d for d in details if "expected" in d and "found" in d)
        return (
            VerificationResult.FAILED,
            details,
            f"Resource is still non-compliant ({mismatches}). Re-apply the "
            "approved fix or escalate to the owner; the item stays open",
        )
    return (VerificationResult.COMPLIANT, details, NEXT_ACTION_COMPLIANT)


def ensure_closable(evidence: CanonicalEvidence) -> None:
    """Raise unless the violation has after-state proof of compliance.
    Ticket or PR creation alone never satisfies this."""
    verification = evidence.verification
    if verification.verification_result is not VerificationResult.COMPLIANT:
        raise ClosureBlockedError(
            reason=(
                f"{evidence.violation_id} cannot close: verification result "
                f"is {verification.verification_result.value}; closure "
                "requires after-state proof (RULES.md 2.5)"
            ),
            next_action=verification.next_action or NEXT_ACTION_NOT_RUN,
        )
    if verification.after_state is None:
        raise ClosureBlockedError(
            reason=f"{evidence.violation_id} cannot close: no after-state stored",
            next_action=NEXT_ACTION_NOT_RUN,
        )
