"""Approval gate domain rules.

Approval is required before any runtime cloud change, source-code change,
network exposure change, identity change, or production behavior change
(RULES.md 2.1, 2.2). In hackathon mode the production gate stops at ticket,
PR/comment preview, or dry-run: real runtime applies and source pushes are
refused outright, approved or not (RULES.md 2.3).
"""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from app.domain.enums import ApprovalState, RoutePath
from app.domain.evidence_schema import CamelModel, CanonicalEvidence
from app.domain.routing import side_effects_for

APPROVAL_RULE_VERSION = "approval-1.0.0"
HACKATHON_MODE = True


class ChangeCategory(StrEnum):
    RUNTIME_CLOUD_CHANGE = "runtime_cloud_change"
    SOURCE_CODE_CHANGE = "source_code_change"
    NETWORK_EXPOSURE_CHANGE = "network_exposure_change"
    IDENTITY_CHANGE = "identity_change"
    PRODUCTION_BEHAVIOR_CHANGE = "production_behavior_change"


class ActionKind(StrEnum):
    TICKET = "ticket"
    PR_COMMENT_PREVIEW = "pr_comment_preview"
    REMEDIATION_DRY_RUN = "remediation_dry_run"
    EXCEPTION_REQUEST = "exception_request"
    BLOCKED_CARD = "blocked_card"
    ESCALATION_NOTE = "escalation_note"
    RUNTIME_APPLY = "runtime_apply"
    SOURCE_PUSH = "source_push"


# Drafts and previews change nothing and may be generated without approval.
DRAFT_ACTIONS = {
    ActionKind.TICKET,
    ActionKind.PR_COMMENT_PREVIEW,
    ActionKind.EXCEPTION_REQUEST,
    ActionKind.BLOCKED_CARD,
    ActionKind.ESCALATION_NOTE,
}
# Executing a dry-run touches the cloud control plane: approval first.
APPROVAL_REQUIRED_ACTIONS = {ActionKind.REMEDIATION_DRY_RUN}
# Never allowed in hackathon mode, with or without approval.
FORBIDDEN_ACTIONS = {ActionKind.RUNTIME_APPLY, ActionKind.SOURCE_PUSH}

APPROVAL_REQUIRED_ROUTES = {
    RoutePath.SOURCE_PR_PLUS_CHANGE_TICKET,
    RoutePath.REMEDIATION_DRY_RUN,
    RoutePath.TIME_BOUND_EXCEPTION,
}

NETWORK_RESOURCE_TYPES = (
    "microsoft.network/networksecuritygroups",
    "microsoft.network/publicipaddresses",
    "microsoft.storage/storageaccounts",
    "microsoft.dbforpostgresql/flexibleservers",
)


class ApprovalGateError(Exception):
    """An action was attempted that the approval gate refuses."""

    def __init__(self, reason: str, rule: str) -> None:
        self.reason = reason
        self.rule = rule
        super().__init__(f"{reason} [{rule}]")


class ApprovalRequiredError(ApprovalGateError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason, "RULES.md 2.1-2.2: no change without approval")


class ApprovalPayload(CamelModel):
    violation_id: str
    resource_id: str
    route: RoutePath | None
    approver_role: str | None
    risk_score: int | None
    risk_band: str | None
    score_factors: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    side_effects: list[str] = Field(default_factory=list)
    rollback_or_next_action: str | None
    verification_query: str | None
    change_categories: list[ChangeCategory] = Field(default_factory=list)
    requested_at: datetime
    rule_version: str = APPROVAL_RULE_VERSION


def change_categories(evidence: CanonicalEvidence) -> list[ChangeCategory]:
    categories: list[ChangeCategory] = []
    route = evidence.decision.recommended_path
    if route is RoutePath.SOURCE_PR_PLUS_CHANGE_TICKET:
        categories.append(ChangeCategory.SOURCE_CODE_CHANGE)
    if route is RoutePath.REMEDIATION_DRY_RUN:
        categories.append(ChangeCategory.RUNTIME_CLOUD_CHANGE)
    resource_type = (evidence.resource_facts.resource_type or "").lower()
    if resource_type in NETWORK_RESOURCE_TYPES:
        categories.append(ChangeCategory.NETWORK_EXPOSURE_CHANGE)
    if evidence.risk_signals.identity_impact is True:
        categories.append(ChangeCategory.IDENTITY_CHANGE)
    if evidence.resource_facts.environment.value == "Production":
        categories.append(ChangeCategory.PRODUCTION_BEHAVIOR_CHANGE)
    return categories


def approval_required(evidence: CanonicalEvidence) -> bool:
    return evidence.decision.recommended_path in APPROVAL_REQUIRED_ROUTES


def build_approval_payload(
    evidence: CanonicalEvidence, requested_at: datetime
) -> ApprovalPayload:
    decision = evidence.decision
    return ApprovalPayload(
        violation_id=evidence.violation_id,
        resource_id=evidence.resource_facts.resource_id,
        route=decision.recommended_path,
        approver_role=decision.approver_role,
        risk_score=decision.risk_score,
        risk_band=decision.risk_band.value if decision.risk_band else None,
        score_factors=decision.score_factors,
        blockers=[b.value for b in decision.blockers],
        side_effects=side_effects_for(evidence),
        rollback_or_next_action=decision.rollback_or_next_action,
        verification_query=evidence.verification.verification_query,
        change_categories=change_categories(evidence),
        requested_at=requested_at,
    )


def validate_action(
    evidence: CanonicalEvidence,
    kind: ActionKind,
    approval_state: ApprovalState,
) -> None:
    """Raise unless the action is allowed for this evidence and approval
    state. Deterministic: this is the only enforcement point for actions."""
    if kind in FORBIDDEN_ACTIONS and HACKATHON_MODE:
        raise ApprovalGateError(
            f"Action '{kind.value}' is not permitted in hackathon mode; "
            "production changes stop at ticket, PR/comment, or dry-run",
            "RULES.md 2.3: production stops at ticket/PR/dry-run",
        )
    if kind in APPROVAL_REQUIRED_ACTIONS and approval_state is not (
        ApprovalState.APPROVED
    ):
        raise ApprovalRequiredError(
            f"Action '{kind.value}' on {evidence.violation_id} requires an "
            f"approved approval record (current state: {approval_state.value})"
        )
