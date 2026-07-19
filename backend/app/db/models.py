"""Declarative base and persistence models.

raw_findings is append-only and never mutated after ingestion (RULES.md
section 6.9); violations holds the normalized canonical evidence. Schema is
owned by Alembic migrations; local/test convenience uses create_all.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class RawFindingRow(Base):
    __tablename__ = "raw_findings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(32))
    ingest_id: Mapped[str] = mapped_column(String(64), index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class ApprovalRow(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    violation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("violations.violation_id"), index=True
    )
    status: Mapped[str] = mapped_column(String(16), index=True)
    approver_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approver: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ViolationRow(Base):
    __tablename__ = "violations"

    violation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    raw_finding_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("raw_findings.id")
    )
    schema_version: Mapped[str] = mapped_column(String(16))
    policy_id: Mapped[str] = mapped_column(String(256), index=True)
    resource_id: Mapped[str] = mapped_column(String(1024))
    resource_id_normalized: Mapped[str] = mapped_column(String(1024), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    compliance_state: Mapped[str] = mapped_column(String(32))
    action_status: Mapped[str] = mapped_column(String(32), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON)
    missing_evidence: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
