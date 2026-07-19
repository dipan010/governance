"""Artifacts API: generate draft artifacts through the approval gate."""

import uuid
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.approval_gate import ApprovalGate
from app.agents.artifact_composer import (
    ROUTE_ARTIFACTS,
    ActionArtifact,
    ArtifactComposer,
)
from app.agents.source_drift_agent import SourceDriftAgent
from app.connectors.repo_map import FixtureRepoMap
from app.core.config import get_settings
from app.core.security import Role, require_role
from app.db.models import ArtifactRow, ViolationRow
from app.db.session import get_db
from app.domain.approval import ActionKind, ApprovalGateError
from app.domain.enums import ActionStatus
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.routing import ExceptionRequest
from app.repositories.approvals_repo import ApprovalsRepository
from app.repositories.violations_repo import ViolationsRepository

router = APIRouter(prefix="/api")

DbSession = Annotated[Session, Depends(get_db)]
OperatorRole = Annotated[Role, Depends(require_role(Role.OPERATOR, Role.ADMIN))]


@lru_cache
def get_composer() -> ArtifactComposer:
    repos = FixtureRepoMap(get_settings().fixtures_dir)
    return ArtifactComposer(SourceDriftAgent(repos))


class ExceptionBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    owner: str
    justification: str
    compensating_control: str = Field(alias="compensatingControl")
    expiry: str | None = None
    review_date: str | None = Field(alias="reviewDate", default=None)


class ArtifactRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    kind: str | None = None
    exception_request: ExceptionBody | None = Field(
        alias="exceptionRequest", default=None
    )


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    artifact_id: str = Field(alias="artifactId")
    violation_id: str = Field(alias="violationId")
    kind: str
    title: str
    body: str
    requires_approval: bool = Field(alias="requiresApproval")
    approval_state: str = Field(alias="approvalState")
    is_draft: bool = Field(alias="isDraft")
    created_at: str = Field(alias="createdAt")


def _response(artifact: ActionArtifact) -> ArtifactResponse:
    return ArtifactResponse(
        artifact_id=artifact.artifact_id,
        violation_id=artifact.violation_id,
        kind=artifact.kind.value,
        title=artifact.title,
        body=artifact.body,
        requires_approval=artifact.requires_approval,
        approval_state=artifact.approval_state,
        is_draft=artifact.is_draft,
        created_at=artifact.created_at.isoformat(),
    )


def _load(db: Session, violation_id: str) -> tuple[ViolationRow, CanonicalEvidence]:
    row = ViolationsRepository(db).get_violation(violation_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "violation_not_found", "violationId": violation_id},
        )
    return row, CanonicalEvidence.model_validate(row.evidence)


def _record_on_evidence(
    evidence: CanonicalEvidence, kind: ActionKind, artifact_id: str
) -> None:
    state = evidence.action_state
    if kind is ActionKind.TICKET:
        state.ticket_id = f"TICKET-{artifact_id[:8]}"
    elif kind is ActionKind.REMEDIATION_DRY_RUN:
        state.remediation_task_id = f"DRYRUN-{artifact_id[:8]}"
    # PR/comment previews never set pr_url: no real PR exists.
    if kind is ActionKind.BLOCKED_CARD:
        state.action_status = ActionStatus.BLOCKED
    else:
        state.action_status = ActionStatus.ARTIFACT_CREATED


@router.post("/violations/{violation_id}/artifact")
def create_artifacts(
    violation_id: str,
    db: DbSession,
    _role: OperatorRole,
    body: ArtifactRequest | None = None,
) -> list[ArtifactResponse]:
    row, evidence = _load(db, violation_id)
    gate = ApprovalGate(ApprovalsRepository(db), ViolationsRepository(db))

    if body is not None and body.kind:
        try:
            kinds = [ActionKind(body.kind)]
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "unknown_artifact_kind", "kind": body.kind},
            ) from exc
    else:
        route = evidence.decision.recommended_path
        kinds = ROUTE_ARTIFACTS.get(route, []) if route else []
        if not kinds:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "no_artifact_for_route",
                    "route": route.value if route else None,
                },
            )

    exception = None
    if body is not None and body.exception_request is not None:
        req = body.exception_request
        exception = ExceptionRequest.model_validate(
            {
                "owner": req.owner,
                "justification": req.justification,
                "compensating_control": req.compensating_control,
                "expiry": req.expiry,
                "review_date": req.review_date,
            }
        )

    responses: list[ArtifactResponse] = []
    now = datetime.now(UTC)
    for kind in kinds:
        try:
            gate.ensure_allowed(evidence, kind)
        except ApprovalGateError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "approval_gate",
                    "reason": exc.reason,
                    "rule": exc.rule,
                },
            ) from exc
        artifact_id = uuid.uuid4().hex
        try:
            artifact = get_composer().compose(
                evidence,
                kind,
                gate.approval_state(violation_id).value,
                artifact_id,
                now,
                exception=exception,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "invalid_artifact_request", "reason": str(exc)},
            ) from exc
        db.add(
            ArtifactRow(
                id=artifact.artifact_id,
                violation_id=violation_id,
                kind=artifact.kind.value,
                title=artifact.title,
                body=artifact.body,
                requires_approval=artifact.requires_approval,
                approval_state=artifact.approval_state,
                is_draft=artifact.is_draft,
                created_at=now,
            )
        )
        _record_on_evidence(evidence, kind, artifact.artifact_id)
        responses.append(_response(artifact))

    ViolationsRepository(db).upsert_violation(evidence, row.raw_finding_id)
    db.flush()
    return responses


@router.get("/violations/{violation_id}/artifacts")
def list_artifacts(violation_id: str, db: DbSession) -> list[ArtifactResponse]:
    _load(db, violation_id)
    stmt = (
        select(ArtifactRow)
        .where(ArtifactRow.violation_id == violation_id)
        .order_by(ArtifactRow.created_at)
    )
    return [
        ArtifactResponse(
            artifact_id=r.id,
            violation_id=r.violation_id,
            kind=r.kind,
            title=r.title,
            body=r.body,
            requires_approval=r.requires_approval,
            approval_state=r.approval_state,
            is_draft=r.is_draft,
            created_at=r.created_at.isoformat(),
        )
        for r in db.scalars(stmt)
    ]
