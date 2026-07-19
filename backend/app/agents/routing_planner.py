"""Remediation Routing Planner: the only component that sets the
recommended route and its approval requirements on a violation."""

from app.domain.evidence_schema import CanonicalEvidence
from app.domain.routing import (
    ROUTE_RULE_VERSION,
    ExceptionRequest,
    RouteDecision,
    plan_route,
)


class RoutingPlanner:
    def route(
        self,
        evidence: CanonicalEvidence,
        exception_request: ExceptionRequest | None = None,
    ) -> RouteDecision:
        route_decision = plan_route(evidence, exception_request)
        decision = evidence.decision
        decision.recommended_path = route_decision.route
        decision.blockers = route_decision.blockers
        decision.approval_required = route_decision.approval_required
        decision.approver_role = route_decision.approver_role
        decision.rollback_or_next_action = route_decision.rollback_or_next_action
        decision.route_rule_version = ROUTE_RULE_VERSION
        return route_decision
