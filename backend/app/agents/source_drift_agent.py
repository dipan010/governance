"""Source-of-Truth Drift Agent.

Compares the failing runtime property with the IaC repo map's current and
expected source values, sets sourceDriftLikely and sourceConfidence, and
identifies whether a runtime-only patch would be temporary (RULES.md 2.4:
prefer source repair over runtime patching for recurring issues).
"""

from pydantic import BaseModel, Field

from app.connectors.repo_map import RepoMapConnector
from app.domain.enums import ConfidenceLevel, coerce_enum
from app.domain.evidence_schema import CanonicalEvidence


class SourceDriftFinding(BaseModel):
    source_property: str
    runtime_property: str
    current_source_value: str
    expected_source_value: str


class SourceDriftAnalysis(BaseModel):
    violation_id: str
    repo_url: str
    repo_path: str
    module: str | None = None
    code_owner: str | None = None
    pipeline: str | None = None
    source_drift_likely: bool
    source_confidence: ConfidenceLevel
    drifted_properties: list[SourceDriftFinding] = Field(default_factory=list)
    runtime_patch_temporary: bool
    verification_query: str | None = None
    expected_compliant_value: str | None = None


class SourceDriftAgent:
    def __init__(self, repos: RepoMapConnector) -> None:
        self._repos = repos

    def analyze(self, evidence: CanonicalEvidence) -> SourceDriftAnalysis | None:
        """Analyze source drift for one violation. Returns None when the
        resource has no repo mapping (source fix cannot be proposed)."""
        mapping = self._repos.get_mapping(evidence.resource_facts.resource_id)
        if mapping is None:
            evidence.history.source_confidence = ConfidenceLevel.UNKNOWN
            return None

        drifted = [
            SourceDriftFinding(
                source_property=name,
                runtime_property=prop.runtime_property,
                current_source_value=prop.current_source_value,
                expected_source_value=prop.expected_source_value,
            )
            for name, prop in mapping.drifted_properties().items()
        ]
        drift_likely = bool(drifted)
        confidence = coerce_enum(
            ConfidenceLevel, mapping.source_confidence, ConfidenceLevel.UNKNOWN
        )

        # The agent is authoritative for these evidence fields.
        evidence.history.source_drift_likely = drift_likely
        evidence.history.source_confidence = confidence

        return SourceDriftAnalysis(
            violation_id=evidence.violation_id,
            repo_url=mapping.repo_url,
            repo_path=mapping.repo_path,
            module=mapping.module,
            code_owner=mapping.code_owner,
            pipeline=mapping.pipeline,
            source_drift_likely=drift_likely,
            source_confidence=confidence,
            drifted_properties=drifted,
            # A runtime-only patch is temporary while the source still
            # contains the bad value: the next deployment reintroduces it.
            runtime_patch_temporary=drift_likely,
            verification_query=evidence.verification.verification_query,
            expected_compliant_value=evidence.verification.expected_compliant_value,
        )
