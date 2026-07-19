"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import APP_NAME, APP_VERSION, get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)
    app = FastAPI(title=APP_NAME, version=APP_VERSION)
    app.include_router(health_router)
    return app


app = create_app()
