"""Health and version endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import APP_NAME, APP_VERSION, get_settings
from app.domain.evidence_schema import SCHEMA_VERSION

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    environment: str


class VersionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    version: str
    schema_version: str = Field(alias="schemaVersion")


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=get_settings().environment)


@router.get("/api/version", response_model_by_alias=True)
def version() -> VersionResponse:
    return VersionResponse(
        name=APP_NAME, version=APP_VERSION, schema_version=SCHEMA_VERSION
    )
