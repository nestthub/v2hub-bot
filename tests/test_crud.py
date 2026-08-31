from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from v2hub_bot.db.crud import get_or_create_user, get_user
from v2hub_bot.db.models import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_get_or_create_user_creates_new_row(
    db_session: AsyncSession, sample_user_id: int
) -> None:
    user = await get_or_create_user(db_session, sample_user_id)

    assert isinstance(user, User)
    assert user.id == sample_user_id
    assert user.is_banned is False


@pytest.mark.asyncio
async def test_get_or_create_user_is_idempotent(
    db_session: AsyncSession, sample_user_id: int
) -> None:
    first = await get_or_create_user(db_session, sample_user_id)
    second = await get_or_create_user(db_session, sample_user_id)

    assert first.id == second.id
    assert first.created_at == second.created_at


@pytest.mark.asyncio
async def test_get_or_create_user_returns_existing_user(
    db_session: AsyncSession, existing_user: User
) -> None:
    user = await get_or_create_user(db_session, existing_user.id)

    assert user.id == existing_user.id
    assert user.created_at == existing_user.created_at


@pytest.mark.asyncio
async def test_get_user_returns_none_when_missing(db_session: AsyncSession) -> None:
    result = await get_user(db_session, user_id=999)

    assert result is None


@pytest.mark.asyncio
async def test_get_user_returns_existing_row(db_session: AsyncSession, existing_user: User) -> None:
    result = await get_user(db_session, existing_user.id)

    assert result is not None
    assert result.id == existing_user.id
