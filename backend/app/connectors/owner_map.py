"""Owner map connector (CMDB / owner CSV stand-in)."""

import csv
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel


class OwnerRecord(BaseModel):
    owner_team: str
    owner_email: str
    support_group: str | None = None
    business_app: str | None = None
    escalation_path: str | None = None


class OwnerMapConnector(Protocol):
    def get_owner(self, resource_id: str) -> OwnerRecord | None: ...

    def find_owner_by_app(self, app_tag: str) -> OwnerRecord | None: ...


class FixtureOwnerMap:
    def __init__(self, fixtures_dir: Path) -> None:
        self._by_resource: dict[str, OwnerRecord] = {}
        self._by_app: dict[str, OwnerRecord] = {}
        with (fixtures_dir / "owner_map.csv").open() as fh:
            for row in csv.DictReader(fh):
                record = OwnerRecord(
                    owner_team=row["ownerTeam"],
                    owner_email=row["ownerEmail"],
                    support_group=row.get("supportGroup"),
                    business_app=row.get("businessApp"),
                    escalation_path=row.get("escalationPath"),
                )
                self._by_resource[row["resourceId"].lower()] = record
                if record.business_app:
                    self._by_app[record.business_app.lower()] = record

    def get_owner(self, resource_id: str) -> OwnerRecord | None:
        return self._by_resource.get(resource_id.lower())

    def find_owner_by_app(self, app_tag: str) -> OwnerRecord | None:
        return self._by_app.get(app_tag.lower())
