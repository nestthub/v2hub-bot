from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from v2hub_bot.db.crud import (
    count_users,
    delete_local_user,
    get_all_user_ids,
    get_or_create_user,
    get_sorted_user_ids,
    get_user,
    update_user_lang,
)
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


# ── language ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_or_create_user_defaults_language_to_en_when_none_given(
    db_session: AsyncSession, sample_user_id: int
) -> None:
    """lang=None must fall back to the column default, not violate NOT NULL."""
    user = await get_or_create_user(db_session, sample_user_id, lang=None)

    assert user.lang == "en"


@pytest.mark.asyncio
async def test_get_or_create_user_stores_given_language(
    db_session: AsyncSession, sample_user_id: int
) -> None:
    user = await get_or_create_user(db_session, sample_user_id, lang="ru")

    assert user.lang == "ru"


@pytest.mark.asyncio
async def test_get_or_create_user_does_not_overwrite_language_of_existing_user(
    db_session: AsyncSession, existing_user: User
) -> None:
    user = await get_or_create_user(db_session, existing_user.id, lang="ru")

    assert user.lang == "en"


@pytest.mark.asyncio
async def test_update_user_lang_changes_language(
    db_session: AsyncSession, existing_user: User
) -> None:
    await update_user_lang(db_session, existing_user.id, "fa")

    refreshed = await get_user(db_session, existing_user.id)
    assert refreshed is not None
    assert refreshed.lang == "fa"


@pytest.mark.asyncio
async def test_update_user_lang_ignores_unknown_user(db_session: AsyncSession) -> None:
    await update_user_lang(db_session, 999, "fa")

    assert await get_user(db_session, 999) is None


# ── listings / counters ──────────────────────────────────────────────────────


async def _seed(db_session: AsyncSession) -> None:
    """1: ru, Jan 2024 | 2: en, Feb 2024 | 3: ru, Mar 2024 (banned) | 4: en, Apr 2024."""
    rows = [
        (1, "ru", False, datetime(2024, 1, 10, tzinfo=UTC)),
        (2, "en", False, datetime(2024, 2, 10, tzinfo=UTC)),
        (3, "ru", True, datetime(2024, 3, 10, tzinfo=UTC)),
        (4, "en", False, datetime(2024, 4, 10, tzinfo=UTC)),
    ]
    for user_id, lang, banned, created in rows:
        db_session.add(User(id=user_id, lang=lang, is_banned=banned, created_at=created))
    await db_session.commit()


@pytest.mark.asyncio
async def test_count_users(db_session: AsyncSession) -> None:
    assert await count_users(db_session) == 0

    await _seed(db_session)

    assert await count_users(db_session) == 4


@pytest.mark.asyncio
async def test_get_all_user_ids_excludes_banned_by_default(db_session: AsyncSession) -> None:
    await _seed(db_session)

    assert sorted(await get_all_user_ids(db_session)) == [1, 2, 4]
    assert sorted(await get_all_user_ids(db_session, exclude_banned=False)) == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_get_sorted_user_ids_orders_by_creation_time(db_session: AsyncSession) -> None:
    await _seed(db_session)

    assert await get_sorted_user_ids(db_session) == [1, 2, 4]
    assert await get_sorted_user_ids(db_session, exclude_banned=False) == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_get_sorted_user_ids_filters_by_language(db_session: AsyncSession) -> None:
    await _seed(db_session)

    assert await get_sorted_user_ids(db_session, lang="en") == [2, 4]
    assert await get_sorted_user_ids(db_session, lang="ru") == [1]  # 3 is banned
    assert await get_sorted_user_ids(db_session, lang="ru", exclude_banned=False) == [1, 3]
    assert await get_sorted_user_ids(db_session, lang="fa") == []


@pytest.mark.asyncio
async def test_get_sorted_user_ids_filters_by_date_range(db_session: AsyncSession) -> None:
    await _seed(db_session)

    start, end = datetime(2024, 2, 1, tzinfo=UTC), datetime(2024, 4, 1, tzinfo=UTC)

    assert await get_sorted_user_ids(db_session, start_time=start) == [2, 4]
    assert await get_sorted_user_ids(db_session, end_time=end) == [1, 2]
    assert await get_sorted_user_ids(db_session, start_time=start, end_time=end) == [2]
    assert await get_sorted_user_ids(db_session, start_time=start, lang="en") == [2, 4]


@pytest.mark.asyncio
async def test_delete_local_user_removes_only_that_user(db_session: AsyncSession) -> None:
    await _seed(db_session)

    await delete_local_user(db_session, 1)

    assert await get_user(db_session, 1) is None
    assert await count_users(db_session) == 3


@pytest.mark.asyncio
async def test_delete_local_user_is_idempotent(db_session: AsyncSession) -> None:
    await delete_local_user(db_session, 999)

    assert await count_users(db_session) == 0
