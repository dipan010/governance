"""Ingestion and violations API."""

import uuid
from functools import lru_cache
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.agents.core_policy_agent import (
    NormalizationResult,
    normalize_defender_finding,
    normalize_policy_finding,
)
from app.agents.enrichment_agent import EnrichmentAgent
from app.agents.nsg_drift_agent import NsgDriftAgent
from app.agents.storage_firewall_agent import StorageFirewallAgent
from app.connectors.defender import FixtureDefender
from app.connectors.owner_map import FixtureOwnerMap
from app.connectors.repo_map import FixtureRepoMap
from app.connectors.resource_inventory import FixtureResourceInventory
from app.connectors.verification_source import FixtureVerificationSource
from app.core.config import get_settings
from app.core.security import Role, require_role
from app.db.session import get_db
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.focused_signals import merge_signals
from app.domain.validation import IssueSeverity, ValidationIssue
from app.repositories.violations_repo import ViolationsRepository


@lru_cache
def get_enrichment_agent() -> EnrichmentAgent:
    fixtures_dir = get_settings().fixtures_dir
    return EnrichmentAgent(
        inventory=FixtureResourceInventory(fixtures_dir),
        owners=FixtureOwnerMap(fixtures_dir),
        repos=FixtureRepoMap(fixtures_dir),
        defender=FixtureDefender(fixtures_dir),
        verification=FixtureVerificationSource(fixtures_dir),
    )


@lru_cache
def get_repo_map() -> FixtureRepoMap:
    return FixtureRepoMap(get_settings().fixtures_dir)


def apply_focused_agents(evidence: CanonicalEvidence, record: dict[str, Any]) -> None:
    """Run focused agents in the pipeline; they emit signals only."""
    runtime_properties: dict[str, Any] = record.get("properties") or {}
    repo_mapping = get_repo_map().get_mapping(evidence.resource_facts.resource_id)
    storage_agent = StorageFirewallAgent()
    if storage_agent.applies_to(evidence):
        merge_signals(
            evidence, storage_agent.detect(evidence, runtime_properties, repo_mapping)
        )
    nsg_agent = NsgDriftAgent()
    if nsg_agent.applies_to(evidence):
        merge_signals(evidence, nsg_agent.detect(evidence, runtime_properties))


router = APIRouter(prefix="/api")

DbSession = Annotated[Session, Depends(get_db)]
IngestRole = Annotated[
    Role, Depends(require_role(Role.ANALYST, Role.OPERATOR, Role.ADMIN))
]


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    findings: list[dict[str, Any]]


class RecordResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    violation_id: str | None = Field(alias="violationId", default=None)
    status: Literal["ingested", "ingested_with_warnings", "error"]
    issues: list[ValidationIssue] = Field(default_factory=list)


class IngestResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ingest_id: str = Field(alias="ingestId")
    ingested: int
    errors: int
    results: list[RecordResult]


class ViolationSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    violation_id: str = Field(alias="violationId")
    policy_id: str = Field(alias="policyId")
    resource_id: str = Field(alias="resourceId")
    severity: str
    compliance_state: str = Field(alias="complianceState")
    action_status: str = Field(alias="actionStatus")
    missing_evidence: list[str] = Field(alias="missingEvidence")


class ViolationDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    violation_id: str = Field(alias="violationId")
    evidence: dict[str, Any]
    missing_evidence: list[str] = Field(alias="missingEvidence")
    raw_evidence: dict[str, Any] | None = Field(alias="rawEvidence")


def _ingest(
    body: IngestRequest,
    db: Session,
    source: Literal["policy", "defender"],
) -> IngestResponse:
    repo = ViolationsRepository(db)
    ingest_id = uuid.uuid4().hex
    results: list[RecordResult] = []
    for record in body.findings:
        # Raw evidence is preserved even for invalid records.
        raw_id = repo.add_raw_finding(source, ingest_id, record)
        try:
            normalized: NormalizationResult = (
                normalize_policy_finding(record)
                if source == "policy"
                else normalize_defender_finding(record)
            )
        except Exception:
            results.append(
                RecordResult(
                    status="error",
                    issues=[
                        ValidationIssue(
                            field="record",
                            code="missing_resource_identity",
                            severity=IssueSeverity.ERROR,
                            message="Record could not be normalized",
                        )
                    ],
                )
            )
            continue
        get_enrichment_agent().enrich(normalized.evidence)
        apply_focused_agents(normalized.evidence, record)
        repo.upsert_violation(normalized.evidence, raw_id)
        results.append(
            RecordResult(
                violation_id=normalized.evidence.violation_id,
                status="ingested_with_warnings" if normalized.issues else "ingested",
                issues=normalized.issues,
            )
        )
    ingested = sum(1 for r in results if r.status != "error")
    return IngestResponse(
        ingest_id=ingest_id,
        ingested=ingested,
        errors=len(results) - ingested,
        results=results,
    )


@router.post("/ingest/policy")
def ingest_policy(
    body: IngestRequest, db: DbSession, _role: IngestRole
) -> IngestResponse:
    return _ingest(body, db, "policy")


@router.post("/ingest/defender")
def ingest_defender(
    body: IngestRequest, db: DbSession, _role: IngestRole
) -> IngestResponse:
    return _ingest(body, db, "defender")


@router.get("/violations")
def list_violations(db: DbSession) -> list[ViolationSummary]:
    repo = ViolationsRepository(db)
    return [
        ViolationSummary(
            violation_id=row.violation_id,
            policy_id=row.policy_id,
            resource_id=row.resource_id,
            severity=row.severity,
            compliance_state=row.compliance_state,
            action_status=row.action_status,
            missing_evidence=row.missing_evidence,
        )
        for row in repo.list_violations()
    ]


@router.get("/violations/{violation_id}")
def get_violation(violation_id: str, db: DbSession) -> ViolationDetail:
    repo = ViolationsRepository(db)
    row = repo.get_violation(violation_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "violation_not_found", "violationId": violation_id},
        )
    raw = repo.get_raw_finding(row.raw_finding_id)
    return ViolationDetail(
        violation_id=row.violation_id,
        evidence=row.evidence,
        missing_evidence=row.missing_evidence,
        raw_evidence=raw.payload if raw else None,
    )
