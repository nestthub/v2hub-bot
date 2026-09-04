from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from v2hub import ConflictError, NotFoundError, VPNAPIError
from v2hub_admin import AsyncAdminClient
from v2hub_bot.services.v2hub import V2HubService, _make_client

pytestmark = pytest.mark.unit


def test_make_client_builds_admin_client_from_settings() -> None:
    client = _make_client()

    assert isinstance(client, AsyncAdminClient)


def _make_fake_client() -> MagicMock:
    """Build a MagicMock standing in for AsyncAdminClient's async context manager."""
    client = MagicMock()
    admin = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=admin)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


# ── Users ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_user_returns_user_on_success() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    fake_user = MagicMock(api_token="fresh-token")
    admin.create_user.return_value = fake_user

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        user = await service.create_user(user_id=1)

    assert user is fake_user
    assert user.api_token == "fresh-token"


@pytest.mark.asyncio
async def test_create_user_falls_back_to_get_user_if_already_exists() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.create_user.side_effect = VPNAPIError("user already exists")
    fake_user = MagicMock(api_token="already-existing-token")
    admin.get_user.return_value = fake_user

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        user = await service.create_user(user_id=1)

    assert user is fake_user
    assert user.api_token == "already-existing-token"
    admin.get_user.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_user_returns_user_on_success() -> None:
    fake_user = MagicMock(api_token="tok")
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_user.return_value = fake_user

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.get_user(user_id=5)

    assert result is fake_user


@pytest.mark.asyncio
async def test_get_user_returns_none_on_vpn_api_error() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_user.side_effect = VPNAPIError("not found")

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.get_user(user_id=5)

    assert result is None


@pytest.mark.asyncio
async def test_refresh_token_returns_new_token() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.refresh_token.return_value = MagicMock(new_api_token="rotated-token")

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        token = await service.refresh_token(user_id=7)

    assert token == "rotated-token"


@pytest.mark.asyncio
async def test_refresh_token_propagates_error() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.refresh_token.side_effect = VPNAPIError("refresh failed")

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        with pytest.raises(VPNAPIError):
            await service.refresh_token(user_id=7)


# ── Providers ────────────────────────────────────────────────────────────────
# Provider lookups (by name, by owner) go straight to the server now — there
# is no local provider_hashes registry step in between.


@pytest.mark.asyncio
async def test_get_provider_by_name_returns_provider() -> None:
    fake_provider = MagicMock(provider_name="vpn123")
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_provider_by_name.return_value = fake_provider

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.get_provider_by_name("vpn123")

    assert result is fake_provider
    admin.get_provider_by_name.assert_awaited_once_with("vpn123")


@pytest.mark.asyncio
async def test_get_provider_by_name_returns_none_on_not_found() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_provider_by_name.side_effect = NotFoundError("gone")

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.get_provider_by_name("unknown")

    assert result is None


@pytest.mark.asyncio
async def test_get_provider_by_owner_id_returns_provider() -> None:
    fake_provider = MagicMock(provider_name="vpn123")
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_provider_by_owner_id.return_value = fake_provider

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.get_provider_by_owner_id(42)

    assert result is fake_provider
    admin.get_provider_by_owner_id.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_get_provider_by_owner_id_returns_none_when_user_owns_no_provider() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_provider_by_owner_id.side_effect = NotFoundError("no provider")

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.get_provider_by_owner_id(42)

    assert result is None


@pytest.mark.asyncio
async def test_create_provider_looks_up_owner_hash_then_creates() -> None:
    fake_owner = MagicMock(user_hash="owner-hash-1")
    fake_provider = MagicMock(provider_name="vpn123")
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_user.return_value = fake_owner
    admin.create_provider.return_value = fake_provider

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.create_provider(
            owner_user_id=42, provider_name="vpn123", provider_url="https://vpn123.example.com"
        )

    assert result is fake_provider
    admin.get_user.assert_awaited_once_with(42)
    admin.create_provider.assert_awaited_once_with(
        owner_hash="owner-hash-1",
        provider_name="vpn123",
        provider_url="https://vpn123.example.com",
    )


