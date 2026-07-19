"""Action artifact composer.

Renders draft artifacts (ticket, PR/comment preview, dry-run plan, exception
request, blocked card) from templates using evidence only. Every artifact is
a draft: nothing is sent to ServiceNow/Jira/GitHub/Azure. The approval gate
is enforced by the API before composition for approval-required kinds.
"""

from datetime import datetime
from pathlib import Path
from string import Template

from pydantic import BaseModel

from app.agents.source_drift_agent import SourceDriftAgent
from app.domain.approval import ActionKind
from app.domain.enums import BlockerCode, RoutePath
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.routing import ExceptionRequest, side_effects_for

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

ROUTE_ARTIFACTS: dict[RoutePath, list[ActionKind]] = {
    RoutePath.SOURCE_PR_PLUS_CHANGE_TICKET: [
        ActionKind.PR_COMMENT_PREVIEW,
        ActionKind.TICKET,
    ],
    RoutePath.OWNER_TICKET_OR_CHANGE_REQUEST: [ActionKind.TICKET],
    RoutePath.REMEDIATION_DRY_RUN: [ActionKind.REMEDIATION_DRY_RUN],
    RoutePath.TIME_BOUND_EXCEPTION: [ActionKind.EXCEPTION_REQUEST],
    RoutePath.BLOCKED_MANUAL_REVIEW: [ActionKind.BLOCKED_CARD],
    RoutePath.ESCALATION: [ActionKind.BLOCKED_CARD],
}

_TEMPLATE_FILES = {
    ActionKind.TICKET: "ticket.md",
    ActionKind.PR_COMMENT_PREVIEW: "pr_comment.md",
    ActionKind.REMEDIATION_DRY_RUN: "remediation_dry_run.md",
    ActionKind.EXCEPTION_REQUEST: "exception_request.md",
    ActionKind.BLOCKED_CARD: "blocked_card.md",
}

BLOCKER_RULES: dict[BlockerCode, tuple[str, str]] = {
    BlockerCode.MISSING_OWNER: (
        "RULES.md 2.7: missing owner blocks auto-action",
        "Run owner discovery (tags, CMDB, deployment caller), then re-route",
    ),
    BlockerCode.MISSING_RESOURCE_IDENTITY: (
        "RULES.md 2.6: no executable recommendation without resource identity",
        "Enrich the finding with a resource ID, then re-route",
    ),
    BlockerCode.MISSING_FAILURE_REASON: (
        "RULES.md 3.6: missing evidence routes to enrichment",
        "Re-query policy insights for the failure detail",
    ),
    BlockerCode.MISSING_VERIFICATION_QUERY: (
        "RULES.md 2.5: no closure without after-state proof",
        "Attach a verification query; until then, ticket only",
    ),
    BlockerCode.UNKNOWN_DOWNTIME_RISK: (
        "RULES.md 2.7: unknown downtime risk blocks auto-remediation",
        "Owner assesses downtime impact in a change review",
    ),
    BlockerCode.UNKNOWN_DEPENDENCY_IMPACT: (
        "RULES.md 2.7: unknown dependency impact blocks auto-remediation",
        "Map dependencies via Resource Graph before any change",
    ),
    BlockerCode.PRODUCTION_RUNTIME_CHANGE: (
        "RULES.md 2.3: production stops at ticket, PR/comment, or dry-run",
        "Use the owner ticket or source PR path with a change window",
    ),
    BlockerCode.MISSING_PERMISSION_CHECK: (
        "RULES.md 2.7: missing permission check blocks runtime action",
        "Verify the managed identity's effective permission first",
    ),
    BlockerCode.SOURCE_CODE_CHANGE_WITHOUT_APPROVAL: (
        "RULES.md 2.2: no source change without approval",
        "Request approval; keep the PR as a preview until granted",
    ),
    BlockerCode.EXCEPTION_WITHOUT_EXPIRY: (
        "RULES.md 2.8: exceptions require owner, justification, "
        "compensating control, and expiry",
        "Complete the exception request fields and resubmit",
    ),
}


class ActionArtifact(BaseModel):
    artifact_id: str
    violation_id: str
    kind: ActionKind
    title: str
    body: str
    requires_approval: bool
    approval_state: str
    is_draft: bool = True
    created_at: datetime


def _fmt(value: object) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list):
        return "; ".join(str(v) for v in value) if value else "none"
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items()) if value else "none"
    return str(value)


