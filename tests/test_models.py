from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from v2hub_bot.db.models import Base, User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.unit


def test_user_table_only_has_bot_local_columns() -> None:
    """The bot's DB must never carry v2hub-side data (tokens, provider info).

    It only tracks that a Telegram user_id has started the bot, and when.
    """
    columns = set(User.__table__.columns.keys())

    assert columns == {"id", "is_banned", "created_at"}


def test_only_users_table_exists() -> None:
    """The old `providers` table must be gone: ownership now lives on the server."""
    assert set(Base.metadata.tables.keys()) == {"users"}


def test_user_repr_includes_id() -> None:
    user = User(id=123)

    assert repr(user) == "<User id=123>"


@pytest.mark.asyncio
async def test_user_defaults_on_insert(db_session: AsyncSession, sample_user_id: int) -> None:
    user = User(id=sample_user_id)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id == sample_user_id
    assert user.is_banned is False
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_user_persists_and_can_be_fetched(db_session: AsyncSession) -> None:
    db_session.add(User(id=7))
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.id == 7))
    fetched = result.scalar_one()

    assert fetched.id == 7
