"""Audit domain: event types, prompt-run tracking, append-only error.

Every major decision produces an audit event with a correlation ID, the
prompt run that produced the behavior, and (where applicable) an action ID
and evidence packet location. Payloads are masked before storage — no
secrets in audit logs (RULES.md 9.5, 9.9).
"""

import json
from enum import StrEnum
from functools import lru_cache

from app.core.config import get_settings


class AuditEventType(StrEnum):
    FINDING_INGESTED = "finding.ingested"
    FINDING_NORMALIZED = "finding.normalized"
    FINDING_ENRICHED = "finding.enriched"
    SIGNALS_DETECTED = "focused_agent.signals_detected"
    RISK_SCORED = "risk.scored"
    ROUTE_PLANNED = "route.planned"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_DEFERRED = "approval.deferred"
    ARTIFACT_GENERATED = "artifact.generated"
    VERIFICATION_COMPLETED = "verification.completed"
    VIOLATION_CLOSED = "violation.closed"
    VIOLATION_BLOCKED = "violation.blocked"
    EXCEPTION_CREATED = "exception.created"


class AppendOnlyViolationError(RuntimeError):
    """Raised when code attempts to modify or delete a stored audit event."""


@lru_cache
def current_prompt_run_id() -> str:
    """The prompt run that produced the current behavior, from state.json."""
    state_path = get_settings().fixtures_dir.parents[1] / "state.json"
    try:
        prompt_id: str = json.loads(state_path.read_text())["currentPromptId"]
    except (OSError, KeyError, ValueError):
        return "unknown"
    return prompt_id
