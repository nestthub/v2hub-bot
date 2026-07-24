from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Message

from v2hub_bot.middlewares.throttle import ThrottleMiddleware

pytestmark = pytest.mark.unit


def _make_message(user_id: int | None = 1) -> MagicMock:
    # spec=Message so isinstance(message, Message) passes inside the middleware.
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(id=user_id) if user_id is not None else None
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_first_call_is_not_throttled() -> None:
    middleware = ThrottleMiddleware(rate_limit=1.5)
    handler = AsyncMock(return_value="handled")
    message = _make_message(user_id=1)

    result = await middleware(handler, message, {})

    handler.assert_awaited_once_with(message, {})
    message.answer.assert_not_called()
    assert result == "handled"


@pytest.mark.asyncio
async def test_rapid_second_call_is_throttled() -> None:
    middleware = ThrottleMiddleware(rate_limit=100.0)  # huge window, guarantees throttle
    handler = AsyncMock(return_value="handled")
    message = _make_message(user_id=1)

    await middleware(handler, message, {})
    result = await middleware(handler, message, {})

    assert handler.await_count == 1
    message.answer.assert_awaited_once()
    assert result is None


@pytest.mark.asyncio
async def test_call_after_window_passes_is_not_throttled() -> None:
    middleware = ThrottleMiddleware(rate_limit=0.0)
    handler = AsyncMock(return_value="handled")
    message = _make_message(user_id=1)

    await middleware(handler, message, {})
    result = await middleware(handler, message, {})

    assert handler.await_count == 2
    assert result == "handled"


@pytest.mark.asyncio
async def test_different_users_are_throttled_independently() -> None:
    middleware = ThrottleMiddleware(rate_limit=100.0)
    handler = AsyncMock(return_value="handled")
    message_a = _make_message(user_id=1)
    message_b = _make_message(user_id=2)

    result_a = await middleware(handler, message_a, {})
    result_b = await middleware(handler, message_b, {})

    assert handler.await_count == 2
    assert result_a == "handled"
    assert result_b == "handled"


@pytest.mark.asyncio
async def test_non_message_events_bypass_throttling() -> None:
    middleware = ThrottleMiddleware(rate_limit=100.0)
    handler = AsyncMock(return_value="handled")
    non_message_event = MagicMock()  # not a Message instance

    result = await middleware(handler, non_message_event, {})

    handler.assert_awaited_once_with(non_message_event, {})
    assert result == "handled"


@pytest.mark.asyncio
async def test_message_without_from_user_bypasses_throttling() -> None:
    middleware = ThrottleMiddleware(rate_limit=100.0)
    handler = AsyncMock(return_value="handled")
    message = _make_message(user_id=None)

    result = await middleware(handler, message, {})

    handler.assert_awaited_once_with(message, {})
    assert result == "handled"
