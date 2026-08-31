from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TgUser

from v2hub.models import (
    ConnectionResponse,
    ConnectionsResponse,
    ProviderAuthorizationStatus,
)
from v2hub_bot.handlers import provider as provider_handler
from v2hub_bot.services import ConflictError, NotFoundError, V2HubError

pytestmark = pytest.mark.unit


def _tg_user(user_id: int = 1) -> MagicMock:
    user = MagicMock(spec=TgUser)
    user.id = user_id
    user.first_name = "Alice"
    return user


def _message(user: MagicMock | None = None) -> MagicMock:
    message = MagicMock(spec=Message)
    message.from_user = user
    message.answer = AsyncMock()
    return message


def _callback(user: MagicMock, data: str) -> MagicMock:
    call = MagicMock(spec=CallbackQuery)
    call.from_user = user
    call.data = data
    call.message = MagicMock(spec=Message)
    call.message.edit_text = AsyncMock()
    call.answer = AsyncMock()
    return call


# ── Status helpers ────────────────────────────────────────────────────────────


def test_status_label_none_means_not_authorized() -> None:
    assert provider_handler._status_label(None) == provider_handler.t.PROVIDER_STATUS_NONE


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (
            ProviderAuthorizationStatus.PENDING,
            provider_handler.t.PROVIDER_STATUS_PENDING,
        ),
        (
            ProviderAuthorizationStatus.APPROVED,
            provider_handler.t.PROVIDER_STATUS_APPROVED,
        ),
        (
            ProviderAuthorizationStatus.REVOKED,
            provider_handler.t.PROVIDER_STATUS_REVOKED,
        ),
    ],
)
def test_status_label_known_values(
    status: ProviderAuthorizationStatus,
    expected: str,
) -> None:
    assert provider_handler._status_label(status) == expected


def test_is_pending_and_is_approved() -> None:
    assert provider_handler._is_pending(ProviderAuthorizationStatus.PENDING) is True
    assert provider_handler._is_pending(ProviderAuthorizationStatus.APPROVED) is False
    assert provider_handler._is_approved(ProviderAuthorizationStatus.APPROVED) is True
    assert provider_handler._is_approved(ProviderAuthorizationStatus.PENDING) is False


def test_extract_provider_name_from_valid_callback() -> None:
    call = _callback(_tg_user(), "provider:approve:vpn123")

    assert provider_handler._extract_provider_name(call) == "vpn123"


def test_extract_provider_name_returns_none_for_missing_data() -> None:
    call = _callback(_tg_user(), "")
    call.data = None

    assert provider_handler._extract_provider_name(call) is None


def test_extract_provider_name_returns_none_for_malformed_data() -> None:
    call = _callback(_tg_user(), "provider:approve")

    assert provider_handler._extract_provider_name(call) is None


# ── Deep link: /start provider_{name} ────────────────────────────────────────


@pytest.mark.asyncio
async def test_provider_deep_link_with_existing_authorization_shows_status() -> None:
    message = _message(_tg_user())
    fake_auth = MagicMock(
        provider_name="vpn123",
        provider_url="https://vpn123.example.com",
        status=ProviderAuthorizationStatus.PENDING,
    )

    with patch.object(
        provider_handler.v2hub_client,
        "get_provider_authorization",
        AsyncMock(return_value=fake_auth),
    ):
        await provider_handler.handle_provider_deep_link(
            message,
            1,
            "provider",
            "vpn123",
            None,
        )

    message.answer.assert_awaited_once()
    text = message.answer.await_args.args[0]
    assert "vpn123" in text


@pytest.mark.asyncio
async def test_provider_deep_link_no_authorization_falls_back_to_provider_lookup() -> None:
    message = _message(_tg_user())
    fake_provider = MagicMock(
        provider_name="vpn123",
        provider_url="https://vpn123.example.com",
    )

    with (
        patch.object(
            provider_handler.v2hub_client,
            "get_provider_authorization",
            AsyncMock(return_value=None),
        ),
        patch.object(
            provider_handler.v2hub_client,
            "get_provider_by_name",
            AsyncMock(return_value=fake_provider),
        ),
    ):
        await provider_handler.handle_provider_deep_link(
            message,
            1,
            "provider",
            "vpn123",
            None,
        )

    message.answer.assert_awaited_once()
    text = message.answer.await_args.args[0]
    assert "vpn123" in text


