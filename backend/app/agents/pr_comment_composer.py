"""PR/comment preview composer.

Renders a deterministic markdown preview of the source fix. This is a
PREVIEW ONLY: no branch is created, no PR is opened, nothing is posted to
any repository. Executing a source change requires explicit human approval
through the approval gate (RULES.md 2.2).
"""

from pydantic import BaseModel, Field

from app.agents.source_drift_agent import SourceDriftAnalysis
from app.domain.evidence_schema import CanonicalEvidence

APPROVAL_NOTICE = (
    "This is a preview only. No branch, commit, or pull request is created "
    "without explicit human approval through the approval gate."
)

TEMPORARY_PATCH_WARNING = (
    "A runtime-only patch would be TEMPORARY: the IaC source still contains "
    "the non-compliant value, so the next deployment would reintroduce the "
    "violation. Fix the source."
)


class PrCommentPreview(BaseModel):
    violation_id: str
    repo_url: str
    repo_path: str
    code_owner: str | None
    title: str
    body: str
    expected_after_state: dict[str, str] = Field(default_factory=dict)
    is_preview: bool = True


def compose_pr_comment(
    evidence: CanonicalEvidence, analysis: SourceDriftAnalysis
) -> PrCommentPreview:
    if not analysis.source_drift_likely:
        raise ValueError(
            "PR/comment preview requires detected source drift; "
            f"{analysis.violation_id} has none"
        )

    expected_after_state = {
        finding.source_property: finding.expected_source_value
        for finding in analysis.drifted_properties
    }

    property_rows = "\n".join(
        f"| `{f.source_property}` | `{f.current_source_value}` | "
        f"`{f.expected_source_value}` | `{f.runtime_property}` |"
        for f in analysis.drifted_properties
    )

    policy = evidence.policy_evidence
    body = f"""## Source fix required: {policy.policy_name}

**Violation:** {analysis.violation_id}
**Resource:** `{evidence.resource_facts.resource_id}`
**Failure reason:** {policy.failure_reason}
**Repo:** {analysis.repo_url}
**File:** `{analysis.repo_path}`
**Module:** `{analysis.module}`
**CODEOWNER:** {analysis.code_owner}
**Pipeline:** `{analysis.pipeline}`
**Source confidence:** {analysis.source_confidence.value}

### Failing properties

| Source property | Current value | Expected value | Runtime property |
|---|---|---|---|
{property_rows}

### Expected after-state

{_render_after_state(expected_after_state)}
Expected compliant value: `{analysis.expected_compliant_value}`

### Verification

```text
{analysis.verification_query}
```

### Why not a runtime patch?

{TEMPORARY_PATCH_WARNING}

---
{APPROVAL_NOTICE}
"""
    return PrCommentPreview(
        violation_id=analysis.violation_id,
        repo_url=analysis.repo_url,
        repo_path=analysis.repo_path,
        code_owner=analysis.code_owner,
        title=(
            f"fix({analysis.module}): {analysis.violation_id} — {policy.policy_name}"
        ),
        body=body,
        expected_after_state=expected_after_state,
    )


def _render_after_state(after_state: dict[str, str]) -> str:
    return "\n".join(f"- `{prop}` = `{value}`" for prop, value in after_state.items())
