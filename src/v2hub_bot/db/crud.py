from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from v2hub_bot.db.models import User

# ── Users ─────────────────────────────────────────────────────────────────────
# The bot's database only tracks that a Telegram user_id has started the
# bot (and when). Everything about the user's v2hub account — api_token,
# provider link, statuses — lives on the server and is always fetched
# fresh through the v2hub-admin API. Nothing v2hub-related is cached here.


async def get_or_create_user(session: AsyncSession, user_id: int) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=user_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
