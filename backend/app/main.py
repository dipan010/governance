"""FastAPI application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.approvals import router as approvals_router
from app.api.artifacts import router as artifacts_router
from app.api.audit import router as audit_router
from app.api.dashboard import router as dashboard_router
from app.api.findings import router as findings_router
from app.api.health import router as health_router
from app.api.routes import router as routes_router
from app.api.scoring import router as scoring_router
from app.api.verification import router as verification_router
from app.core.config import APP_NAME, APP_VERSION, get_settings
from app.core.logging import configure_logging
from app.db.models import Base
from app.db.session import get_engine


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Local/test convenience; deployed schema is owned by Alembic migrations.
    if get_settings().environment in ("local", "test"):
        Base.metadata.create_all(get_engine())
    yield


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)
    app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=_lifespan)
    app.include_router(health_router)
    app.include_router(findings_router)
    app.include_router(scoring_router)
    app.include_router(routes_router)
    app.include_router(approvals_router)
    app.include_router(artifacts_router)
    app.include_router(verification_router)
    app.include_router(audit_router)
    app.include_router(dashboard_router)
    return app


app = create_app()
