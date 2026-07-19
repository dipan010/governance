"""Approvals API: request, decide, and inspect approvals."""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.agents.approval_gate import ApprovalGate
from app.core.security import Role, require_role
from app.db.models import ApprovalRow, ViolationRow
from app.db.session import get_db
from app.domain.approval import ApprovalGateError
from app.domain.audit import AuditEventType
from app.domain.evidence_schema import CanonicalEvidence
from app.repositories.approvals_repo import ApprovalsRepository
from app.repositories.audit_repo import AuditRepository
from app.repositories.violations_repo import ViolationsRepository

_DECISION_EVENTS = {
    "approve": AuditEventType.APPROVAL_APPROVED,
    "reject": AuditEventType.APPROVAL_REJECTED,
    "defer": AuditEventType.APPROVAL_DEFERRED,
}

router = APIRouter(prefix="/api")

DbSession = Annotated[Session, Depends(get_db)]
RequesterRole = Annotated[
    Role, Depends(require_role(Role.ANALYST, Role.OPERATOR, Role.ADMIN))
]
ApproverRole = Annotated[Role, Depends(require_role(Role.APPROVER, Role.ADMIN))]


class ApprovalRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    approval_id: str = Field(alias="approvalId")
    violation_id: str = Field(alias="violationId")
    status: str
    approver_role: str | None = Field(alias="approverRole")
    approver: str | None
    reason: str | None
    payload: dict[str, Any]
    requested_at: str = Field(alias="requestedAt")
    decided_at: str | None = Field(alias="decidedAt")


class DecisionRequest(BaseModel):
    decision: Literal["approve", "reject", "defer"]
    approver: str
    reason: str | None = None


def _record(row: ApprovalRow) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=row.id,
        violation_id=row.violation_id,
        status=row.status,
        approver_role=row.approver_role,
        approver=row.approver,
        reason=row.reason,
        payload=row.payload,
        requested_at=row.requested_at.isoformat(),
        decided_at=row.decided_at.isoformat() if row.decided_at else None,
    )


def _load(db: Session, violation_id: str) -> tuple[ViolationRow, CanonicalEvidence]:
    row = ViolationsRepository(db).get_violation(violation_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "violation_not_found", "violationId": violation_id},
        )
    return row, CanonicalEvidence.model_validate(row.evidence)


@router.post("/violations/{violation_id}/approval-request")
def request_approval(
    violation_id: str, db: DbSession, _role: RequesterRole
) -> ApprovalRecord:
    row, evidence = _load(db, violation_id)
    gate = ApprovalGate(ApprovalsRepository(db), ViolationsRepository(db))
    approval = gate.request(evidence, row.raw_finding_id)
    AuditRepository(db).add_event(
        violation_id,
        AuditEventType.APPROVAL_REQUESTED,
        {"approverRole": approval.approver_role, "payload": approval.payload},
        action_id=approval.id,
    )
    db.flush()
    return _record(approval)


@router.post("/violations/{violation_id}/approve")
def decide_approval(
    violation_id: str, body: DecisionRequest, db: DbSession, _role: ApproverRole
) -> ApprovalRecord:
    row, evidence = _load(db, violation_id)
    gate = ApprovalGate(ApprovalsRepository(db), ViolationsRepository(db))
    try:
        approval = gate.decide(
            evidence, row.raw_finding_id, body.decision, body.approver, body.reason
        )
    except ApprovalGateError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "approval_gate", "reason": exc.reason, "rule": exc.rule},
        ) from exc
    AuditRepository(db).add_event(
        violation_id,
        _DECISION_EVENTS[body.decision],
        {"approver": body.approver, "reason": body.reason},
        action_id=approval.id,
    )
    db.flush()
    return _record(approval)


@router.get("/violations/{violation_id}/approvals")
def list_approvals(violation_id: str, db: DbSession) -> list[ApprovalRecord]:
    _load(db, violation_id)
    return [_record(r) for r in ApprovalsRepository(db).list_for(violation_id)]