@pytest.mark.asyncio
async def test_provider_deep_link_unknown_provider_shows_not_found() -> None:
    message = _message(_tg_user())

    with (
        patch.object(
            provider_handler.v2hub_client,
            "get_provider_authorization",
            AsyncMock(return_value=None),
        ),
        patch.object(
            provider_handler.v2hub_client,
            "get_provider_by_name",
            AsyncMock(return_value=None),
        ),
    ):
        await provider_handler.handle_provider_deep_link(
            message,
            1,
            "provider",
            "ghost",
            None,
        )

    text = message.answer.await_args.args[0]
    assert "ghost" in text


# ── Deep link: /start conn_{hmac}_{name} ─────────────────────────────────────


@pytest.mark.asyncio
async def test_conn_deep_link_forwards_hmac_and_shows_connection_request() -> None:
    message = _message(_tg_user())
    fake_auth = MagicMock(
        provider_name="vpn123",
        provider_url="https://vpn123.example.com",
        status=ProviderAuthorizationStatus.PENDING,
    )
    process_mock = AsyncMock(return_value=fake_auth)

    with patch.object(
        provider_handler.v2hub_client,
        "process_provider_authorization",
        process_mock,
    ):
        await provider_handler.handle_provider_deep_link(
            message,
            1,
            "conn",
            "vpn123",
            "raw-hmac",
        )

    process_mock.assert_awaited_once_with(
        user_id=1,
        provider_name="vpn123",
        hmac="raw-hmac",
    )
    text = message.answer.await_args.args[0]
    assert "vpn123" in text
    assert "подпис" in text.lower()


@pytest.mark.asyncio
async def test_conn_deep_link_invalid_hmac_shows_error() -> None:
    message = _message(_tg_user())

    with patch.object(
        provider_handler.v2hub_client,
        "process_provider_authorization",
        AsyncMock(side_effect=V2HubError("invalid hmac")),
    ):
        await provider_handler.handle_provider_deep_link(
            message,
            1,
            "conn",
            "vpn123",
            "bad-hmac",
        )

    text = message.answer.await_args.args[0]
    assert "invalid hmac" in text


# ── provider:menu ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_provider_menu_shows_intro_for_non_provider() -> None:
    call = _callback(_tg_user(), "provider:menu")

    with patch.object(
        provider_handler.v2hub_client,
        "get_provider_by_owner_id",
        AsyncMock(return_value=None),
    ) as owner_lookup_mock:
        await provider_handler.cb_provider_menu(call)

    owner_lookup_mock.assert_awaited_once_with(1)
    call.message.edit_text.assert_awaited_once()
    text = call.message.edit_text.await_args.args[0]
    assert text == provider_handler.t.PROVIDER_INTRO


@pytest.mark.asyncio
async def test_provider_menu_shows_provider_info_for_provider_role() -> None:
    call = _callback(_tg_user(), "provider:menu")
    fake_provider = MagicMock(
        provider_name="vpn123",
        provider_url="https://vpn123.example.com",
        is_active=True,
    )

    with patch.object(
        provider_handler.v2hub_client,
        "get_provider_by_owner_id",
        AsyncMock(return_value=fake_provider),
    ):
        await provider_handler.cb_provider_menu(call)

    text = call.message.edit_text.await_args.args[0]
    assert "vpn123" in text


# ── approve / reject / disconnect ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_provider_approve_success() -> None:
    call = _callback(_tg_user(), "provider:approve:vpn123")
    fake_auth = MagicMock(
        provider_name="vpn123",
        status=ProviderAuthorizationStatus.APPROVED,
    )

    with patch.object(
        provider_handler.v2hub_client,
        "approve_provider_authorization",
        AsyncMock(return_value=fake_auth),
    ):
        await provider_handler.cb_provider_approve(call)

    text = call.message.edit_text.await_args.args[0]
    assert "vpn123" in text


@pytest.mark.asyncio
async def test_cb_provider_approve_conflict_shows_error() -> None:
    call = _callback(_tg_user(), "provider:approve:vpn123")

    with patch.object(
        provider_handler.v2hub_client,
        "approve_provider_authorization",
        AsyncMock(side_effect=ConflictError("not pending")),
    ):
        await provider_handler.cb_provider_approve(call)

    text = call.message.edit_text.await_args.args[0]
    assert "not pending" in text


