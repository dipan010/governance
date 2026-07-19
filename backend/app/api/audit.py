"""Audit API: read the append-only audit trail for a violation."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.audit_repo import AuditRepository

router = APIRouter(prefix="/api")

DbSession = Annotated[Session, Depends(get_db)]


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(alias="eventId")
    violation_id: str = Field(alias="violationId")
    event_type: str = Field(alias="eventType")
    correlation_id: str = Field(alias="correlationId")
    action_id: str | None = Field(alias="actionId")
    prompt_run_id: str = Field(alias="promptRunId")
    evidence_packet: str | None = Field(alias="evidencePacket")
    payload: dict[str, Any]
    created_at: str = Field(alias="createdAt")


@router.get("/audit/{violation_id}")
def audit_trail(violation_id: str, db: DbSession) -> list[AuditEventResponse]:
    return [
        AuditEventResponse(
            event_id=row.id,
            violation_id=row.violation_id,
            event_type=row.event_type,
            correlation_id=row.correlation_id,
            action_id=row.action_id,
            prompt_run_id=row.prompt_run_id,
            evidence_packet=row.evidence_packet,
            payload=row.payload,
            created_at=row.created_at.isoformat(),
        )
        for row in AuditRepository(db).list_for(violation_id)
    ]
