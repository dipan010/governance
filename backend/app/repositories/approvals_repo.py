"""Approvals repository: approval requests and decisions persist with reason."""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ApprovalRow


def _default_id_factory() -> str:
    return uuid.uuid4().hex


def _default_clock() -> datetime:
    return datetime.now(UTC)


class ApprovalsRepository:
    def __init__(
        self,
        session: Session,
        id_factory: Callable[[], str] = _default_id_factory,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self._session = session
        self._id_factory = id_factory
        self._clock = clock

    def add_request(
        self,
        violation_id: str,
        approver_role: str | None,
        payload: dict[str, Any],
    ) -> ApprovalRow:
        row = ApprovalRow(
            id=self._id_factory(),
            violation_id=violation_id,
            status="Requested",
            approver_role=approver_role,
            payload=payload,
            requested_at=self._clock(),
        )
        self._session.add(row)
        return row

    def decide(
        self,
        row: ApprovalRow,
        status: str,
        approver: str,
        reason: str | None,
    ) -> ApprovalRow:
        row.status = status
        row.approver = approver
        row.reason = reason
        row.decided_at = self._clock()
        return row

    def latest_for(self, violation_id: str) -> ApprovalRow | None:
        stmt = (
            select(ApprovalRow)
            .where(ApprovalRow.violation_id == violation_id)
            .order_by(ApprovalRow.requested_at.desc(), ApprovalRow.id.desc())
        )
        return self._session.scalars(stmt).first()

    def list_for(self, violation_id: str) -> list[ApprovalRow]:
        stmt = (
            select(ApprovalRow)
            .where(ApprovalRow.violation_id == violation_id)
            .order_by(ApprovalRow.requested_at)
        )
        return list(self._session.scalars(stmt))
