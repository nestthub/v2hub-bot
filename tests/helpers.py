"""Shared test data and factories — the single place for them.

Import from here (``from helpers import t, tg_user, make_message, ...``)
instead of redefining Telegram mocks in every test module.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TgUser

from v2hub_admin.models import ProviderResponse
from v2hub_bot.locales import i18n

# Matches BOT_ADMINS in conftest.py.
ADMIN_ID = 7

# Default (English) translator. Also usable in @pytest.mark.parametrize,
# which is evaluated at collection time and so can't use fixtures.
t = i18n.get_translator()


def tg_user(user_id: int = 1, *, first_name: str = "Alice", language_code: str = "en") -> MagicMock:
    user = MagicMock(spec=TgUser)
    user.id = user_id
    user.first_name = first_name
    user.language_code = language_code
    return user


def make_message(user: MagicMock | None = None, text: str | None = None) -> MagicMock:
    # spec=Message so isinstance(message, Message) passes inside handlers/middlewares.
    message = MagicMock(spec=Message)
    message.from_user = user
    message.text = text
    message.html_text = text
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    return message


def make_callback(user: MagicMock | None = None, data: str | None = None) -> MagicMock:
    call = MagicMock(spec=CallbackQuery)
    call.from_user = user if user is not None else tg_user()
    call.data = data
    call.message = make_message()
    call.answer = AsyncMock()
    return call


def make_state() -> MagicMock:
    state = MagicMock(spec=FSMContext)
    state.clear = AsyncMock()
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    return state


def command_object(args: str | None) -> CommandObject:
    return CommandObject(prefix="/", command="start", args=args)


def make_provider(
    *,
    provider_hash: str = "hash1",
    provider_name: str = "vpn123",
    owner_hash: str = "owner-hash",
    provider_url: str | None = "https://example.com",
    api_token: str = "token123",
    is_active: bool = True,
) -> ProviderResponse:
    return ProviderResponse(
        provider_hash=provider_hash,
        owner_hash=owner_hash,
        provider_name=provider_name,
        api_token=api_token,
        provider_url=provider_url,
        is_active=is_active,
    )
