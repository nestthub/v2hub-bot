from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TgUser

from v2hub_bot.handlers import token as token_handler
from v2hub_bot.services import V2HubError

pytestmark = pytest.mark.unit


def _tg_user(user_id: int = 1) -> MagicMock:
    user = MagicMock(spec=TgUser)
    user.id = user_id
    user.first_name = "Bob"
    return user


def _session_cm(session: MagicMock) -> MagicMock:
    @asynccontextmanager
    async def _cm() -> AsyncMock:
        yield session

    return _cm


def _message_with_user(user: MagicMock) -> MagicMock:
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

    await token_handler.cmd_token(message)

    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_cmd_token_no_token_shows_generate_prompt(sample_user_id: int) -> None:
    user = _tg_user(sample_user_id)
    message = _message_with_user(user)
    fake_session = AsyncMock()

    with (
        patch("v2hub_bot.handlers.token.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.token.get_user", AsyncMock(return_value=None)),
    ):
        await token_handler.cmd_token(message)

    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cmd_token_with_token_shows_token_info(sample_user_id: int) -> None:
    user = _tg_user(sample_user_id)
    message = _message_with_user(user)
    fake_session = AsyncMock()
    db_user = MagicMock(api_token="my-token", token_generated_at=datetime.now(UTC))

    with (
        patch("v2hub_bot.handlers.token.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.token.get_user", AsyncMock(return_value=db_user)),
    ):
        await token_handler.cmd_token(message)

    text = message.answer.await_args.args[0]
    assert "my-token" in text


# ── token:generate ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_token_generate_success(sample_user_id: int) -> None:
    user = _tg_user(sample_user_id)
    call = _callback(user)
    fake_session = AsyncMock()

    with (
        patch.object(token_handler.v2hub_client, "create_user", AsyncMock(return_value="tok-123")),
        patch("v2hub_bot.handlers.token.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.token.get_or_create_user", AsyncMock()),
        patch("v2hub_bot.handlers.token.save_token", AsyncMock()) as save_token_mock,
    ):
        await token_handler.cb_token_generate(call)

    save_token_mock.assert_awaited_once_with(fake_session, sample_user_id, "tok-123")
    call.message.edit_text.assert_awaited_once()
    assert "tok-123" in call.message.edit_text.await_args.args[0]


@pytest.mark.asyncio
async def test_cb_token_generate_handles_v2hub_error(sample_user_id: int) -> None:
    user = _tg_user(sample_user_id)
    call = _callback(user)

    with patch.object(
        token_handler.v2hub_client,
        "create_user",
        AsyncMock(side_effect=V2HubError("api down")),
    ):
        await token_handler.cb_token_generate(call)

    call.message.edit_text.assert_awaited_once()
    assert "api down" in call.message.edit_text.await_args.args[0]


# ── token:refresh ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_token_refresh_without_existing_token_shows_alert(
    sample_user_id: int,
) -> None:
    user = _tg_user(sample_user_id)
    call = _callback(user)
    fake_session = AsyncMock()

    with (
        patch("v2hub_bot.handlers.token.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.token.get_user", AsyncMock(return_value=None)),
    ):
        await token_handler.cb_token_refresh(call)

    call.answer.assert_awaited_once()
    assert call.answer.await_args.kwargs.get("show_alert") is True
    call.message.edit_text.assert_not_called()


@pytest.mark.asyncio
async def test_cb_token_refresh_success(sample_user_id: int) -> None:
    user = _tg_user(sample_user_id)
    call = _callback(user)
    fake_session = AsyncMock()
    db_user = MagicMock(api_token="old-token")

    with (
        patch("v2hub_bot.handlers.token.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.token.get_user", AsyncMock(return_value=db_user)),
        patch.object(
            token_handler.v2hub_client,
            "refresh_token",
            AsyncMock(return_value="rotated-token"),
        ),
        patch("v2hub_bot.handlers.token.save_token", AsyncMock()) as save_token_mock,
    ):
        await token_handler.cb_token_refresh(call)

    save_token_mock.assert_awaited_once_with(fake_session, sample_user_id, "rotated-token")
    call.message.edit_text.assert_awaited_once()
    assert "rotated-token" in call.message.edit_text.await_args.args[0]


@pytest.mark.asyncio
async def test_cb_token_refresh_handles_v2hub_error(sample_user_id: int) -> None:
    user = _tg_user(sample_user_id)
    call = _callback(user)
    fake_session = AsyncMock()
    db_user = MagicMock(api_token="old-token")

    with (
        patch("v2hub_bot.handlers.token.async_session", _session_cm(fake_session)),
        patch("v2hub_bot.handlers.token.get_user", AsyncMock(return_value=db_user)),
        patch.object(
            token_handler.v2hub_client,
            "refresh_token",
            AsyncMock(side_effect=V2HubError("refresh failed")),
        ),
    ):
        await token_handler.cb_token_refresh(call)

    call.message.edit_text.assert_awaited_once()
    assert "refresh failed" in call.message.edit_text.await_args.args[0]
