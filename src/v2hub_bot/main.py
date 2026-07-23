import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from v2hub_bot.config import settings
from v2hub_bot.db import init_db
from v2hub_bot.handlers import help as help_handler
from v2hub_bot.handlers import start, support, token
from v2hub_bot.middlewares import ThrottleMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Middlewares
    dp.message.middleware(ThrottleMiddleware(rate_limit=1.5))

    # Routers
    dp.include_router(start.router)
    dp.include_router(token.router)
    dp.include_router(support.router)
    dp.include_router(help_handler.router)

    logger.info("Bot started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def cli() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
