"""IaC repo map connector (source-of-truth mapping stand-in)."""

import json
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SourceProperty(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    current_source_value: str
    expected_source_value: str
    runtime_property: str


class RepoMapping(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="ignore"
    )

    resource_id: str
    repo_url: str
    repo_path: str
    module: str | None = None
    code_owner: str | None = None
    pipeline: str | None = None
    source_confidence: str = "Unknown"
    properties: dict[str, SourceProperty] = Field(default_factory=dict)

    def drifted_properties(self) -> dict[str, SourceProperty]:
        """Source properties whose current value differs from the expected one."""
        return {
            name: prop
            for name, prop in self.properties.items()
            if prop.current_source_value != prop.expected_source_value
        }


class RepoMapConnector(Protocol):
    def get_mapping(self, resource_id: str) -> RepoMapping | None: ...


class FixtureRepoMap:
    def __init__(self, fixtures_dir: Path) -> None:
        payload: dict[str, Any] = json.loads(
            (fixtures_dir / "repo_map.json").read_text()
        )
        self._by_id = {
            mapping["resourceId"].lower(): RepoMapping.model_validate(mapping)
            for mapping in payload["mappings"]
        }

    def get_mapping(self, resource_id: str) -> RepoMapping | None:
        return self._by_id.get(resource_id.lower())
