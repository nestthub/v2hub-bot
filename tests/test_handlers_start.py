from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message
from helpers import command_object, make_callback, make_message, t, tg_user
from sqlalchemy import select

from v2hub_bot.db.models import User
from v2hub_bot.handlers import start
from v2hub_bot.services import v2hubError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.unit


async def _local_user_ids(session_factory: async_sessionmaker[AsyncSession]) -> list[int]:
    async with session_factory() as session:
        return list((await session.execute(select(User.id))).scalars())


# ── /start ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cmd_start_without_from_user_does_nothing() -> None:
    message = make_message(user=None)

    await start.cmd_start(message)

    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_cmd_start_new_user_sends_welcome_and_records_user_locally(
    sample_user_id: int,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """No user on the server yet -> account is created and the welcome is sent.
    The bot only records that the user_id started the bot locally; the token
    itself is never persisted locally."""
    message = make_message(tg_user(sample_user_id))

    with (
        patch.object(start.v2hub_client, "get_user", AsyncMock(return_value=None)),
        patch.object(
            start.v2hub_client,
            "create_user",
            AsyncMock(return_value=MagicMock(api_token="new-token")),
        ) as create_mock,
    ):
        await start.cmd_start(message)

    create_mock.assert_awaited_once_with(user_id=sample_user_id)
    message.answer.assert_awaited_once()
    assert message.answer.await_args.kwargs["text"] == t("WELCOME_NEW").format(name="Alice")
    assert await _local_user_ids(session_factory) == [sample_user_id]


@pytest.mark.asyncio
async def test_cmd_start_returning_user_sends_single_welcome(sample_user_id: int) -> None:
    message = make_message(tg_user(sample_user_id))
    existing_server_user = MagicMock(api_token="existing-token")

    with patch.object(start.v2hub_client, "get_user", AsyncMock(return_value=existing_server_user)):
        await start.cmd_start(message)

    message.answer.assert_awaited_once()
    kwargs = message.answer.await_args.kwargs
    assert kwargs["text"] == t("WELCOME_RETURNING").format(name="Alice")
    assert kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_cmd_start_v2hub_error_does_not_crash(sample_user_id: int) -> None:
    """If token creation fails for a brand-new user, the bot should not crash."""
    message = make_message(tg_user(sample_user_id))

    with (
        patch.object(start.v2hub_client, "get_user", AsyncMock(return_value=None)),
        patch.object(start.v2hub_client, "create_user", AsyncMock(side_effect=v2hubError("boom"))),
    ):
        await start.cmd_start(message)

    message.answer.assert_awaited_once()


# ── menu callbacks ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_menu_edits_message_with_main_menu(sample_user_id: int) -> None:
    call = make_callback(tg_user(sample_user_id), "menu")
    call.message = MagicMock(spec=Message)
    call.message.edit_text = AsyncMock()

    await start.cb_menu(call)

    call.message.edit_text.assert_awaited_once()
    assert call.message.edit_text.await_args.kwargs["reply_markup"] is not None
    call.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cb_menu_records_user_locally(
    sample_user_id: int,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    call = make_callback(tg_user(sample_user_id), "menu")

    await start.cb_menu(call)

    assert await _local_user_ids(session_factory) == [sample_user_id]


# ── /start with a deep-link payload ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_cmd_start_deep_link_token_shows_token_actions(sample_user_id: int) -> None:
    message = make_message(tg_user(sample_user_id))
    expected_markup = MagicMock()

    with (
        patch(
            "v2hub_bot.handlers.start._token_info_text",
            AsyncMock(return_value=("Your token", True, None)),
        ) as token_info_mock,
        patch(
            "v2hub_bot.handlers.start.token_actions",
            MagicMock(return_value=expected_markup),
        ) as token_actions_mock,
    ):
        await start.cmd_start_deep_link(message, command_object("token"))

    token_info_mock.assert_awaited_once()
    assert token_info_mock.await_args.args[0] == sample_user_id
    token_actions_mock.assert_called_once()
    assert token_actions_mock.call_args.args[0] is True

    message.answer.assert_awaited_once_with("Your token", reply_markup=expected_markup)


@pytest.mark.asyncio
async def test_cmd_start_deep_link_without_from_user_does_nothing() -> None:
    message = make_message(user=None)

    await start.cmd_start_deep_link(message, command_object("provider_vpn123"))

    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_cmd_start_deep_link_invalid_payload_shows_error(sample_user_id: int) -> None:
    message = make_message(tg_user(sample_user_id))

    await start.cmd_start_deep_link(message, command_object("garbage"))

    message.answer.assert_awaited_once_with(t("DEEP_LINK_INVALID"))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "expected_args"),
    [
        ("provider_vpn123", ("provider", "vpn123", None)),
        ("conn_hmac123_vpn123", ("conn", "vpn123", "hmac123")),
    ],
)
async def test_cmd_start_deep_link_delegates_to_provider_handler(
    sample_user_id: int,
    payload: str,
    expected_args: tuple[str, str, str | None],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Also checks that the bot still records the user locally before delegating
    — that's the only thing it persists."""
    message = make_message(tg_user(sample_user_id))
    handle_mock = AsyncMock()

    with patch("v2hub_bot.handlers.provider.handle_provider_deep_link", handle_mock):
        await start.cmd_start_deep_link(message, command_object(payload))

    handle_mock.assert_awaited_once_with(message, sample_user_id, *expected_args, ANY)
    assert callable(handle_mock.await_args.args[-1])
    assert await _local_user_ids(session_factory) == [sample_user_id]
