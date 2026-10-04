from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from helpers import make_message, tg_user
from sqlalchemy import select

from v2hub_bot.db.models import User
from v2hub_bot.locales import i18n
from v2hub_bot.middlewares.throttle import ThrottleMiddleware

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_first_call_is_not_throttled() -> None:
    middleware = ThrottleMiddleware(rate_limit=1.5)
    handler = AsyncMock(return_value="handled")
    message = make_message(tg_user(1))

    result = await middleware(handler, message, {})

    handler.assert_awaited_once_with(message, {})
    message.answer.assert_not_called()
    assert result == "handled"


@pytest.mark.asyncio
async def test_rapid_second_call_is_throttled() -> None:
    middleware = ThrottleMiddleware(rate_limit=100.0)  # huge window, guarantees throttle
    handler = AsyncMock(return_value="handled")
    message = make_message(tg_user(1))

    await middleware(handler, message, {})
    result = await middleware(handler, message, {})

    assert handler.await_count == 1
    message.answer.assert_awaited_once()
    assert result is None


@pytest.mark.asyncio
async def test_call_after_window_passes_is_not_throttled() -> None:
    middleware = ThrottleMiddleware(rate_limit=0.0)
    handler = AsyncMock(return_value="handled")
    message = make_message(tg_user(1))

    await middleware(handler, message, {})
    result = await middleware(handler, message, {})

    assert handler.await_count == 2
    assert result == "handled"


@pytest.mark.asyncio
async def test_different_users_are_throttled_independently() -> None:
    middleware = ThrottleMiddleware(rate_limit=100.0)
    handler = AsyncMock(return_value="handled")
    message_a = make_message(tg_user(1))
    message_b = make_message(tg_user(2))

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
    message = make_message(None)

    result = await middleware(handler, message, {})

    handler.assert_awaited_once_with(message, {})
    assert result == "handled"


@pytest.mark.asyncio
async def test_throttle_warning_uses_telegram_language_for_unknown_user() -> None:
    middleware = ThrottleMiddleware(rate_limit=100.0)
    handler = AsyncMock()
    message = make_message(tg_user(1, language_code="ru"))

    await middleware(handler, message, {})
    await middleware(handler, message, {})

    assert message.answer.await_args.args[0] == i18n.get_translator("ru")("THROTTLE_WARNING")


@pytest.mark.asyncio
async def test_throttle_warning_uses_language_chosen_in_settings(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        session.add(User(id=1, lang="fa"))
        await session.commit()
    middleware = ThrottleMiddleware(rate_limit=100.0)
    handler = AsyncMock()
    message = make_message(tg_user(1, language_code="ru"))  # Telegram says ru, user chose fa

    await middleware(handler, message, {})
    await middleware(handler, message, {})

    expected = i18n.get_translator("fa")("THROTTLE_WARNING")
    assert expected != i18n.get_translator("ru")("THROTTLE_WARNING")
    assert message.answer.await_args.args[0] == expected


@pytest.mark.asyncio
async def test_throttled_message_does_not_create_a_local_user(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    middleware = ThrottleMiddleware(rate_limit=100.0)
    handler = AsyncMock()
    message = make_message(tg_user(1))

    await middleware(handler, message, {})
    await middleware(handler, message, {})

    async with session_factory() as session:
        assert (await session.execute(select(User.id))).first() is None