@pytest.mark.asyncio
async def test_create_provider_propagates_not_found_when_owner_has_no_account() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_user.side_effect = NotFoundError("no such user")

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        with pytest.raises(NotFoundError):
            await service.create_provider(owner_user_id=42, provider_name="vpn123")

    admin.create_provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_provider_propagates_conflict_when_name_taken() -> None:
    fake_owner = MagicMock(user_hash="owner-hash-1")
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_user.return_value = fake_owner
    admin.create_provider.side_effect = ConflictError("provider already exists")

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        with pytest.raises(ConflictError):
            await service.create_provider(owner_user_id=42, provider_name="vpn123")


@pytest.mark.asyncio
async def test_refresh_provider_token_returns_new_token() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.refresh_provider_token.return_value = MagicMock(new_api_token="new-provider-token")

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.refresh_provider_token("provider-hash-1")

    assert result == "new-provider-token"
    admin.refresh_provider_token.assert_awaited_once_with(provider_hash="provider-hash-1")


@pytest.mark.asyncio
async def test_get_user_connections_returns_connections_response() -> None:
    fake_connections = MagicMock()
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_user_providers.return_value = fake_connections

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.get_user_connections(user_id=1)

    assert result is fake_connections
    admin.get_user_providers.assert_awaited_once_with(1)


# ── Provider authorization ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_provider_authorization_returns_state() -> None:
    fake_auth = MagicMock(status="pending")
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_provider_authorization.return_value = fake_auth

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.get_provider_authorization("vpn123", user_id=1)

    assert result is fake_auth
    admin.get_provider_authorization.assert_awaited_once_with(provider_name="vpn123", user_id=1)


@pytest.mark.asyncio
async def test_get_provider_authorization_returns_none_on_404() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.get_provider_authorization.side_effect = NotFoundError("no auth record")

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.get_provider_authorization("vpn123", user_id=1)

    assert result is None


@pytest.mark.asyncio
async def test_process_provider_authorization_forwards_hmac_unchanged() -> None:
    fake_auth = MagicMock(status="pending")
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.process_provider_authorization.return_value = fake_auth

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.process_provider_authorization(
            user_id=1, provider_name="vpn123", hmac="raw-hmac-value"
        )

    assert result is fake_auth
    admin.process_provider_authorization.assert_awaited_once_with(
        user_id=1, provider_name="vpn123", hmac="raw-hmac-value"
    )


@pytest.mark.asyncio
async def test_approve_provider_authorization_success() -> None:
    fake_auth = MagicMock(status="approved")
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.approve_provider_authorization.return_value = fake_auth

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.approve_provider_authorization(user_id=1, provider_name="vpn123")

    assert result is fake_auth


@pytest.mark.asyncio
async def test_approve_provider_authorization_propagates_conflict() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.approve_provider_authorization.side_effect = ConflictError("not pending")

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        with pytest.raises(ConflictError):
            await service.approve_provider_authorization(user_id=1, provider_name="vpn123")


@pytest.mark.asyncio
async def test_reject_provider_authorization_success() -> None:
    fake_auth = MagicMock(status=None)
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.reject_provider_authorization.return_value = fake_auth

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        result = await service.reject_provider_authorization(user_id=1, provider_name="vpn123")

    assert result is fake_auth


@pytest.mark.asyncio
async def test_delete_user_calls_admin_delete_user() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        await service.delete_user(user_id=7)

    admin.delete_user.assert_awaited_once_with(7)


@pytest.mark.asyncio
async def test_delete_user_propagates_not_found() -> None:
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.delete_user.side_effect = NotFoundError("no such user")

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        with pytest.raises(NotFoundError):
            await service.delete_user(user_id=7)
