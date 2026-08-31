from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TgUser

from v2hub_bot.handlers import start
from v2hub_bot.services import V2HubError

pytestmark = pytest.mark.unit


def _tg_user(user_id: int = 1) -> MagicMock:
    user = MagicMock(spec=TgUser)
    user.id = user_id
    user.first_name = "Alice"
    return user


def _message(user: MagicMock | None) -> MagicMock:
    message = MagicMock(spec=Message)
    message.from_user = user
    message.answer = AsyncMock()
    return message


def _session_cm(session: MagicMock) -> MagicMock:
    @asynccontextmanager
    async def _cm() -> AsyncMock:
        yield session

    return _cm


@pytest.mark.asyncio
async def test_cmd_start_without_from_user_does_nothing() -> None:
    message = _message(user=None)

    await start.cmd_start(message)

    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_cmd_start_new_user_sends_welcome_and_token(sample_user_id: int) -> None:
    """No user on the server yet -> account is created and both welcome
    messages are sent. The bot only records that the user_id started the
    bot locally; the token itself is never persisted locally."""
    user = _tg_user(sample_user_id)
    message = _message(user)

    fake_session = AsyncMock()

    with (
        patch("v2hub_bot.handlers.start.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.start.get_or_create_user", AsyncMock()) as get_or_create_mock,
        patch.object(start.v2hub_client, "get_user", AsyncMock(return_value=None)),
        patch.object(start.v2hub_client, "create_user", AsyncMock(return_value="new-token")),
    ):
        await start.cmd_start(message)

    get_or_create_mock.assert_awaited_once_with(fake_session, sample_user_id)
    assert message.answer.await_count == 2
    first_call_text = message.answer.await_args_list[0].args[0]
    second_call_text = message.answer.await_args_list[1].args[0]
    assert "Alice" in first_call_text
    assert "new-token" in second_call_text


@pytest.mark.asyncio
async def test_cmd_start_returning_user_sends_single_welcome(sample_user_id: int) -> None:
    user = _tg_user(sample_user_id)
    message = _message(user)

    existing_server_user = MagicMock(api_token="existing-token")
    fake_session = AsyncMock()

    with (
        patch("v2hub_bot.handlers.start.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.start.get_or_create_user", AsyncMock()),
        patch.object(start.v2hub_client, "get_user", AsyncMock(return_value=existing_server_user)),
    ):
        await start.cmd_start(message)

    message.answer.assert_awaited_once()
    text, kwargs = message.answer.await_args
    assert "Alice" in text[0]
    assert kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_cmd_start_v2hub_error_falls_back_to_returning_flow(sample_user_id: int) -> None:
    """If token creation fails for a brand-new user, bot should not crash and
    should not claim the token is ready."""
    user = _tg_user(sample_user_id)
    message = _message(user)

    fake_session = AsyncMock()

    with (
        patch("v2hub_bot.handlers.start.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.start.get_or_create_user", AsyncMock()),
        patch.object(start.v2hub_client, "get_user", AsyncMock(return_value=None)),
        patch.object(start.v2hub_client, "create_user", AsyncMock(side_effect=V2HubError("boom"))),
    ):
        await start.cmd_start(message)

    # is_new=True but token=None -> falls into the "else" branch (single message)
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cb_menu_edits_message_with_main_menu(sample_user_id: int) -> None:
    call = MagicMock(spec=CallbackQuery)
    call.from_user = _tg_user(sample_user_id)
    call.message = MagicMock(spec=Message)
    call.message.edit_text = AsyncMock()
    call.answer = AsyncMock()

    server_user = MagicMock(api_token="tok")

    with patch.object(start.v2hub_client, "get_user", AsyncMock(return_value=server_user)):
        await start.cb_menu(call)

    call.message.edit_text.assert_awaited_once()
    call.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cb_menu_without_server_account_shows_no_token(sample_user_id: int) -> None:
    call = MagicMock(spec=CallbackQuery)
    call.from_user = _tg_user(sample_user_id)
    call.message = MagicMock(spec=Message)
    call.message.edit_text = AsyncMock()
    call.answer = AsyncMock()

    with patch.object(start.v2hub_client, "get_user", AsyncMock(return_value=None)):
        await start.cb_menu(call)

    call.message.edit_text.assert_awaited_once()
    _, kwargs = call.message.edit_text.await_args
    assert kwargs["reply_markup"] is not None


# ── /start with a deep-link payload ──────────────────────────────────────────


def _command_object(args: str | None) -> MagicMock:
    from aiogram.filters import CommandObject

    return CommandObject(prefix="/", command="start", args=args)


@pytest.mark.asyncio
async def test_cmd_start_deep_link_without_from_user_does_nothing() -> None:
    message = _message(user=None)

    await start.cmd_start_deep_link(message, _command_object("provider_vpn123"))

    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_cmd_start_deep_link_invalid_payload_shows_error(sample_user_id: int) -> None:
    user = _tg_user(sample_user_id)
    message = _message(user)

    await start.cmd_start_deep_link(message, _command_object("garbage"))

    message.answer.assert_awaited_once()
    assert message.answer.await_args.args[0] == start.t.DEEP_LINK_INVALID


@pytest.mark.asyncio
async def test_cmd_start_deep_link_provider_payload_delegates_to_provider_handler(
    sample_user_id: int,
) -> None:
    user = _tg_user(sample_user_id)
    message = _message(user)
    fake_session = AsyncMock()

    handle_mock = AsyncMock()

    with (
        patch("v2hub_bot.handlers.start.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.start.get_or_create_user", AsyncMock()),
        patch("v2hub_bot.handlers.provider.handle_provider_deep_link", handle_mock),
    ):
        await start.cmd_start_deep_link(message, _command_object("provider_vpn123"))

    handle_mock.assert_awaited_once_with(message, sample_user_id, "provider", "vpn123", None)


@pytest.mark.asyncio
async def test_cmd_start_deep_link_conn_payload_delegates_to_provider_handler(
    sample_user_id: int,
) -> None:
    user = _tg_user(sample_user_id)
    message = _message(user)
    fake_session = AsyncMock()

    handle_mock = AsyncMock()

    with (
        patch("v2hub_bot.handlers.start.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.start.get_or_create_user", AsyncMock()),
        patch("v2hub_bot.handlers.provider.handle_provider_deep_link", handle_mock),
    ):
        await start.cmd_start_deep_link(message, _command_object("conn_hmac123_vpn123"))

    handle_mock.assert_awaited_once_with(message, sample_user_id, "conn", "vpn123", "hmac123")


@pytest.mark.asyncio
async def test_cmd_start_deep_link_marks_user_locally_before_delegating(
    sample_user_id: int,
) -> None:
    """Even on a deep-link start, the bot still records that this user_id
    started the bot — that's the only thing it persists locally."""
    user = _tg_user(sample_user_id)
    message = _message(user)
    fake_session = AsyncMock()

    with (
        patch("v2hub_bot.handlers.start.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.start.get_or_create_user", AsyncMock()) as get_or_create_mock,
        patch("v2hub_bot.handlers.provider.handle_provider_deep_link", AsyncMock()),
    ):
        await start.cmd_start_deep_link(message, _command_object("provider_vpn123"))

    get_or_create_mock.assert_awaited_once_with(fake_session, sample_user_id)
