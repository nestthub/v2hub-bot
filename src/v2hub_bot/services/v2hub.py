"""
Async wrapper over the v2hub-admin library (https://pypi.org/project/v2hub-admin/).

API:
    AsyncAdminClient(base_url, secret_key)
        .create_user(user_id)   → user.api_token
        .get_user(user_id)      → user
        .refresh_token(user_id) → user.api_token
        .delete_user(user_id)   → None
        .set_user_status(user_id, is_active) → user

Errors from v2hub:
    VPNAPIError, AuthenticationError, AuthorizationError
"""

import logging

from v2hub import AuthenticationError, AuthorizationError, VPNAPIError
from v2hub_admin import AsyncAdminClient
from v2hub_admin.models import UserResponse
from v2hub_bot.config import settings

logger = logging.getLogger(__name__)

# Re-export for handlers to catch
__all__ = ["AuthenticationError", "AuthorizationError", "V2HubError", "VPNAPIError", "v2hub_client"]

# Convenience alias so handlers can catch a single base class
V2HubError = VPNAPIError


def _make_client() -> AsyncAdminClient:
    return AsyncAdminClient(
        base_url=settings.v2hub_api_url,
        secret_key=settings.v2hub_secret_key,
    )


class V2HubService:
    """
    Thin async facade used by handlers.
    Uses a fresh context-manager client per call to stay stateless.
    """

    async def create_user(self, user_id: int) -> str:
        """Create user and return api_token."""
        async with _make_client() as admin:
            try:
                user: UserResponse = await admin.create_user(user_id)
            except:
                user = await admin.get_user(user_id)

            return user.api_token

    async def get_user(self, user_id: int) -> UserResponse | None:
        """Return user object or None if not found."""
        try:
            async with _make_client() as admin:
                return await admin.get_user(user_id)
        except VPNAPIError:
            return None

    async def refresh_token(self, user_id: int) -> str:
        """Rotate token for an existing user, return new api_token."""
        async with _make_client() as admin:
            user = await admin.refresh_token(user_id)
            return user.new_api_token


# Module-level singleton used by all handlers
v2hub_client = V2HubService()
