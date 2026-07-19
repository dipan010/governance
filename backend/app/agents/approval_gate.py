"""Approval Gate agent: owns approval enforcement (RULES.md 4.5).

No cloud, source, network, identity, or production-affecting action executes
without an approved approval record. Rejections and deferrals persist with
their reason.
"""

from collections.abc import Callable
from datetime import UTC, datetime

from app.db.models import ApprovalRow
from app.domain.approval import (
    ActionKind,
    ApprovalGateError,
    build_approval_payload,
    validate_action,
)
from app.domain.enums import ActionStatus, ApprovalState
from app.domain.evidence_schema import CanonicalEvidence
from app.repositories.approvals_repo import ApprovalsRepository
from app.repositories.violations_repo import ViolationsRepository

_DECISION_TO_STATE = {
    "approve": ApprovalState.APPROVED,
    "reject": ApprovalState.REJECTED,
    "defer": ApprovalState.DEFERRED,
}


def _default_clock() -> datetime:
    return datetime.now(UTC)


class ApprovalGate:
    def __init__(
        self,
        approvals: ApprovalsRepository,
        violations: ViolationsRepository,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self._approvals = approvals
        self._violations = violations
        self._clock = clock

    def request(self, evidence: CanonicalEvidence, raw_finding_id: str) -> ApprovalRow:
        payload = build_approval_payload(evidence, self._clock())
        row = self._approvals.add_request(
            violation_id=evidence.violation_id,
            approver_role=payload.approver_role,
            payload=payload.model_dump(by_alias=True, mode="json"),
        )
        evidence.action_state.action_status = ActionStatus.AWAITING_APPROVAL
        self._violations.upsert_violation(evidence, raw_finding_id)
        return row

    def decide(
        self,
        evidence: CanonicalEvidence,
        raw_finding_id: str,
        decision: str,
        approver: str,
        reason: str | None,
    ) -> ApprovalRow:
        state = _DECISION_TO_STATE.get(decision)
        if state is None:
            raise ApprovalGateError(
                f"Unknown approval decision '{decision}'",
                "approval decisions are approve, reject, or defer",
            )
        if state in (ApprovalState.REJECTED, ApprovalState.DEFERRED) and not reason:
            raise ApprovalGateError(
                f"A reason is required to {decision} an approval",
                "RULES.md: rejected/deferred approvals persist with reason",
            )
        row = self._approvals.latest_for(evidence.violation_id)
        if row is None:
            raise ApprovalGateError(
                f"No approval request exists for {evidence.violation_id}",
                "request approval before deciding",
            )

        self._approvals.decide(row, state.value, approver, reason)
        if state is ApprovalState.APPROVED:
            evidence.action_state.approver = approver
            evidence.action_state.approved_at = self._clock()
            evidence.action_state.action_status = ActionStatus.APPROVED
        elif state is ApprovalState.REJECTED:
            evidence.action_state.action_status = ActionStatus.REJECTED
        # Deferred keeps AwaitingApproval.
        self._violations.upsert_violation(evidence, raw_finding_id)
        return row

    def approval_state(self, violation_id: str) -> ApprovalState:
        row = self._approvals.latest_for(violation_id)
        if row is None:
            return ApprovalState.NOT_REQUESTED
        return ApprovalState(row.status)

    def ensure_allowed(self, evidence: CanonicalEvidence, kind: ActionKind) -> None:
        """The single enforcement point before any action executes."""
        validate_action(evidence, kind, self.approval_state(evidence.violation_id))
