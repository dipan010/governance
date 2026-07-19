"""Defender for Cloud connector (severity and regulatory control enrichment)."""

import json
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DefenderAssessment(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="ignore"
    )

    resource_id: str
    policy_id: str
    severity: str
    regulatory_control: str | None = None
    recommendation: str | None = None


class DefenderConnector(Protocol):
    def get_assessment(
        self, resource_id: str, policy_id: str
    ) -> DefenderAssessment | None: ...


class FixtureDefender:
    def __init__(self, fixtures_dir: Path) -> None:
        payload: dict[str, Any] = json.loads(
            (fixtures_dir / "defender_assessments.json").read_text()
        )
        self._by_key = {
            (a["resourceId"].lower(), a["policyId"]): DefenderAssessment.model_validate(
                a
            )
            for a in payload["assessments"]
        }

    def get_assessment(
        self, resource_id: str, policy_id: str
    ) -> DefenderAssessment | None:
        return self._by_key.get((resource_id.lower(), policy_id))
