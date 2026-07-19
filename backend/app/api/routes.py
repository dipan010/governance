"""Routing API: generate the route recommendation for a violation."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.agents.routing_planner import RoutingPlanner
from app.core.security import Role, require_role
from app.db.session import get_db
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.routing import ExceptionRequest
from app.repositories.violations_repo import ViolationsRepository

router = APIRouter(prefix="/api")

DbSession = Annotated[Session, Depends(get_db)]
RouteRole = Annotated[
    Role, Depends(require_role(Role.ANALYST, Role.OPERATOR, Role.ADMIN))
]


class ExceptionRequestBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    owner: str
    justification: str
    compensating_control: str = Field(alias="compensatingControl")
    expiry: str | None = None
    review_date: str | None = Field(alias="reviewDate", default=None)


class RouteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    exception_request: ExceptionRequestBody | None = Field(
        alias="exceptionRequest", default=None
    )


class RouteResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    violation_id: str = Field(alias="violationId")
    route: str
    reason: str
    blockers: list[str]
    approval_required: bool = Field(alias="approvalRequired")
    approver_role: str | None = Field(alias="approverRole")
    side_effects: list[str] = Field(alias="sideEffects")
    rollback_or_next_action: str = Field(alias="rollbackOrNextAction")
    route_rule_version: str = Field(alias="routeRuleVersion")


@router.post("/violations/{violation_id}/route")
def route_violation(
    violation_id: str,
    db: DbSession,
    _role: RouteRole,
    body: RouteRequest | None = None,
) -> RouteResponse:
    repo = ViolationsRepository(db)
    row = repo.get_violation(violation_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "violation_not_found", "violationId": violation_id},
        )
    evidence = CanonicalEvidence.model_validate(row.evidence)

    exception_request = None
    if body is not None and body.exception_request is not None:
        req = body.exception_request
        exception_request = ExceptionRequest.model_validate(
            {
                "owner": req.owner,
                "justification": req.justification,
                "compensating_control": req.compensating_control,
                "expiry": req.expiry,
                "review_date": req.review_date,
            }
        )

    route_decision = RoutingPlanner().route(evidence, exception_request)
    repo.upsert_violation(evidence, row.raw_finding_id)
    return RouteResponse(
        violation_id=violation_id,
        route=route_decision.route.value,
        reason=route_decision.reason,
        blockers=[b.value for b in route_decision.blockers],
        approval_required=route_decision.approval_required,
        approver_role=route_decision.approver_role,
        side_effects=route_decision.side_effects,
        rollback_or_next_action=route_decision.rollback_or_next_action,
        route_rule_version=route_decision.rule_version,
    )
