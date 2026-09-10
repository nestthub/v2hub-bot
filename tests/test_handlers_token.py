from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TgUser

from v2hub_bot.handlers import token
from v2hub_bot.services import v2hubError

pytestmark = pytest.mark.unit


def _tg_user(user_id: int = 1) -> MagicMock:
    user = MagicMock(spec=TgUser)
    user.id = user_id
    return user


def _message(user: MagicMock) -> MagicMock:
    message = MagicMock(spec=Message)
    message.from_user = user
    message.answer = AsyncMock()
    return message


def _callback(user: MagicMock) -> MagicMock:
    call = MagicMock(spec=CallbackQuery)
    call.from_user = user
    call.message = MagicMock(spec=Message)
    call.message.edit_text = AsyncMock()
    call.answer = AsyncMock()
    return call


# ── /token ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cmd_token_without_from_user_does_nothing() -> None:
    message = MagicMock(spec=Message)
    message.from_user = None
    message.answer = AsyncMock()

    await token.cmd_token(message)

    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_cmd_token_with_no_server_account_shows_none(sample_user_id: int) -> None:
    message = _message(_tg_user(sample_user_id))

    with patch.object(token.v2hub_client, "get_user", AsyncMock(return_value=None)):
        await token.cmd_token(message)

    message.answer.assert_awaited_once()
    text, kwargs = message.answer.await_args
    assert text[0] == token.t.TOKEN_NONE
    assert kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_cmd_token_with_existing_token_shows_it(sample_user_id: int) -> None:
    message = _message(_tg_user(sample_user_id))
    server_user = MagicMock(api_token="server-token-1")

    with patch.object(token.v2hub_client, "get_user", AsyncMock(return_value=server_user)):
        await token.cmd_token(message)

    message.answer.assert_awaited_once()
    text = message.answer.await_args.args[0]
    assert "server-token-1" in text


# ── token:info ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_token_info_reads_straight_from_server(sample_user_id: int) -> None:
    call = _callback(_tg_user(sample_user_id))
    server_user = MagicMock(api_token="server-token-2")

    with patch.object(
        token.v2hub_client, "get_user", AsyncMock(return_value=server_user)
    ) as get_user_mock:
        await token.cb_token_info(call)

    get_user_mock.assert_awaited_once_with(sample_user_id)
    call.message.edit_text.assert_awaited_once()
    assert "server-token-2" in call.message.edit_text.await_args.args[0]
    call.answer.assert_awaited_once()


# ── token:generate ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_token_generate_success_shows_new_token_without_touching_local_db(
    sample_user_id: int,
) -> None:
    """token.py doesn't import async_session at all anymore: the token is
    never persisted locally, only created/read via v2hub_client."""
    call = _callback(_tg_user(sample_user_id))

    assert not hasattr(token, "async_session")

    with patch.object(
        token.v2hub_client,
        "create_user",
        AsyncMock(return_value=MagicMock(api_token="brand-new-token")),
    ) as create_mock:
        await token.cb_token_generate(call)

    create_mock.assert_awaited_once_with(user_id=sample_user_id)
    call.message.edit_text.assert_awaited_once()
    assert "brand-new-token" in call.message.edit_text.await_args.args[0]


@pytest.mark.asyncio
async def test_cb_token_generate_error_shows_error_message(sample_user_id: int) -> None:
    call = _callback(_tg_user(sample_user_id))

    with patch.object(token.v2hub_client, "create_user", AsyncMock(side_effect=v2hubError("boom"))):
        await token.cb_token_generate(call)

    call.message.edit_text.assert_awaited_once()
    assert "boom" in call.message.edit_text.await_args.args[0]


# ── token:refresh ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_token_refresh_without_active_token_shows_alert(sample_user_id: int) -> None:
    call = _callback(_tg_user(sample_user_id))

    with patch.object(token.v2hub_client, "get_user", AsyncMock(return_value=None)):
        await token.cb_token_refresh(call)

    call.answer.assert_awaited_once_with(token.t.TOKEN_NO_ACTIVE, show_alert=True)
    call.message.edit_text.assert_not_called()


@pytest.mark.asyncio
async def test_cb_token_refresh_success_shows_rotated_token(sample_user_id: int) -> None:
    call = _callback(_tg_user(sample_user_id))
    server_user = MagicMock(api_token="old-token")

    with (
        patch.object(token.v2hub_client, "get_user", AsyncMock(return_value=server_user)),
        patch.object(token.v2hub_client, "refresh_token", AsyncMock(return_value="rotated-token")),
    ):
        await token.cb_token_refresh(call)

    call.message.edit_text.assert_awaited_once()
    assert "rotated-token" in call.message.edit_text.await_args.args[0]


@pytest.mark.asyncio
async def test_cb_token_refresh_error_shows_error_message(sample_user_id: int) -> None:
    call = _callback(_tg_user(sample_user_id))
    server_user = MagicMock(api_token="old-token")

    with (
        patch.object(token.v2hub_client, "get_user", AsyncMock(return_value=server_user)),
        patch.object(
            token.v2hub_client, "refresh_token", AsyncMock(side_effect=v2hubError("refresh failed"))
        ),
    ):
        await token.cb_token_refresh(call)

    call.message.edit_text.assert_awaited_once()
    assert "refresh failed" in call.message.edit_text.await_args.args[0]
