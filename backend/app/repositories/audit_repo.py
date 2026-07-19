"""Audit repository: append-only event log with masking and prompt-run ID.

The repository exposes no update or delete operations, and a session-level
guard in app.db.models rejects any modification or deletion of stored audit
rows — append-only is enforced at the application level.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import mask_sensitive
from app.db.models import AuditEventRow
from app.domain.audit import AuditEventType, current_prompt_run_id


def _default_id_factory() -> str:
    return uuid.uuid4().hex


def _default_clock() -> datetime:
    return datetime.now(UTC)


class AuditRepository:
    def __init__(
        self,
        session: Session,
        id_factory: Callable[[], str] = _default_id_factory,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self._session = session
        self._id_factory = id_factory
        self._clock = clock

    def add_event(
        self,
        violation_id: str,
        event_type: AuditEventType,
        payload: dict[str, Any],
        correlation_id: str | None = None,
        action_id: str | None = None,
        evidence_packet: str | None = None,
    ) -> AuditEventRow:
        row = AuditEventRow(
            id=self._id_factory(),
            violation_id=violation_id,
            event_type=event_type.value,
            correlation_id=correlation_id or self._id_factory(),
            action_id=action_id,
            prompt_run_id=current_prompt_run_id(),
            evidence_packet=evidence_packet,
            payload=mask_sensitive(payload),
            created_at=self._clock(),
        )
        self._session.add(row)
        return row

    def list_for(self, violation_id: str) -> list[AuditEventRow]:
        stmt = (
            select(AuditEventRow)
            .where(AuditEventRow.violation_id == violation_id)
            .order_by(AuditEventRow.created_at, AuditEventRow.id)
        )
        return list(self._session.scalars(stmt))
