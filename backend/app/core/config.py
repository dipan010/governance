"""Application settings.

Secrets are never committed: values come from environment variables or, in
Azure, from Key Vault via managed identity (wired in P16). The local default
database is SQLite; Azure Database for PostgreSQL is the deployment target.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_NAME = "policy-compliance-drift-agent"
APP_VERSION = "0.1.0"

DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parents[3] / "data" / "fixtures"
DEFAULT_EVIDENCE_DIR = Path(__file__).resolve().parents[3] / "data" / "evidence_packets"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PCDA_", env_file=".env", extra="ignore"
    )

    environment: str = "local"
    database_url: str = "sqlite+pysqlite:///./local.db"
    key_vault_uri: str | None = None
    log_level: str = "INFO"
    fixtures_dir: Path = DEFAULT_FIXTURES_DIR
    evidence_packets_dir: Path = DEFAULT_EVIDENCE_DIR


@lru_cache
def get_settings() -> Settings:
    return Settings()
