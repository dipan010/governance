"""Deterministic route selection (pure, unit-testable).

Rule order (spec section 12, with one documented interpretation): unknown
side effects block RUNTIME remediation, not source fixes — a source PR plus
change ticket never touches the runtime resource directly, so POL-001-style
findings with source drift still route to the source fix. A missing owner
always blocks. Production items never auto-apply: changing routes carry
approval_required=True and stop at ticket/PR/dry-run.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import (
    BlockerCode,
    EnvironmentType,
    ImpactLevel,
    RoutePath,
)
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.scoring import compute_blockers

ROUTE_RULE_VERSION = "route-1.0.0"

LOW_IMPACT = (ImpactLevel.NONE, ImpactLevel.LOW)


class ExceptionRequest(BaseModel):
    owner: str
    justification: str
    compensating_control: str
    expiry: datetime | None = None
    review_date: datetime | None = None

    def is_valid(self) -> bool:
        return bool(
            self.owner
            and self.justification
            and self.compensating_control
            and self.expiry is not None
        )


class RouteDecision(BaseModel):
    route: RoutePath
    reason: str
    blockers: list[BlockerCode] = Field(default_factory=list)
    approval_required: bool
    approver_role: str | None = None
    side_effects: list[str] = Field(default_factory=list)
    rollback_or_next_action: str
    rule_version: str = ROUTE_RULE_VERSION


def _side_effects(evidence: CanonicalEvidence) -> list[str]:
    eligibility = evidence.remediation_eligibility
    effects = [
        f"restart risk: {eligibility.restart_risk.value}",
        f"downtime risk: {eligibility.downtime_risk.value}",
        f"cost impact: {eligibility.cost_impact.value}",
    ]
    if evidence.resource_facts.environment is EnvironmentType.PRODUCTION:
        effects.append("production resource: runtime change affects live traffic")
    return effects


def plan_route(
    evidence: CanonicalEvidence,
    exception_request: ExceptionRequest | None = None,
) -> RouteDecision:
    blockers = compute_blockers(evidence)
    side_effects = _side_effects(evidence)

    def decision(
        route: RoutePath,
        reason: str,
        approval_required: bool,
        approver_role: str | None,
        next_action: str,
    ) -> RouteDecision:
        return RouteDecision(
            route=route,
            reason=reason,
            blockers=blockers,
            approval_required=approval_required,
            approver_role=approver_role,
            side_effects=side_effects,
            rollback_or_next_action=next_action,
        )

    if not evidence.resource_facts.resource_id:
        return decision(
            RoutePath.INVALID_FINDING,
            "Resource identity is missing; the finding cannot be routed",
            False,
            None,
            "Enrich resource identity, then re-route",
        )

    if evidence.ownership.owner_team is None:
        return decision(
            RoutePath.BLOCKED_MANUAL_REVIEW,
            "Owner is missing; auto-action is blocked until owner discovery",
            False,
            None,
            "Run owner discovery or manual review, then re-route",
        )

    if (
        evidence.history.source_drift_likely is True
        and evidence.ownership.repo_path is not None
    ):
        return decision(
            RoutePath.SOURCE_PR_PLUS_CHANGE_TICKET,
            "Source drift detected with a mapped repo path; runtime-only "
            "patching would be temporary, so fix the source of truth",
            True,
            "Cloud Governance Approver",
            "Revert the source PR if the deployment misbehaves; re-run "
            "verification after deployment",
        )

    if exception_request is not None:
        if exception_request.is_valid():
            return decision(
                RoutePath.TIME_BOUND_EXCEPTION,
                "Valid exception request with owner, justification, "
                "compensating control, and expiry",
                True,
                "Security / Compliance Lead",
                "Review the exception before its expiry date; remove the "
                "compensating control only after compliance is restored",
            )
        blockers = [*blockers, BlockerCode.EXCEPTION_WITHOUT_EXPIRY]
        return decision(
            RoutePath.BLOCKED_MANUAL_REVIEW,
            "Exception request is invalid (owner, justification, "
            "compensating control, and expiry are all required)",
            False,
            None,
            "Complete the exception request fields, then re-route",
        )

    eligibility = evidence.remediation_eligibility
    if (
        eligibility.remediation_supported is True
        and eligibility.permission_available is True
        and evidence.resource_facts.environment is not EnvironmentType.PRODUCTION
        and eligibility.downtime_risk in LOW_IMPACT
        and eligibility.restart_risk in LOW_IMPACT
    ):
        return decision(
            RoutePath.REMEDIATION_DRY_RUN,
            "Remediation is supported with permission available on a "
            "non-production resource with low side-effect risk; dry-run "
            "only, and only after approval",
            True,
            "Change Approver",
            "Review the dry-run plan output; apply only with a separate "
            "approved change",
        )

    return decision(
        RoutePath.OWNER_TICKET_OR_CHANGE_REQUEST,
        "Owner exists but automation is not safe "
        "(side effects unknown or remediation unsupported)",
        False,
        None,
        "Assign the ticket to the owner team and schedule a change review",
    )