@pytest.mark.asyncio
async def test_cb_provider_approve_missing_provider_name_noop() -> None:
    call = _callback(_tg_user(), "provider:approve")

    await provider_handler.cb_provider_approve(call)

    call.message.edit_text.assert_not_called()
    call.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cb_provider_reject_success() -> None:
    call = _callback(_tg_user(), "provider:reject:vpn123")

    with patch.object(
        provider_handler.v2hub_client,
        "reject_provider_authorization",
        AsyncMock(return_value=MagicMock(status=None)),
    ):
        await provider_handler.cb_provider_reject(call)

    text = call.message.edit_text.await_args.args[0]
    assert "vpn123" in text


@pytest.mark.asyncio
async def test_cb_provider_reject_not_found_shows_error() -> None:
    call = _callback(_tg_user(), "provider:reject:vpn123")

    with patch.object(
        provider_handler.v2hub_client,
        "reject_provider_authorization",
        AsyncMock(side_effect=NotFoundError("no such authorization")),
    ):
        await provider_handler.cb_provider_reject(call)

    text = call.message.edit_text.await_args.args[0]
    assert "no such authorization" in text


@pytest.mark.asyncio
async def test_cb_provider_disconnect_deletes_when_no_subscriptions() -> None:
    call = _callback(_tg_user(), "provider:disconnect:vpn123")

    with patch.object(
        provider_handler.v2hub_client,
        "reject_provider_authorization",
        AsyncMock(return_value=MagicMock(status=None)),
    ):
        await provider_handler.cb_provider_disconnect(call)

    text = call.message.edit_text.await_args.args[0]
    assert text == provider_handler.t.PROVIDER_DISCONNECTED_DELETED.format(
        provider_name="vpn123",
    )


@pytest.mark.asyncio
async def test_cb_provider_disconnect_revokes_when_subscriptions_exist() -> None:
    call = _callback(_tg_user(), "provider:disconnect:vpn123")

    with patch.object(
        provider_handler.v2hub_client,
        "reject_provider_authorization",
        AsyncMock(
            return_value=MagicMock(
                status=ProviderAuthorizationStatus.REVOKED,
            )
        ),
    ):
        await provider_handler.cb_provider_disconnect(call)

    text = call.message.edit_text.await_args.args[0]
    assert text == provider_handler.t.PROVIDER_DISCONNECTED_REVOKED.format(
        provider_name="vpn123",
    )


@pytest.mark.asyncio
async def test_cb_provider_disconnect_error_shows_message() -> None:
    call = _callback(_tg_user(), "provider:disconnect:vpn123")

    with patch.object(
        provider_handler.v2hub_client,
        "reject_provider_authorization",
        AsyncMock(side_effect=V2HubError("boom")),
    ):
        await provider_handler.cb_provider_disconnect(call)

    text = call.message.edit_text.await_args.args[0]
    assert "boom" in text


# ── provider:my ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_my_providers_empty_when_no_authorizations() -> None:
    call = _callback(_tg_user(), "provider:my")

    with patch.object(
        provider_handler.v2hub_client,
        "get_user_connections",
        AsyncMock(
            return_value=ConnectionsResponse(
                connections=[],
            )
        ),
    ):
        await provider_handler.cb_my_providers(call)

    text = call.message.edit_text.await_args.args[0]
    assert text == provider_handler.t.MY_PROVIDERS_EMPTY


@pytest.mark.asyncio
async def test_cb_my_providers_lists_authorized_providers_only() -> None:
    call = _callback(_tg_user(), "provider:my")

    with patch.object(
        provider_handler.v2hub_client,
        "get_user_connections",
        AsyncMock(
            return_value=ConnectionsResponse(
                connections=[
                    ConnectionResponse(
                        provider_name="vpn123",
                        provider_url="https://vpn123.example.com",
                        is_authorized=True,
                        status=ProviderAuthorizationStatus.APPROVED,
                    ),
                    ConnectionResponse(
                        provider_name="vpn456",
                        provider_url="https://vpn456.example.com",
                        is_authorized=False,
                        status=ProviderAuthorizationStatus.PENDING,
                    ),
                ],
            )
        ),
    ):
        await provider_handler.cb_my_providers(call)

    call.message.edit_text.assert_awaited_once()
    assert call.message.edit_text.await_args.args[0] == provider_handler.t.MY_PROVIDERS_TITLE


# ── provider:view ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_provider_view_missing_name_noop() -> None:
    call = _callback(_tg_user(), "provider:view")

    await provider_handler.cb_provider_view(call)

    call.message.edit_text.assert_not_called()
    call.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cb_provider_view_shows_not_found_when_no_authorization() -> None:
    call = _callback(_tg_user(), "provider:view:vpn123")

    with patch.object(
        provider_handler.v2hub_client,
        "get_provider_authorization",
        AsyncMock(return_value=None),
    ):
        await provider_handler.cb_provider_view(call)

    text = call.message.edit_text.await_args.args[0]
    assert "vpn123" in text


