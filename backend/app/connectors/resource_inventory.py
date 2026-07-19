"""Resource inventory connector (Azure Resource Graph stand-in).

The Protocol is the seam where the fixture implementation is swapped for a
real Azure Resource Graph client later without touching the enrichment agent.
"""

import json
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ResourceHistory(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    first_seen: str | None = None
    previous_fix: str | None = None
    recurrence_count: int = 0


class ResourceRemediation(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    remediation_supported: bool = False
    required_permission: str | None = None
    permission_available: bool = False
    restart_risk: str = "Unknown"
    downtime_risk: str = "Unknown"
    cost_impact: str = "Unknown"


class ResourceInventoryRecord(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="ignore"
    )

    resource_id: str
    resource_type: str | None = None
    subscription_id: str | None = None
    resource_group: str | None = None
    location: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    environment: str = "Unknown"
    production_criticality: str = "Unknown"
    data_classification: str = "Unknown"
    internet_exposure: bool | None = None
    identity_impact: bool | None = None
    dependency_count: int | None = None
    dependency_impact_known: bool = True
    remediation: ResourceRemediation | None = None
    history: ResourceHistory | None = None


class ResourceInventoryConnector(Protocol):
    def get_resource(self, resource_id: str) -> ResourceInventoryRecord | None: ...


class FixtureResourceInventory:
    def __init__(self, fixtures_dir: Path) -> None:
        payload: dict[str, Any] = json.loads(
            (fixtures_dir / "resource_inventory.json").read_text()
        )
        self._by_id = {
            record["resourceId"].lower(): ResourceInventoryRecord.model_validate(record)
            for record in payload["resources"]
        }

    def get_resource(self, resource_id: str) -> ResourceInventoryRecord | None:
        return self._by_id.get(resource_id.lower())
