"""Violations repository: raw evidence store plus normalized violation store.

Raw findings are append-only; normalized violations upsert idempotently by
stable violation ID (RULES.md sections 4.8, 6.8, 6.9). Clock and ID factory
are injectable for deterministic tests.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RawFindingRow, ViolationRow
from app.domain.evidence_schema import CanonicalEvidence


def _default_id_factory() -> str:
    return uuid.uuid4().hex


def _default_clock() -> datetime:
    return datetime.now(UTC)


class ViolationsRepository:
    def __init__(
        self,
        session: Session,
        id_factory: Callable[[], str] = _default_id_factory,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self._session = session
        self._id_factory = id_factory
        self._clock = clock

    def add_raw_finding(
        self, source: str, ingest_id: str, payload: dict[str, Any]
    ) -> str:
        raw_id = self._id_factory()
        self._session.add(
            RawFindingRow(
                id=raw_id,
                source=source,
                ingest_id=ingest_id,
                ingested_at=self._clock(),
                payload=payload,
            )
        )
        return raw_id

    def get_raw_finding(self, raw_id: str) -> RawFindingRow | None:
        return self._session.get(RawFindingRow, raw_id)

    def upsert_violation(
        self, evidence: CanonicalEvidence, raw_finding_id: str
    ) -> ViolationRow:
        now = self._clock()
        dumped = evidence.model_dump(by_alias=True, mode="json")
        row = self._session.get(ViolationRow, evidence.violation_id)
        if row is None:
            row = ViolationRow(
                violation_id=evidence.violation_id,
                created_at=now,
            )
            self._session.add(row)
        row.raw_finding_id = raw_finding_id
        row.schema_version = evidence.schema_version
        row.policy_id = evidence.policy_evidence.policy_id
        row.resource_id = evidence.resource_facts.resource_id
        row.resource_id_normalized = evidence.resource_facts.resource_id_normalized
        row.severity = evidence.risk_signals.severity.value
        row.compliance_state = evidence.policy_evidence.compliance_state.value
        row.action_status = evidence.action_state.action_status.value
        row.evaluated_at = evidence.policy_evidence.evaluated_at
        row.evidence = dumped
        row.missing_evidence = list(evidence.missing_evidence)
        row.updated_at = now
        return row

    def list_violations(self) -> list[ViolationRow]:
        stmt = select(ViolationRow).order_by(ViolationRow.violation_id)
        return list(self._session.scalars(stmt))

    def get_violation(self, violation_id: str) -> ViolationRow | None:
        return self._session.get(ViolationRow, violation_id)
