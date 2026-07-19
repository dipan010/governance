"""Verification API: run/simulate verification and enforce proof-gated closure."""

from functools import lru_cache
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.agents.verification_engine import VerificationEngine
from app.connectors.storage import LocalEvidencePacketStore
from app.connectors.verification_source import FixtureVerificationSource
from app.core.config import get_settings
from app.core.security import Role, require_role
from app.db.models import ViolationRow
from app.db.session import get_db
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.verification import ClosureBlockedError, VerificationOutcome
from app.repositories.audit_repo import AuditRepository
from app.repositories.violations_repo import ViolationsRepository

router = APIRouter(prefix="/api")

DbSession = Annotated[Session, Depends(get_db)]
VerifierRole = Annotated[
    Role, Depends(require_role(Role.OPERATOR, Role.AUDITOR, Role.ADMIN))
]


@lru_cache
def get_verification_source() -> FixtureVerificationSource:
    return FixtureVerificationSource(get_settings().fixtures_dir)


def _engine(db: Session) -> VerificationEngine:
    return VerificationEngine(
        get_verification_source(),
        AuditRepository(db),
        LocalEvidencePacketStore(get_settings().evidence_packets_dir),
    )


class VerifyRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    after_state: dict[str, Any] | None = Field(alias="afterState", default=None)


class VerifyResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    violation_id: str = Field(alias="violationId")
    result: str
    before_state: dict[str, Any] | None = Field(alias="beforeState")
    after_state: dict[str, Any] | None = Field(alias="afterState")
    verification_query: str | None = Field(alias="verificationQuery")
    expected_compliant_value: str | None = Field(alias="expectedCompliantValue")
    details: list[str]
    next_action: str = Field(alias="nextAction")
    action_status: str = Field(alias="actionStatus")
    rule_version: str = Field(alias="ruleVersion")


def _load(db: Session, violation_id: str) -> tuple[ViolationRow, CanonicalEvidence]:
    row = ViolationsRepository(db).get_violation(violation_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "violation_not_found", "violationId": violation_id},
        )
    return row, CanonicalEvidence.model_validate(row.evidence)


def _response(
    outcome: VerificationOutcome, evidence: CanonicalEvidence
) -> VerifyResponse:
    return VerifyResponse(
        violation_id=outcome.violation_id,
        result=outcome.result.value,
        before_state=outcome.before_state,
        after_state=outcome.after_state,
        verification_query=outcome.verification_query,
        expected_compliant_value=outcome.expected_compliant_value,
        details=outcome.details,
        next_action=outcome.next_action,
        action_status=evidence.action_state.action_status.value,
        rule_version=outcome.rule_version,
    )


@router.post("/violations/{violation_id}/verify")
def verify_violation(
    violation_id: str,
    db: DbSession,
    _role: VerifierRole,
    body: VerifyRequest | None = None,
) -> VerifyResponse:
    row, evidence = _load(db, violation_id)
    engine = _engine(db)
    outcome = engine.verify(
        evidence, after_state_override=body.after_state if body else None
    )
    ViolationsRepository(db).upsert_violation(evidence, row.raw_finding_id)
    db.flush()
    return _response(outcome, evidence)


@router.post("/violations/{violation_id}/close")
def close_violation(
    violation_id: str, db: DbSession, _role: VerifierRole
) -> dict[str, str]:
    row, evidence = _load(db, violation_id)
    engine = _engine(db)
    try:
        engine.close(evidence)
    except ClosureBlockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "closure_blocked",
                "reason": exc.reason,
                "nextAction": exc.next_action,
            },
        ) from exc
    ViolationsRepository(db).upsert_violation(evidence, row.raw_finding_id)
    db.flush()
    return {
        "violationId": violation_id,
        "actionStatus": evidence.action_state.action_status.value,
    }
