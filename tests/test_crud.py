from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from v2hub_bot.db.crud import get_or_create_user, get_user, save_token

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from v2hub_bot.db.models import User

pytestmark = pytest.mark.unit


async def test_get_or_create_user_creates_new_user(
    db_session: AsyncSession, sample_user_id: int
) -> None:
    user = await get_or_create_user(db_session, sample_user_id)

    assert user.id == sample_user_id
    assert user.api_token is None
    assert user.is_banned is False


async def test_get_or_create_user_returns_existing_user(
    db_session: AsyncSession, existing_user: User
) -> None:
    user = await get_or_create_user(db_session, existing_user.id)

    assert user.id == existing_user.id
    assert user.api_token == existing_user.api_token


async def test_get_or_create_user_is_idempotent(
    db_session: AsyncSession, sample_user_id: int
) -> None:
    first = await get_or_create_user(db_session, sample_user_id)
    second = await get_or_create_user(db_session, sample_user_id)

    assert first.id == second.id


async def test_get_user_returns_none_for_unknown_user(
    db_session: AsyncSession, sample_user_id: int
) -> None:
    user = await get_user(db_session, sample_user_id)

    assert user is None


async def test_get_user_returns_user_when_present(
    db_session: AsyncSession, existing_user: User
) -> None:
    user = await get_user(db_session, existing_user.id)

    assert user is not None
    assert user.id == existing_user.id


async def test_save_token_updates_existing_user(
    db_session: AsyncSession, sample_user_id: int
) -> None:
    await get_or_create_user(db_session, sample_user_id)

    await save_token(db_session, sample_user_id, "brand-new-token")

    user = await get_user(db_session, sample_user_id)
    assert user is not None
    assert user.api_token == "brand-new-token"
    assert user.token_generated_at is not None


async def test_save_token_overwrites_previous_token(
    db_session: AsyncSession, existing_user: User
) -> None:
    old_generated_at = existing_user.token_generated_at
    print(existing_user.__dict__)

    await save_token(db_session, existing_user.id, "rotated-token")

    user = await get_user(db_session, existing_user.id)
    assert user is not None
    assert user.api_token == "rotated-token"
    assert user.token_generated_at is not None
    assert user.token_generated_at.replace(tzinfo=None) >= old_generated_at.replace(tzinfo=None)


async def test_save_token_noop_for_unknown_user(
    db_session: AsyncSession, sample_user_id: int
) -> None:
    """Saving a token for a user that doesn't exist should not raise or create one."""
    await save_token(db_session, sample_user_id, "orphan-token")

    user = await get_user(db_session, sample_user_id)
    assert user is None
