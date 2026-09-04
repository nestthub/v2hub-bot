"""
Async wrapper over the v2hub-admin library (https://pypi.org/project/v2hub-admin/).

Everything about a user's v2hub account — API token, provider ownership,
provider authorizations — lives on the server and is always fetched fresh
here. The bot's own database never caches any of it; it only remembers
that a Telegram user_id has started the bot.

API:
    AsyncAdminClient(base_url, secret_key)
        .create_user(user_id)   → user
        .get_user(user_id)      → user (has .user_hash, used as owner_hash)
        .refresh_token(user_id) → user.new_api_token
        .delete_user(user_id)   → None
        .set_user_status(user_id, is_active) → user

        .get_providers()                                → provider_name -> provider_hash
        .get_provider(provider_hash)                     → provider
        .get_provider_by_name(provider_name)              → provider | 404
        .get_provider_by_owner_id(owner_id)                → provider | 404
        .create_provider(owner_hash, provider_name, provider_url) → provider (incl. api_token)
        .delete_provider(provider_hash)                     → None
        .update_provider_name(provider_hash, provider_name)    → provider
        .update_provider_url(provider_hash, provider_url)      → provider
        .refresh_provider_token(provider_hash)              → new_api_token

        .get_user_providers(user_id)                         → all connections for a user
        .get_provider_authorization(provider_name, user_id)     → auth | 404
        .process_provider_authorization(user_id, provider_name, hmac) → auth
        .approve_provider_authorization(user_id, provider_name) → auth
        .reject_provider_authorization(user_id, provider_name)  → auth

Errors from v2hub:
    VPNAPIError, AuthenticationError, AuthorizationError, NotFoundError, ConflictError
"""

import logging
from datetime import datetime
from typing import Literal

from v2hub import AuthenticationError, AuthorizationError, ConflictError, NotFoundError, VPNAPIError
from v2hub.models import ConnectionsResponse
from v2hub_admin import AsyncAdminClient
from v2hub_admin.models import (
    AllProvidersResponse,
    ProviderAuthorizationInfoResponse,
    ProviderResponse,
    StatsResponse,
    UserResponse,
)
from v2hub_bot.config import settings

logger = logging.getLogger(__name__)

