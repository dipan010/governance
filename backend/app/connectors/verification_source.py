"""Verification source connector (before/after state and query stand-in)."""

import json
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class VerificationTemplate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="ignore"
    )

    finding_ref: str
    resource_id: str
    verification_query: str
    expected_compliant_value: str
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None


class VerificationSourceConnector(Protocol):
    def get_template(
        self, finding_ref: str, resource_id: str
    ) -> VerificationTemplate | None: ...


class FixtureVerificationSource:
    def __init__(self, fixtures_dir: Path) -> None:
        payload: dict[str, Any] = json.loads(
            (fixtures_dir / "before_after_state.json").read_text()
        )
        templates = [
            VerificationTemplate.model_validate(state) for state in payload["states"]
        ]
        self._by_ref = {t.finding_ref: t for t in templates}
        self._by_resource = {t.resource_id.lower(): t for t in templates}

    def get_template(
        self, finding_ref: str, resource_id: str
    ) -> VerificationTemplate | None:
        return self._by_ref.get(finding_ref) or self._by_resource.get(
            resource_id.lower()
        )
