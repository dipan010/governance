"""Verification Engine: owns closure eligibility (RULES.md 4.6).

Re-checks resource state (fixture-backed for MVP), compares before/after
against the expected compliant value, blocks closure without proof, and
writes an audit event for every verified fix.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from app.connectors.storage import EvidencePacketStore
from app.connectors.verification_source import VerificationSourceConnector
from app.domain.audit import AuditEventType
from app.domain.enums import ActionStatus, VerificationResult
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.verification import (
    VERIFICATION_RULE_VERSION,
    VerificationOutcome,
    ensure_closable,
    evaluate_after_state,
)
from app.repositories.audit_repo import AuditRepository


def _default_clock() -> datetime:
    return datetime.now(UTC)


class VerificationEngine:
    def __init__(
        self,
        verification_source: VerificationSourceConnector,
        audit: AuditRepository,
        packets: EvidencePacketStore,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self._source = verification_source
        self._audit = audit
        self._packets = packets
        self._clock = clock

    def verify(
        self,
        evidence: CanonicalEvidence,
        after_state_override: dict[str, Any] | None = None,
    ) -> VerificationOutcome:
        """Run (or simulate) verification. The override stands in for a live
        re-query result; the fixture after-state is the MVP default."""
        verification = evidence.verification
        after_state = after_state_override
        if after_state is None:
            template = self._source.get_template(
                evidence.violation_id, evidence.resource_facts.resource_id
            )
            if template is not None:
                after_state = template.after_state

        result, details, next_action = evaluate_after_state(
            after_state, verification.expected_compliant_value
        )

        verification.after_state = after_state
        verification.verification_result = result
        verification.next_action = next_action
        verification.verification_rule_version = VERIFICATION_RULE_VERSION

        if result is VerificationResult.COMPLIANT:
            evidence.action_state.action_status = ActionStatus.VERIFIED
            self._record_audit_event(evidence, details)
        elif evidence.action_state.action_status is ActionStatus.CLOSED:
            # A failed re-check must never leave a closed item closed.
            evidence.action_state.action_status = ActionStatus.VERIFICATION_PENDING

        return VerificationOutcome(
            violation_id=evidence.violation_id,
            result=result,
            before_state=verification.before_state,
            after_state=after_state,
            verification_query=verification.verification_query,
            expected_compliant_value=verification.expected_compliant_value,
            details=details,
            next_action=next_action,
            checked_at=self._clock(),
        )

    def close(self, evidence: CanonicalEvidence) -> None:
        """Close only with after-state proof; raises ClosureBlockedError."""
        ensure_closable(evidence)
        evidence.action_state.action_status = ActionStatus.CLOSED
        self._record_audit_event(
            evidence,
            [f"{evidence.violation_id} closed with after-state proof"],
            event_type=AuditEventType.VIOLATION_CLOSED,
        )

    def _record_audit_event(
        self,
        evidence: CanonicalEvidence,
        details: list[str],
        event_type: AuditEventType = AuditEventType.VERIFICATION_COMPLETED,
    ) -> None:
        packet = {
            "violationId": evidence.violation_id,
            "result": evidence.verification.verification_result.value,
            "beforeState": evidence.verification.before_state,
            "afterState": evidence.verification.after_state,
            "verificationQuery": evidence.verification.verification_query,
            "expectedCompliantValue": (evidence.verification.expected_compliant_value),
            "details": details,
            "ruleVersion": VERIFICATION_RULE_VERSION,
        }
        timestamp = self._clock().strftime("%Y%m%dT%H%M%S%f")
        location = self._packets.put(
            evidence.violation_id, f"{event_type.value}-{timestamp}", packet
        )
        self._audit.add_event(
            violation_id=evidence.violation_id,
            event_type=event_type,
            payload=packet,
            action_id=evidence.action_state.remediation_task_id
            or evidence.action_state.ticket_id,
            evidence_packet=location,
        )
