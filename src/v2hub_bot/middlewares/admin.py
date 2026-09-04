import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject

from v2hub_bot.config import settings

logger = logging.getLogger(__name__)


class AdminMiddleware(BaseMiddleware):
    """Restrict access to handlers to configured bot administrators."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)

        if user is None:
            return None

        if user.id not in settings.bot_admins:
            logger.debug("Unauthorized admin access attempt from user %s", user.id)

            if isinstance(event, CallbackQuery):
                await event.answer()

            return None

        return await handler(event, data)
