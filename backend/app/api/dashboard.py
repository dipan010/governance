"""Dashboard summary metrics (spec section 17.1)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ArtifactRow
from app.db.session import get_db
from app.repositories.violations_repo import ViolationsRepository

router = APIRouter(prefix="/api")

DbSession = Annotated[Session, Depends(get_db)]


class DashboardSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_findings: int = Field(alias="totalFindings")
    critical_findings: int = Field(alias="criticalFindings")
    repeat_violations: int = Field(alias="repeatViolations")
    auto_remediable: int = Field(alias="autoRemediable")
    tickets: int
    pr_comments: int = Field(alias="prComments")
    exceptions: int
    blocked_unsafe_actions: int = Field(alias="blockedUnsafeActions")
    verified_fixes: int = Field(alias="verifiedFixes")


@router.get("/dashboard/summary")
def dashboard_summary(db: DbSession) -> DashboardSummary:
    rows = ViolationsRepository(db).list_violations()
    artifacts = list(db.scalars(select(ArtifactRow)))
    artifact_kinds = [a.kind for a in artifacts]

    def decision(row_evidence: dict[str, object]) -> dict[str, object]:
        value = row_evidence.get("decision", {})
        return value if isinstance(value, dict) else {}

    return DashboardSummary(
        total_findings=len(rows),
        critical_findings=sum(
            1 for r in rows if decision(r.evidence).get("riskBand") == "Critical"
        ),
        repeat_violations=sum(
            1
            for r in rows
            if (r.evidence.get("history", {}) or {}).get("recurrenceCount", 0)
        ),
        auto_remediable=sum(
            1
            for r in rows
            if decision(r.evidence).get("recommendedPath") == "remediation_dry_run"
        ),
        tickets=artifact_kinds.count("ticket"),
        pr_comments=artifact_kinds.count("pr_comment_preview"),
        exceptions=artifact_kinds.count("exception_request"),
        blocked_unsafe_actions=sum(1 for r in rows if r.action_status == "Blocked"),
        verified_fixes=sum(
            1 for r in rows if r.action_status in ("Verified", "Closed")
        ),
    )
