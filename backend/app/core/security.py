"""Role model and authorization dependency scaffold.

Roles follow RULES.md section 9.8. In local/hackathon mode the dependency
resolves to ADMIN so the demo flows work; real authentication (Entra ID /
managed identity) is wired at deployment time (P16). Write APIs added in
later prompts must depend on require_role.
"""

from collections.abc import Callable
from enum import StrEnum

from fastapi import HTTPException, status

from app.core.config import get_settings


class Role(StrEnum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    APPROVER = "approver"
    OPERATOR = "operator"
    AUDITOR = "auditor"
    ADMIN = "admin"


def get_current_role() -> Role:
    settings = get_settings()
    if settings.environment in ("local", "test"):
        return Role.ADMIN
    # Real identity resolution is intentionally not implemented yet; deny by
    # default rather than silently granting access outside local/test.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication is not configured for this environment",
    )


def require_role(*allowed: Role) -> Callable[[], Role]:
    def dependency() -> Role:
        role = get_current_role()
        if role is not Role.ADMIN and role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is not permitted for this action",
            )
        return role

    return dependency
