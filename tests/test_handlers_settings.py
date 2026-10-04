from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from helpers import ADMIN_ID, make_callback, make_message, t, tg_user
from sqlalchemy import select

from v2hub_bot.db.models import User
from v2hub_bot.handlers import settings as settings_handler
from v2hub_bot.locales import i18n

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.unit

RU = i18n.get_translator("ru")


def _callback_data(markup: InlineKeyboardMarkup) -> list[str | None]:
    return [button.callback_data for row in markup.inline_keyboard for button in row]


async def _stored_lang(
    session_factory: async_sessionmaker[AsyncSession], user_id: int
) -> str | None:
    async with session_factory() as session:
        return (
            await session.execute(select(User.lang).where(User.id == user_id))
        ).scalar_one_or_none()


# ── /settings ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cmd_settings_shows_settings_menu() -> None:
    message = make_message(tg_user())

    await settings_handler.cmd_settings(message)

    message.answer.assert_awaited_once()
    assert message.answer.await_args.args[0] == t("SETTINGS_TEXT")
    assert "settings:language" in _callback_data(message.answer.await_args.kwargs["reply_markup"])


@pytest.mark.asyncio
async def test_cmd_settings_without_from_user_does_nothing() -> None:
    message = make_message(user=None)

    await settings_handler.cmd_settings(message)

    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_cmd_settings_uses_users_language() -> None:
    message = make_message(tg_user(language_code="ru"))

    await settings_handler.cmd_settings(message)

    assert message.answer.await_args.args[0] == RU("SETTINGS_TEXT")


# ── settings callback ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_settings_edits_message_in_place() -> None:
    call = make_callback(tg_user(), "settings")

    await settings_handler.cb_settings(call)

    call.message.edit_text.assert_awaited_once()
    assert call.message.edit_text.await_args.args[0] == t("SETTINGS_TEXT")
    call.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cb_settings_with_inaccessible_message_only_answers() -> None:
    call = make_callback(tg_user(), "settings")
    call.message = None

    await settings_handler.cb_settings(call)

    call.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cb_settings_without_from_user_does_nothing() -> None:
    call = make_callback(tg_user(), "settings")
    call.from_user = None

    await settings_handler.cb_settings(call)

    call.message.edit_text.assert_not_called()
    call.answer.assert_not_called()


# ── language list ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cb_settings_language_lists_all_supported_languages() -> None:
    call = make_callback(tg_user(), "settings:language")

    await settings_handler.cb_settings_language(call)

    kwargs = call.message.edit_text.await_args.kwargs
    assert call.message.edit_text.await_args.args[0] == t("SETTINGS_LANGUAGE_TEXT")
    offered = {
        data.removeprefix(settings_handler.LANGUAGE_PREFIX)
        for data in _callback_data(kwargs["reply_markup"])
        if data and data.startswith(settings_handler.LANGUAGE_PREFIX)
    }
    assert offered == set(i18n.SUPPORTED_LANGUAGES)
    call.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cb_settings_language_with_inaccessible_message_only_answers() -> None:
    call = make_callback(tg_user(), "settings:language")
    call.message = None

    await settings_handler.cb_settings_language(call)

    call.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cb_settings_language_without_from_user_does_nothing() -> None:
    call = make_callback(tg_user(), "settings:language")
    call.from_user = None

    await settings_handler.cb_settings_language(call)

    call.message.edit_text.assert_not_called()


# ── choosing a language ──────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", sorted(i18n.SUPPORTED_LANGUAGES))
async def test_selecting_a_language_saves_it_and_shows_menu_in_that_language(
    session_factory: async_sessionmaker[AsyncSession], lang: str
) -> None:
    call = make_callback(tg_user(5, first_name="Bob"), f"settings:language:{lang}")

    await settings_handler.cb_settings_language_select(call)

    assert await _stored_lang(session_factory, 5) == lang
    call.message.edit_text.assert_awaited_once()
    text = call.message.edit_text.await_args.args[0]
    assert text == i18n.get_translator(lang)("WELCOME_RETURNING").format(name="Bob")
    assert call.message.edit_text.await_args.kwargs["reply_markup"] is not None
    call.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_selecting_a_language_escapes_the_name() -> None:
    call = make_callback(tg_user(5, first_name="<b>Bob</b>"), "settings:language:en")

    await settings_handler.cb_settings_language_select(call)

    assert "&lt;b&gt;Bob&lt;/b&gt;" in call.message.edit_text.await_args.args[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("admin", [True, False])
async def test_selecting_a_language_shows_admin_button_only_to_admins(admin: bool) -> None:
    user_id = ADMIN_ID if admin else 5
    call = make_callback(tg_user(user_id), "settings:language:en")

    await settings_handler.cb_settings_language_select(call)

    markup = call.message.edit_text.await_args.kwargs["reply_markup"]
    has_admin_button = "admin:panel" in _callback_data(markup)
    assert has_admin_button is admin


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", ["", "xx", "EN", "ru:extra", "x" * 64])
async def test_selecting_an_unsupported_language_is_ignored(
    session_factory: async_sessionmaker[AsyncSession], bad: str
) -> None:
    call = make_callback(tg_user(5), f"settings:language:{bad}")

    await settings_handler.cb_settings_language_select(call)

    assert await _stored_lang(session_factory, 5) is None
    call.message.edit_text.assert_not_called()
    call.answer.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("missing", ["data", "from_user", "message"])
async def test_selecting_a_language_with_incomplete_callback_does_nothing(missing: str) -> None:
    call = make_callback(tg_user(5), "settings:language:ru")
    setattr(call, missing, None)

    await settings_handler.cb_settings_language_select(call)

    call.answer.assert_not_called()


@pytest.mark.asyncio
async def test_selecting_a_language_with_non_message_payload_does_nothing() -> None:
    call = make_callback(tg_user(5), "settings:language:ru")
    call.message = MagicMock()  # not a Message instance (e.g. InaccessibleMessage)

    await settings_handler.cb_settings_language_select(call)

    call.answer.assert_not_called()
