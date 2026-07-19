"""PR/comment preview composer tests."""

from typing import Any

import pytest

from app.agents.core_policy_agent import normalize_policy_finding
from app.agents.enrichment_agent import EnrichmentAgent
from app.agents.pr_comment_composer import (
    APPROVAL_NOTICE,
    TEMPORARY_PATCH_WARNING,
    compose_pr_comment,
)
from app.agents.source_drift_agent import SourceDriftAgent, SourceDriftAnalysis
from app.connectors.defender import FixtureDefender
from app.connectors.owner_map import FixtureOwnerMap
from app.connectors.repo_map import FixtureRepoMap
from app.connectors.resource_inventory import FixtureResourceInventory
from app.connectors.verification_source import FixtureVerificationSource
from app.domain.evidence_schema import CanonicalEvidence
from tests.conftest import FIXTURES


@pytest.fixture
def pol001_with_analysis(
    policy_fixture: dict[str, Any],
) -> tuple[CanonicalEvidence, SourceDriftAnalysis]:
    evidence = normalize_policy_finding(policy_fixture["findings"][0]).evidence
    EnrichmentAgent(
        inventory=FixtureResourceInventory(FIXTURES),
        owners=FixtureOwnerMap(FIXTURES),
        repos=FixtureRepoMap(FIXTURES),
        defender=FixtureDefender(FIXTURES),
        verification=FixtureVerificationSource(FIXTURES),
    ).enrich(evidence)
    analysis = SourceDriftAgent(repos=FixtureRepoMap(FIXTURES)).analyze(evidence)
    assert analysis is not None
    return evidence, analysis


def test_preview_contains_all_required_fields(
    pol001_with_analysis: tuple[CanonicalEvidence, SourceDriftAnalysis],
) -> None:
    evidence, analysis = pol001_with_analysis
    preview = compose_pr_comment(evidence, analysis)

    assert preview.violation_id == "POL-001"
    assert preview.repo_url == "https://github.com/dipan010/cloudgov-iac"
    assert preview.repo_path == "terraform/storage/payments/storage_account.tf"
    assert preview.code_owner == "@payments-platform"

    body = preview.body
    assert "terraform/storage/payments/storage_account.tf" in body
    assert "payments-storage" in body  # module
    assert "@payments-platform" in body  # CODEOWNER
    assert "public_network_access_enabled" in body  # failing property
    assert "`true`" in body  # current value
    assert "`false`" in body  # expected value
    assert evidence.verification.verification_query is not None
    assert evidence.verification.verification_query in body  # verification query


def test_preview_includes_expected_after_state(
    pol001_with_analysis: tuple[CanonicalEvidence, SourceDriftAnalysis],
) -> None:
    evidence, analysis = pol001_with_analysis
    preview = compose_pr_comment(evidence, analysis)
    assert preview.expected_after_state == {
        "public_network_access_enabled": "false",
        "network_rules.default_action": "Deny",
    }
    assert "Expected after-state" in preview.body
    assert "publicNetworkAccess == Disabled" in preview.body


def test_no_real_pr_only_preview(
    pol001_with_analysis: tuple[CanonicalEvidence, SourceDriftAnalysis],
) -> None:
    evidence, analysis = pol001_with_analysis
    preview = compose_pr_comment(evidence, analysis)
    assert preview.is_preview is True
    assert APPROVAL_NOTICE in preview.body
    # Evidence action state is untouched: no PR URL recorded.
    assert evidence.action_state.pr_url is None


def test_runtime_patch_labelled_temporary(
    pol001_with_analysis: tuple[CanonicalEvidence, SourceDriftAnalysis],
) -> None:
    evidence, analysis = pol001_with_analysis
    preview = compose_pr_comment(evidence, analysis)
    assert TEMPORARY_PATCH_WARNING in preview.body
    assert "TEMPORARY" in preview.body


def test_compose_requires_source_drift(
    pol001_with_analysis: tuple[CanonicalEvidence, SourceDriftAnalysis],
) -> None:
    evidence, analysis = pol001_with_analysis
    no_drift = analysis.model_copy(
        update={"source_drift_likely": False, "drifted_properties": []}
    )
    with pytest.raises(ValueError, match="requires detected source drift"):
        compose_pr_comment(evidence, no_drift)
