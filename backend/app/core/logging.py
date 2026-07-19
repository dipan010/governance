"""JSON logging with masking of secret-like values (RULES.md sections 6.15, 9.5)."""

import json
import logging
import sys
from datetime import UTC, datetime

SENSITIVE_KEY_MARKERS = (
    "secret",
    "token",
    "password",
    "credential",
    "connectionstring",
    "sas",
    "apikey",
    "accesskey",
    "certificate",
)

MASK = "***MASKED***"


def _is_sensitive(key: str) -> bool:
    normalized = key.lower().replace("_", "").replace("-", "")
    return any(marker in normalized for marker in SENSITIVE_KEY_MARKERS)


def mask_sensitive(payload: dict[str, object]) -> dict[str, object]:
    """Return a copy of payload with secret-like keys masked, recursively."""
    masked: dict[str, object] = {}
    for key, value in payload.items():
        if _is_sensitive(key):
            masked[key] = MASK
        elif isinstance(value, dict):
            masked[key] = mask_sensitive(value)
        else:
            masked[key] = value
    return masked


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
