from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message

from v2hub_bot.middlewares.admin import AdminMiddleware

pytestmark = pytest.mark.unit


def _make_message(user_id: int | None = 1) -> MagicMock:
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(id=user_id) if user_id is not None else None
    return message


def _make_callback(user_id: int | None = 1) -> MagicMock:
    call = MagicMock(spec=CallbackQuery)
    call.from_user = MagicMock(id=user_id) if user_id is not None else None
    call.answer = AsyncMock()
    return call


@pytest.mark.asyncio
async def test_admin_passes_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("v2hub_bot.middlewares.admin.settings.bot_admins", [1])
    middleware = AdminMiddleware()
    handler = AsyncMock(return_value="handled")
    message = _make_message(user_id=1)

    result = await middleware(handler, message, {})

    handler.assert_awaited_once_with(message, {})
    assert result == "handled"


@pytest.mark.asyncio
async def test_non_admin_message_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("v2hub_bot.middlewares.admin.settings.bot_admins", [1])
    middleware = AdminMiddleware()
    handler = AsyncMock(return_value="handled")
    message = _make_message(user_id=999)

    result = await middleware(handler, message, {})

    handler.assert_not_called()
    assert result is None


@pytest.mark.asyncio
async def test_non_admin_callback_is_blocked_and_answered(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("v2hub_bot.middlewares.admin.settings.bot_admins", [1])
    middleware = AdminMiddleware()
    handler = AsyncMock(return_value="handled")
    call = _make_callback(user_id=999)

    result = await middleware(handler, call, {})

    handler.assert_not_called()
    call.answer.assert_awaited_once()
    assert result is None


@pytest.mark.asyncio
async def test_event_without_from_user_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("v2hub_bot.middlewares.admin.settings.bot_admins", [1])
    middleware = AdminMiddleware()
    handler = AsyncMock(return_value="handled")
    message = _make_message(user_id=None)

    result = await middleware(handler, message, {})

    handler.assert_not_called()
    assert result is None
