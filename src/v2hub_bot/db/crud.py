from collections.abc import Sequence
from datetime import datetime
from typing import cast

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from v2hub_bot.db.models import User

# ── Users ─────────────────────────────────────────────────────────────────────
# The bot's database only tracks that a Telegram user_id has started the
# bot (and when). Everything about the user's v2hub account — api_token,
# provider link, statuses — lives on the server and is always fetched
# fresh through the v2hub-admin API. Nothing v2hub-related is cached here.


async def get_or_create_user(session: AsyncSession, user_id: int, lang: str | None = None) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        # lang=None must not be passed explicitly: it would override the column's
        # server default and violate NOT NULL.
        user = User(id=user_id, lang=lang) if lang else User(id=user_id)
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


async def get_sorted_user_ids(
    session: AsyncSession,
    *,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    lang: str | None = None,
    exclude_banned: bool = True,
) -> list[int]:
    """Return Telegram user IDs sorted by account creation time.

    Optionally filters users by creation date range, language, and ban status.
    A None boundary means that the corresponding date filter is not applied.
    """
    stmt = select(User.id)

    if start_time is not None:
        stmt = stmt.where(User.created_at >= start_time)

    if end_time is not None:
        stmt = stmt.where(User.created_at <= end_time)

    if lang is not None:
        stmt = stmt.where(User.lang == lang)

    if exclude_banned:
        stmt = stmt.where(User.is_banned.is_(False))

    stmt = stmt.order_by(User.created_at)

    result = await session.execute(stmt)
    return cast("list[int]", result.scalars().all())


async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(User))
    return result.scalar_one()


async def delete_local_user(session: AsyncSession, user_id: int) -> None:
    """Forget the local `started the bot` record for this user_id.

    Called after deleting a user's v2hub account so the bot doesn't keep
    stale broadcast/statistics entries for an account that no longer
    exists. Idempotent — deleting a user_id that isn't tracked is a no-op.
    """
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()


async def update_user_lang(
    session: AsyncSession,
    user_id: int,
    lang: str,
) -> None:
    """Update the interface language for a Telegram user."""
    user = await get_user(session, user_id)

    if user is None:
        return

    user.lang = lang
    await session.commit()