class ArtifactComposer:
    def __init__(
        self,
        source_drift_agent: SourceDriftAgent,
        templates_dir: Path = TEMPLATES_DIR,
    ) -> None:
        self._source_drift = source_drift_agent
        self._templates_dir = templates_dir

    def compose(
        self,
        evidence: CanonicalEvidence,
        kind: ActionKind,
        approval_state: str,
        artifact_id: str,
        created_at: datetime,
        exception: ExceptionRequest | None = None,
    ) -> ActionArtifact:
        template_file = _TEMPLATE_FILES.get(kind)
        if template_file is None:
            raise ValueError(f"No template for artifact kind '{kind.value}'")
        template = Template((self._templates_dir / template_file).read_text())
        context = self._context(evidence, approval_state, artifact_id, created_at)
        if kind is ActionKind.EXCEPTION_REQUEST:
            if exception is None or not exception.is_valid():
                raise ValueError(
                    "Exception request requires owner, justification, "
                    "compensating control, and expiry (RULES.md 2.8)"
                )
            context.update(
                {
                    "exception_owner": exception.owner,
                    "exception_justification": exception.justification,
                    "exception_compensating_control": (exception.compensating_control),
                    "exception_expiry": _fmt(exception.expiry),
                    "exception_review_date": _fmt(exception.review_date),
                }
            )
        body = template.safe_substitute(context)
        return ActionArtifact(
            artifact_id=artifact_id,
            violation_id=evidence.violation_id,
            kind=kind,
            title=f"{kind.value}: {evidence.violation_id} — "
            f"{evidence.policy_evidence.policy_name}",
            body=body,
            requires_approval=kind is ActionKind.REMEDIATION_DRY_RUN,
            approval_state=approval_state,
            created_at=created_at,
        )

    def _source_fix_section(self, evidence: CanonicalEvidence) -> str:
        analysis = self._source_drift.analyze(evidence)
        if analysis is None or not analysis.source_drift_likely:
            return "Not applicable (no source drift detected for this resource)"
        lines = [
            f"Repo: {analysis.repo_url}",
            f"File: {analysis.repo_path}",
            f"Module: {analysis.module}",
            f"CODEOWNER: {analysis.code_owner}",
        ]
        lines += [
            f"Property {f.source_property}: current '{f.current_source_value}' "
            f"-> expected '{f.expected_source_value}' "
            f"(runtime: {f.runtime_property})"
            for f in analysis.drifted_properties
        ]
        return "\n".join(lines)

    def _blocked_sections(self, evidence: CanonicalEvidence) -> tuple[str, str]:
        rules: list[str] = []
        alternatives: list[str] = []
        for blocker in evidence.decision.blockers:
            rule, alternative = BLOCKER_RULES.get(
                blocker, (blocker.value, "Manual review")
            )
            rules.append(f"- {blocker.value}: {rule}")
            alternatives.append(f"- {alternative}")
        if not rules:
            rules = ["- Route requires manual review"]
            alternatives = ["- Review the finding manually, then re-route"]
        return "\n".join(rules), "\n".join(alternatives)

    def _context(
        self,
        evidence: CanonicalEvidence,
        approval_state: str,
        artifact_id: str,
        created_at: datetime,
    ) -> dict[str, str]:
        decision = evidence.decision
        signals = evidence.risk_signals
        if signals.internet_exposure is True:
            exposure = "internet exposed"
        elif signals.internet_exposure is False:
            exposure = "private only"
        else:
            exposure = "unknown"
        blocked_rules, safe_alternative = self._blocked_sections(evidence)
        return {
            "artifact_id": artifact_id,
            "created_at": created_at.isoformat(),
            "ticket_ref": f"TICKET-{artifact_id[:8]}",
            "violation_id": evidence.violation_id,
            "policy_name": evidence.policy_evidence.policy_name,
            "resource_id": evidence.resource_facts.resource_id or "unknown",
            "resource_type": _fmt(evidence.resource_facts.resource_type),
            "environment": evidence.resource_facts.environment.value,
            "owner_team": _fmt(evidence.ownership.owner_team),
            "owner_email": _fmt(evidence.ownership.owner_email),
            "owner_confidence": evidence.ownership.owner_confidence.value,
            "support_group": _fmt(evidence.ownership.support_group),
            "business_app": _fmt(evidence.ownership.business_app),
            "exposure": exposure,
            "data_classification": signals.data_classification.value,
            "compliance_state": evidence.policy_evidence.compliance_state.value,
            "failure_reason": _fmt(evidence.policy_evidence.failure_reason),
            "evaluated_at": evidence.policy_evidence.evaluated_at.isoformat(),
            "risk_score": _fmt(decision.risk_score),
            "risk_band": decision.risk_band.value if decision.risk_band else "unknown",
            "score_factors": _fmt(decision.score_factors),
            "blockers": _fmt([b.value for b in decision.blockers]),
            "actionability_score": _fmt(decision.actionability_score),
            "route": (
                decision.recommended_path.value
                if decision.recommended_path
                else "unrouted"
            ),
            "rollback_or_next_action": _fmt(decision.rollback_or_next_action),
            "approval_required": _fmt(decision.approval_required),
            "approval_state": approval_state,
            "approver_role": _fmt(decision.approver_role),
            "side_effects": _fmt(side_effects_for(evidence)),
            "required_permission": _fmt(
                evidence.remediation_eligibility.required_permission
            ),
            "source_fix": self._source_fix_section(evidence),
            "verification_query": _fmt(evidence.verification.verification_query),
            "expected_compliant_value": _fmt(
                evidence.verification.expected_compliant_value
            ),
            "before_state": _fmt(evidence.verification.before_state),
            "blocked_rules": blocked_rules,
            "safe_alternative": safe_alternative,
        }
