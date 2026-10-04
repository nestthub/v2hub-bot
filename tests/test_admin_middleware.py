from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from helpers import make_callback, make_message, tg_user

from v2hub_bot.middlewares.admin import AdminMiddleware

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_admin_passes_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("v2hub_bot.middlewares.admin.settings.bot_admins", [1])
    middleware = AdminMiddleware()
    handler = AsyncMock(return_value="handled")
    message = make_message(tg_user(1))

    result = await middleware(handler, message, {})

    handler.assert_awaited_once_with(message, {})
    assert result == "handled"


@pytest.mark.asyncio
async def test_non_admin_message_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("v2hub_bot.middlewares.admin.settings.bot_admins", [1])
    middleware = AdminMiddleware()
    handler = AsyncMock(return_value="handled")
    message = make_message(tg_user(999))

    result = await middleware(handler, message, {})

    handler.assert_not_called()
    assert result is None


@pytest.mark.asyncio
async def test_non_admin_callback_is_blocked_and_answered(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("v2hub_bot.middlewares.admin.settings.bot_admins", [1])
    middleware = AdminMiddleware()
    handler = AsyncMock(return_value="handled")
    call = make_callback(tg_user(999))

    result = await middleware(handler, call, {})

    handler.assert_not_called()
    call.answer.assert_awaited_once()
    assert result is None


@pytest.mark.asyncio
async def test_event_without_from_user_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("v2hub_bot.middlewares.admin.settings.bot_admins", [1])
    middleware = AdminMiddleware()
    handler = AsyncMock(return_value="handled")
    message = make_message(None)

    result = await middleware(handler, message, {})

    handler.assert_not_called()
    assert result is None
