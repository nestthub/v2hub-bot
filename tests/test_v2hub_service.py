from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from v2hub import VPNAPIError
from v2hub_bot.services.v2hub import V2HubService

pytestmark = pytest.mark.unit


def _make_fake_client(user_response: MagicMock | None = None) -> MagicMock:
    """Build a MagicMock standing in for AsyncAdminClient's async context manager."""
    client = MagicMock()
    admin = AsyncMock()
    if user_response is not None:
        admin.create_user.return_value = user_response
        admin.get_user.return_value = user_response
        admin.refresh_token.return_value = user_response
    client.__aenter__ = AsyncMock(return_value=admin)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.mark.asyncio
async def test_create_user_returns_token_on_success() -> None:
    fake_user = MagicMock(api_token="fresh-token")
    fake_client = _make_fake_client(fake_user)

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        token = await service.create_user(user_id=1)

    assert token == "fresh-token"


@pytest.mark.asyncio
async def test_create_user_falls_back_to_get_user_if_already_exists() -> None:
    fake_user = MagicMock(api_token="already-existing-token")
    fake_client = _make_fake_client()
    admin = await fake_client.__aenter__()
    admin.create_user.side_effect = VPNAPIError("user already exists")
    admin.get_user.return_value = fake_user

    with patch("v2hub_bot.services.v2hub._make_client", return_value=fake_client):
        service = V2HubService()
        token = await service.create_user(user_id=1)

    assert token == "already-existing-token"
    admin.get_user.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_user_returns_user_on_success() -> None:
    fake_user = MagicMock(api_token="tok")
    fake_client = _make_fake_client(fake_user)

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
    fake_user = MagicMock(new_api_token="rotated-token")
    fake_client = _make_fake_client(fake_user)

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