# Re-export for handlers to catch
__all__ = [
    "AllProvidersResponse",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "NotFoundError",
    "ProviderAuthorizationInfoResponse",
    "ProviderResponse",
    "V2HubError",
    "VPNAPIError",
    "v2hub_client",
]

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

    Nothing here is cached in the bot's own database: user tokens,
    provider ownership, and authorization state are always read fresh
    from the Admin API.
    """

    # ── Users ────────────────────────────────────────────────────────────────

    async def create_user(self, user_id: int) -> UserResponse:
        """Create user and return api_token."""
        async with _make_client() as admin:
            try:
                user: UserResponse = await admin.create_user(user_id)
            except VPNAPIError:
                user = await admin.get_user(user_id)

            return user

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
            result = await admin.refresh_token(user_id)
            return result.new_api_token

    async def delete_user(self, user_id: int) -> None:
        """Permanently delete a user's v2hub account.

        The server cascades this to owned data according to its own
        rules; the bot additionally forgets the local `started the bot`
        record for this user_id (see db.crud.delete_local_user).
        """
        async with _make_client() as admin:
            await admin.delete_user(user_id)

    # ── Providers ────────────────────────────────────────────────────────────
    # Nothing about a provider (hash, token, url, status) or about who
    # owns it is cached in the bot's own database: it's always fetched
    # fresh here from the Admin API.

    async def get_provider_by_name(self, provider_name: str) -> ProviderResponse | None:
        """Look up a provider by its public name, or None if it doesn't exist."""
        async with _make_client() as admin:
            try:
                return await admin.get_provider_by_name(provider_name)
            except NotFoundError:
                return None

    async def get_provider_by_owner_id(self, owner_id: int) -> ProviderResponse | None:
        """Look up the provider owned by this bot user, or None if they don't own one."""
        async with _make_client() as admin:
            try:
                return await admin.get_provider_by_owner_id(owner_id)
            except NotFoundError:
                return None

    async def get_user_connections(self, user_id: int) -> ConnectionsResponse:
        """Return all known provider connections/authorizations for a user."""
        async with _make_client() as admin:
            return await admin.get_user_providers(user_id)

    async def create_provider(
        self,
        owner_user_id: int,
        provider_name: str,
        provider_url: str | None = None,
    ) -> ProviderResponse:
        """Create a new provider account owned by the given bot user.

        Looks up the owner's `user_hash` (required by the Admin API as
        `owner_hash`) from their `user_id` first. The owner must already
        exist as a regular v2hub user — call `create_user`/`get_user`
        beforehand if needed.

        Only meant to be called by an administrator, e.g. after confirming
        an applicant out-of-band; never as a side effect of user actions.

        Raises:
            NotFoundError: the owner has no v2hub account yet.
            ConflictError: a provider with this name already exists.
        """
        async with _make_client() as admin:
            owner = await admin.get_user(owner_user_id)
            return await admin.create_provider(
                owner_hash=owner.user_hash,
                provider_name=provider_name,
                provider_url=provider_url,
            )

    async def refresh_provider_token(self, provider_hash: str) -> str:
        """Rotate a provider's API token, return the new token."""
        async with _make_client() as admin:
            result = await admin.refresh_provider_token(provider_hash=provider_hash)
            return result.new_api_token

    # ── Provider administration (admin panel CRUD) ──────────────────────────
    # Full lifecycle management for admins: list, inspect, update, and
    # delete any provider account, regardless of who owns it.

    async def get_all_providers(self) -> AllProvidersResponse:
        """Return every provider as a provider_name -> provider_hash mapping."""
        async with _make_client() as admin:
            return await admin.get_providers()

    async def get_provider_by_hash(self, provider_hash: str) -> ProviderResponse | None:
        """Look up a provider by its hash, or None if it doesn't exist."""
        async with _make_client() as admin:
            try:
                return await admin.get_provider(provider_hash)
            except NotFoundError:
                return None

    async def delete_provider(self, provider_hash: str) -> None:
        """Permanently delete a provider account.

        The server cascades this to provider-owned data according to its
        own rules; the bot performs no local cleanup since it never
        caches provider data.
        """
        async with _make_client() as admin:
            await admin.delete_provider(provider_hash=provider_hash)

    async def update_provider_name(
        self, provider_hash: str, provider_name: str
    ) -> ProviderResponse:
        """Rename a provider.

        Raises:
            ConflictError: the new name is already in use.
        """
        async with _make_client() as admin:
            return await admin.update_provider_name(
                provider_hash=provider_hash, provider_name=provider_name
            )

    async def update_provider_url(
        self, provider_hash: str, provider_url: str | None
    ) -> ProviderResponse:
        """Update (or clear, with None) a provider's URL."""
        async with _make_client() as admin:
            return await admin.update_provider_url(
                provider_hash=provider_hash, provider_url=provider_url
            )

    # ── Provider authorization ──────────────────────────────────────────────

    async def get_provider_authorization(
        self, provider_name: str, user_id: int
    ) -> ProviderAuthorizationInfoResponse | None:
        """Return current authorization state, or None if it doesn't exist."""
        async with _make_client() as admin:
            try:
                return await admin.get_provider_authorization(
                    provider_name=provider_name,
                    user_id=user_id,
                )
            except NotFoundError:
                return None

    async def process_provider_authorization(
        self,
        user_id: int,
        provider_name: str,
        hmac: str | None = None,
    ) -> ProviderAuthorizationInfoResponse:
        """Process a `conn_*` deep link. The hmac is forwarded unchanged."""
        async with _make_client() as admin:
            return await admin.process_provider_authorization(
                user_id=user_id,
                provider_name=provider_name,
                hmac=hmac,
            )

    async def approve_provider_authorization(
        self, user_id: int, provider_name: str
    ) -> ProviderAuthorizationInfoResponse:
        """Approve a PENDING authorization."""
        async with _make_client() as admin:
            return await admin.approve_provider_authorization(
                user_id=user_id,
                provider_name=provider_name,
            )

    async def reject_provider_authorization(
        self, user_id: int, provider_name: str
    ) -> ProviderAuthorizationInfoResponse:
        """Reject a PENDING request, or revoke/delete an existing authorization."""
        async with _make_client() as admin:
            return await admin.reject_provider_authorization(
                user_id=user_id,
                provider_name=provider_name,
            )

    async def get_stats(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> StatsResponse:
        """Retrieve server statistics for the specified date range or period."""
        async with _make_client() as admin:
            return await admin.get_stats(start_date=start_date, end_date=end_date, period=period)


# Module-level singleton used by all handlers
v2hub_client = V2HubService()
