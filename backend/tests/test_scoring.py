"""Risk and Recurrence Scorer tests: determinism, bands, blockers,
actionability separation, and raw-vs-ranked ordering."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.agents.core_policy_agent import normalize_policy_finding
from app.agents.enrichment_agent import EnrichmentAgent
from app.agents.scorer_agent import ScorerAgent
from app.connectors.defender import FixtureDefender
from app.connectors.owner_map import FixtureOwnerMap
from app.connectors.repo_map import FixtureRepoMap
from app.connectors.resource_inventory import FixtureResourceInventory
from app.connectors.verification_source import FixtureVerificationSource
from app.domain.enums import BlockerCode, RiskBand
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.scoring import (
    band_for_score,
    compute_actionability,
    compute_blockers,
    compute_risk_score,
)
from tests.conftest import FIXTURES


@pytest.fixture
def scored(policy_fixture: dict[str, Any]) -> dict[str, CanonicalEvidence]:
    enrichment = EnrichmentAgent(
        inventory=FixtureResourceInventory(FIXTURES),
        owners=FixtureOwnerMap(FIXTURES),
        repos=FixtureRepoMap(FIXTURES),
        defender=FixtureDefender(FIXTURES),
        verification=FixtureVerificationSource(FIXTURES),
    )
    scorer = ScorerAgent()
    result = {}
    for record in policy_fixture["findings"]:
        evidence = normalize_policy_finding(record).evidence
        enrichment.enrich(evidence)
        scorer.score(evidence)
        result[evidence.violation_id] = evidence
    return result


def test_pol001_scores_critical(scored: dict[str, CanonicalEvidence]) -> None:
    decision = scored["POL-001"].decision
    assert decision.risk_score == 100  # capped from 105
    assert decision.risk_band is RiskBand.CRITICAL
    joined = " | ".join(decision.score_factors)
    assert "high or critical severity (+20)" in joined
    assert "production or shared platform resource (+15)" in joined
    assert "sensitive data classification (Restricted) (+20)" in joined
    assert "internet exposure (+20)" in joined
    assert "recurrence" in joined
    assert "source drift likely (+10)" in joined
    assert "strong owner confidence (+5)" in joined


def test_scores_are_deterministic(policy_fixture: dict[str, Any]) -> None:
    record = policy_fixture["findings"][0]
    scores = set()
    for _ in range(3):
        evidence = normalize_policy_finding(record).evidence
        score = compute_risk_score(evidence)
        scores.add((score.score, score.band))
    assert len(scores) == 1


def test_band_boundaries() -> None:
    assert band_for_score(100) is RiskBand.CRITICAL
    assert band_for_score(80) is RiskBand.CRITICAL
    assert band_for_score(79) is RiskBand.HIGH
    assert band_for_score(60) is RiskBand.HIGH
    assert band_for_score(59) is RiskBand.MEDIUM
    assert band_for_score(40) is RiskBand.MEDIUM
    assert band_for_score(39) is RiskBand.LOW
    assert band_for_score(0) is RiskBand.LOW


def test_score_capped_at_100(scored: dict[str, CanonicalEvidence]) -> None:
    for evidence in scored.values():
        assert evidence.decision.risk_score is not None
        assert 0 <= evidence.decision.risk_score <= 100


def test_pol005_blocked_and_actionability_limited(
    scored: dict[str, CanonicalEvidence],
) -> None:
    decision = scored["POL-005"].decision
    # Blockers are surfaced, never hidden.
    assert BlockerCode.MISSING_OWNER in decision.blockers
    assert BlockerCode.UNKNOWN_DOWNTIME_RISK in decision.blockers
    assert BlockerCode.UNKNOWN_DEPENDENCY_IMPACT in decision.blockers
    assert decision.actionability_score == 0
    # Risk is a separate view from actionability.
    assert decision.risk_score is not None and decision.risk_score > 0


def test_risk_separate_from_actionability(
    scored: dict[str, CanonicalEvidence],
) -> None:
    pol001 = scored["POL-001"].decision
    pol003 = scored["POL-003"].decision
    # POL-001 is highest risk but blocked (production runtime change);
    # POL-003 is lower risk but far more actionable (dry-run candidate).
    assert pol001.risk_score is not None and pol003.risk_score is not None
    assert pol001.risk_score > pol003.risk_score
    assert pol003.actionability_score is not None
    assert pol001.actionability_score is not None
    assert pol003.actionability_score > pol001.actionability_score
    assert BlockerCode.PRODUCTION_RUNTIME_CHANGE in pol001.blockers
    assert pol003.blockers == []


def test_blockers_do_not_lower_risk(scored: dict[str, CanonicalEvidence]) -> None:
    pol001 = scored["POL-001"]
    without_blockers = compute_risk_score(pol001)
    blockers = compute_blockers(pol001)
    assert blockers  # POL-001 has the production blocker
    assert compute_risk_score(pol001).score == without_blockers.score


def test_actionability_subtracts_blocker_weight(
    scored: dict[str, CanonicalEvidence],
) -> None:
    pol003 = scored["POL-003"]
    actionability = compute_actionability(pol003, [])
    with_blockers = compute_actionability(pol003, [BlockerCode.MISSING_OWNER])
    assert with_blockers.score == max(0, actionability.score - 10)


def test_ranked_order_differs_from_raw_severity_order(
    scored: dict[str, CanonicalEvidence],
) -> None:
    raw = sorted(
        scored.values(),
        key=lambda e: (
            -{"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Unknown": 0}[
                e.risk_signals.severity.value
            ],
            e.violation_id,
        ),
    )
    ranked = sorted(
        scored.values(),
        key=lambda e: (-(e.decision.risk_score or 0), e.violation_id),
    )
    raw_ids = [e.violation_id for e in raw]
    ranked_ids = [e.violation_id for e in ranked]
    assert raw_ids[0] == "POL-002"  # Critical raw severity leads
    assert ranked_ids[0] == "POL-001"  # agent ranking promotes the hero finding
    assert raw_ids != ranked_ids


def test_worklist_sort_api(client: TestClient, policy_fixture: dict[str, Any]) -> None:
    client.post("/api/ingest/policy", json=policy_fixture)
    raw = [v["violationId"] for v in client.get("/api/violations?sort=raw").json()]
    ranked = [
        v["violationId"] for v in client.get("/api/violations?sort=ranked").json()
    ]
    assert raw[0] == "POL-002"
    assert ranked[0] == "POL-001"
    assert raw != ranked


def test_rescore_endpoint(client: TestClient, policy_fixture: dict[str, Any]) -> None:
    client.post("/api/ingest/policy", json=policy_fixture)
    response = client.post("/api/violations/POL-001/score")
    assert response.status_code == 200
    body = response.json()
    assert body["riskScore"] == 100
    assert body["riskBand"] == "Critical"
    assert body["scoreRuleVersion"] == "risk-1.0.0"
    assert "production_runtime_change" in body["blockers"]
    assert body["actionabilityFactors"]

    missing = client.post("/api/violations/POL-404/score")
    assert missing.status_code == 404
