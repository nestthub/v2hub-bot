from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from helpers import make_callback, make_message, tg_user
from sqlalchemy import select

from v2hub_bot.db.models import User
from v2hub_bot.locales import i18n
from v2hub_bot.services.users import (
    get_translator_for,
    get_user_info_and_translator,
    set_user_language,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.unit

RU = i18n.get_translator("ru")
EN = i18n.get_translator("en")
FA = i18n.get_translator("fa")


async def _stored_lang(
    session_factory: async_sessionmaker[AsyncSession], user_id: int
) -> str | None:
    async with session_factory() as session:
        return (
            await session.execute(select(User.lang).where(User.id == user_id))
        ).scalar_one_or_none()


async def _add_user(
    session_factory: async_sessionmaker[AsyncSession], user_id: int, lang: str
) -> None:
    async with session_factory() as session:
        session.add(User(id=user_id, lang=lang))
        await session.commit()


# ── get_user_info_and_translator ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_without_from_user_returns_no_user_and_default_translator() -> None:
    user, t = await get_user_info_and_translator(make_message(user=None))

    assert user is None
    assert t("WELCOME_RETURNING") == EN("WELCOME_RETURNING")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("language_code", "expected_lang"),
    [("ru", "ru"), ("zh-hans", "zh"), ("pt-BR", "en"), (None, "en")],
)
async def test_new_user_gets_normalized_telegram_language(
    session_factory: async_sessionmaker[AsyncSession],
    language_code: str | None,
    expected_lang: str,
) -> None:
    """A missing/unsupported Telegram language must not break user creation."""
    message = make_message(tg_user(5, language_code=language_code))  # type: ignore[arg-type]

    user, t = await get_user_info_and_translator(message)

    assert user is not None
    assert user.lang == expected_lang
    assert await _stored_lang(session_factory, 5) == expected_lang
    assert t("WELCOME_RETURNING") == i18n.get_translator(expected_lang)("WELCOME_RETURNING")


@pytest.mark.asyncio
async def test_stored_language_wins_over_telegram_language(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await _add_user(session_factory, 5, "fa")
    call = make_callback(tg_user(5, language_code="ru"))

    user, t = await get_user_info_and_translator(call)

    assert user is not None
    assert user.lang == "fa"
    assert t("WELCOME_RETURNING") == FA("WELCOME_RETURNING")


# ── get_translator_for ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_translator_for_unknown_user_uses_telegram_language_without_creating_row(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    t = await get_translator_for(tg_user(5, language_code="ru"))

    assert t("WELCOME_RETURNING") == RU("WELCOME_RETURNING")
    assert await _stored_lang(session_factory, 5) is None


@pytest.mark.asyncio
async def test_get_translator_for_known_user_uses_stored_language(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await _add_user(session_factory, 5, "fa")

    t = await get_translator_for(tg_user(5, language_code="ru"))

    assert t("WELCOME_RETURNING") == FA("WELCOME_RETURNING")


# ── set_user_language ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_user_language_updates_existing_user(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await _add_user(session_factory, 5, "en")

    t = await set_user_language(5, "ru")

    assert await _stored_lang(session_factory, 5) == "ru"
    assert t("WELCOME_RETURNING") == RU("WELCOME_RETURNING")


@pytest.mark.asyncio
async def test_set_user_language_creates_missing_user(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await set_user_language(5, "fa")

    assert await _stored_lang(session_factory, 5) == "fa"


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", ["", "xx", "EN", "ru-RU", "../etc"])
async def test_set_user_language_rejects_unsupported_languages(
    session_factory: async_sessionmaker[AsyncSession], bad: str
) -> None:
    with pytest.raises(ValueError, match="unsupported language"):
        await set_user_language(5, bad)

    assert await _stored_lang(session_factory, 5) is None
