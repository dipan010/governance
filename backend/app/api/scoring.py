"""Scoring API: recalculate a violation's score with the current rule version."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.agents.scorer_agent import ScorerAgent
from app.core.security import Role, require_role
from app.db.session import get_db
from app.domain.evidence_schema import CanonicalEvidence
from app.repositories.violations_repo import ViolationsRepository

router = APIRouter(prefix="/api")

DbSession = Annotated[Session, Depends(get_db)]
ScoreRole = Annotated[
    Role, Depends(require_role(Role.ANALYST, Role.OPERATOR, Role.ADMIN))
]


class ScoreResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    violation_id: str = Field(alias="violationId")
    risk_score: int = Field(alias="riskScore")
    risk_band: str = Field(alias="riskBand")
    score_factors: list[str] = Field(alias="scoreFactors")
    blockers: list[str]
    actionability_score: int = Field(alias="actionabilityScore")
    actionability_factors: list[str] = Field(alias="actionabilityFactors")
    score_rule_version: str = Field(alias="scoreRuleVersion")


@router.post("/violations/{violation_id}/score")
def rescore_violation(
    violation_id: str, db: DbSession, _role: ScoreRole
) -> ScoreResponse:
    repo = ViolationsRepository(db)
    row = repo.get_violation(violation_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "violation_not_found", "violationId": violation_id},
        )
    evidence = CanonicalEvidence.model_validate(row.evidence)
    ScorerAgent().score(evidence)
    repo.upsert_violation(evidence, row.raw_finding_id)
    return _to_response(evidence)


def _to_response(evidence: CanonicalEvidence) -> ScoreResponse:
    decision: Any = evidence.decision
    return ScoreResponse(
        violation_id=evidence.violation_id,
        risk_score=decision.risk_score,
        risk_band=decision.risk_band.value,
        score_factors=decision.score_factors,
        blockers=[b.value for b in decision.blockers],
        actionability_score=decision.actionability_score,
        actionability_factors=decision.actionability_factors,
        score_rule_version=decision.score_rule_version,
    )
