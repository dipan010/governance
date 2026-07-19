"""Risk and Recurrence Scorer: the only component that sets risk score,
band, score factors, blockers, and actionability on a violation."""

from app.domain.evidence_schema import CanonicalEvidence
from app.domain.scoring import (
    SCORE_RULE_VERSION,
    compute_actionability,
    compute_blockers,
    compute_risk_score,
)


class ScorerAgent:
    def score(self, evidence: CanonicalEvidence) -> CanonicalEvidence:
        risk = compute_risk_score(evidence)
        blockers = compute_blockers(evidence)
        actionability = compute_actionability(evidence, blockers)

        decision = evidence.decision
        decision.risk_score = risk.score
        decision.risk_band = risk.band
        decision.score_factors = [
            f"{factor.factor} (+{factor.points})" for factor in risk.factors
        ]
        decision.blockers = blockers
        decision.score_rule_version = SCORE_RULE_VERSION
        decision.actionability_score = actionability.score
        decision.actionability_factors = [
            f"{c.factor} (+{c.points})" for c in actionability.components
        ] + (
            [f"blocker weight (-{actionability.blocker_weight})"]
            if actionability.blocker_weight
            else []
        )
        return evidence