@pytest.mark.asyncio
async def test_cb_provider_view_shows_authorization_state() -> None:
    call = _callback(_tg_user(), "provider:view:vpn123")
    fake_auth = MagicMock(
        provider_name="vpn123",
        provider_url="https://vpn123.example.com",
        status=ProviderAuthorizationStatus.APPROVED,
    )

    with patch.object(
        provider_handler.v2hub_client,
        "get_provider_authorization",
        AsyncMock(return_value=fake_auth),
    ):
        await provider_handler.cb_provider_view(call)

    text = call.message.edit_text.await_args.args[0]
    assert "vpn123" in text


# ── missing-provider-name guard clauses ──────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_provider_reject_missing_provider_name_noop() -> None:
    call = _callback(_tg_user(), "provider:reject")

    await provider_handler.cb_provider_reject(call)

    call.message.edit_text.assert_not_called()
    call.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cb_provider_disconnect_missing_provider_name_noop() -> None:
    call = _callback(_tg_user(), "provider:disconnect")

    await provider_handler.cb_provider_disconnect(call)

    call.message.edit_text.assert_not_called()
    call.answer.assert_awaited_once()


# ── provider token management ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_provider_token_shows_token_for_provider_role() -> None:
    call = _callback(_tg_user(), "provider:token")
    fake_provider = MagicMock(api_token="provider-token-abc")

    with patch.object(
        provider_handler.v2hub_client,
        "get_provider_by_owner_id",
        AsyncMock(return_value=fake_provider),
    ):
        await provider_handler.cb_provider_token(call)

    text = call.message.edit_text.await_args.args[0]
    assert "provider-token-abc" in text


@pytest.mark.asyncio
async def test_cb_provider_token_shows_error_when_user_owns_no_provider() -> None:
    call = _callback(_tg_user(), "provider:token")

    with patch.object(
        provider_handler.v2hub_client,
        "get_provider_by_owner_id",
        AsyncMock(return_value=None),
    ):
        await provider_handler.cb_provider_token(call)

    text = call.message.edit_text.await_args.args[0]
    assert text == provider_handler.t.PROVIDER_NOT_FOUND_FOR_ROLE


@pytest.mark.asyncio
async def test_cb_provider_token_refresh_shows_error_when_user_owns_no_provider() -> None:
    call = _callback(_tg_user(), "provider:token_refresh")

    with patch.object(
        provider_handler.v2hub_client,
        "get_provider_by_owner_id",
        AsyncMock(return_value=None),
    ):
        await provider_handler.cb_provider_token_refresh(call)

    text = call.message.edit_text.await_args.args[0]
    assert text == provider_handler.t.PROVIDER_NOT_FOUND_FOR_ROLE


@pytest.mark.asyncio
async def test_cb_provider_token_refresh_success() -> None:
    call = _callback(_tg_user(), "provider:token_refresh")
    fake_provider = MagicMock(provider_hash="hash-1")

    with (
        patch.object(
            provider_handler.v2hub_client,
            "get_provider_by_owner_id",
            AsyncMock(return_value=fake_provider),
        ),
        patch.object(
            provider_handler.v2hub_client,
            "refresh_provider_token",
            AsyncMock(return_value="rotated-provider-token"),
        ) as refresh_mock,
    ):
        await provider_handler.cb_provider_token_refresh(call)

    refresh_mock.assert_awaited_once_with("hash-1")
    text = call.message.edit_text.await_args.args[0]
    assert "rotated-provider-token" in text


@pytest.mark.asyncio
async def test_cb_provider_token_refresh_handles_error() -> None:
    call = _callback(_tg_user(), "provider:token_refresh")
    fake_provider = MagicMock(provider_hash="hash-1")

    with (
        patch.object(
            provider_handler.v2hub_client,
            "get_provider_by_owner_id",
            AsyncMock(return_value=fake_provider),
        ),
        patch.object(
            provider_handler.v2hub_client,
            "refresh_provider_token",
            AsyncMock(side_effect=V2HubError("refresh failed")),
        ),
    ):
        await provider_handler.cb_provider_token_refresh(call)

    text = call.message.edit_text.await_args.args[0]
    assert "refresh failed" in text
