import html

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from v2hub_bot.config import settings
from v2hub_bot.db import async_session, get_or_create_user
from v2hub_bot.locales import ru as t
from v2hub_bot.services import V2HubError, v2hub_client
from v2hub_bot.services.keyboards import extended_menu, main_menu, token_first_time

router = Router()


def parse_deep_link_payload(args: str | None) -> tuple[str, str, str | None] | None:
    """Parse a /start deep-link payload.

    Returns (kind, provider_name, hmac) where kind is "provider" or "conn",
    or None if the payload doesn't match a known provider deep-link format.

        provider_{provider-name}          -> ("provider", provider-name, None)
        conn_{hmac}_{provider-name}       -> ("conn", provider-name, hmac)
    """
    if not args:
        return None

    if args.startswith("provider_"):
        provider_name = args[len("provider_") :]
        if not provider_name:
            return None
        return "provider", provider_name, None

    if args.startswith("conn_"):
        rest = args[len("conn_") :]
        # Format: {hmac}_{provider-name} - hmac itself never contains "_",
        # so split on the first underscore.
        parts = rest.split("_", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return None
        hmac, provider_name = parts
        return "conn", provider_name, hmac

    return None


async def _ensure_token(user_id: int) -> tuple[str | None, bool]:
    """
    Убеждается, что у пользователя есть токен на сервере, создавая его
    при необходимости. Токен нигде локально не хранится — только читается
    и, если нужно, создаётся через v2hub Admin API.

    Возвращает (token, is_new), где is_new=True значит, что аккаунт был
    создан прямо сейчас (у пользователя раньше не было записи на сервере).
    """
    existing = await v2hub_client.get_user(user_id)
    if existing is not None:
        return existing.api_token, False

    try:
        user = await v2hub_client.create_user(user_id=user_id)
        new_token = user.api_token

    except V2HubError:
        return None, False

    return new_token, True


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, command: CommandObject) -> None:
    """Handle /start with a payload: `provider_*` and `conn_*` deep links."""
    user = message.from_user
    if not user:
        return

    parsed = parse_deep_link_payload(command.args)
    if parsed is None:
        await message.answer(t.DEEP_LINK_INVALID)
        return

    # Локально помечаем, что этот Telegram user_id запускал бота.
    async with async_session() as session:
        await get_or_create_user(session, user.id)

    # Imported here to avoid a circular import between start.py and provider.py.
    from v2hub_bot.handlers.provider import handle_provider_deep_link

    kind, provider_name, hmac = parsed
    await handle_provider_deep_link(message, user.id, kind, provider_name, hmac)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    name = html.escape(user.first_name)

    # Локально помечаем, что этот Telegram user_id запускал бота, — это
    # единственное, что бот хранит о нём в своей базе.
    async with async_session() as session:
        await get_or_create_user(session, user.id)

    token, is_new = await _ensure_token(user.id)

    if is_new and token:
        # Шаг 1 — приветствие
        await message.answer(t.WELCOME_NEW.format(name=name))
        # Шаг 2 — токен с инструкцией и кнопками
        await message.answer(
            t.TOKEN_FIRST_TIME.format(token=token),
            reply_markup=token_first_time(),
        )
    else:
        await message.answer(
            t.WELCOME_RETURNING.format(name=name),
            reply_markup=main_menu(has_token=bool(token), is_admin=user.id in settings.bot_admins),
        )


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery) -> None:
    name = html.escape(call.from_user.first_name)

    user = await v2hub_client.get_user(call.from_user.id)

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t.WELCOME_RETURNING.format(name=name),
            reply_markup=main_menu(
                has_token=bool(user and user.api_token),
                is_admin=call.from_user.id in settings.bot_admins,
            ),
        )
    await call.answer()


@router.callback_query(F.data == "menu:extended")
async def cb_extended_menu(call: CallbackQuery) -> None:
    name = html.escape(call.from_user.first_name)

    user = await v2hub_client.get_user(call.from_user.id)

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t.WELCOME_RETURNING.format(name=name),
            reply_markup=extended_menu(
                has_token=bool(user and user.api_token),
                is_admin=call.from_user.id in settings.bot_admins,
            ),
        )
    await call.answer()
