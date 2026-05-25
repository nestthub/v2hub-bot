import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from locales import ru as t

logger = logging.getLogger(__name__)


class ThrottleMiddleware(BaseMiddleware):
    """Simple per-user rate limiter using in-memory timestamps."""

    def __init__(self, rate_limit: float = 1.5) -> None:
        self.rate_limit = rate_limit
        self._last_call: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user = event.from_user
        if user is None:
            return await handler(event, data)

        now = asyncio.get_event_loop().time()
        last = self._last_call.get(user.id, 0.0)

        if now - last < self.rate_limit:
            logger.debug("Throttled user %s", user.id)
            await event.answer(t.THROTTLE_WARNING)
            return

        self._last_call[user.id] = now
        return await handler(event, data)
