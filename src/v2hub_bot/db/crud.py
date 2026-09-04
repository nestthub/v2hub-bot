from collections.abc import Sequence

from sqlalchemy import delete, select
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


async def get_all_user_ids(session: AsyncSession, *, exclude_banned: bool = True) -> Sequence[int]:
    """Return the Telegram user_ids of everyone who has started the bot.

    Used for broadcasts. Only reads from the bot's own local database —
    the server (v2hub) is never the source of truth for who has started
    the bot in Telegram.
    """
    stmt = select(User.id)
    if exclude_banned:
        stmt = stmt.where(User.is_banned.is_(False))

    result = await session.execute(stmt)
    return result.scalars().all()


async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(User))
    return len(result.scalars().all())


async def delete_local_user(session: AsyncSession, user_id: int) -> None:
    """Forget the local `started the bot` record for this user_id.

    Called after deleting a user's v2hub account so the bot doesn't keep
    stale broadcast/statistics entries for an account that no longer
    exists. Idempotent — deleting a user_id that isn't tracked is a no-op.
    """
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
