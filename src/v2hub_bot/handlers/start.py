import html

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from v2hub_bot.config import settings
from v2hub_bot.handlers.token import _token_info_text
from v2hub_bot.services import get_user_info_and_translator, v2hub_client, v2hubError
from v2hub_bot.services.keyboards import extended_menu, main_menu, token_actions

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

    except v2hubError:
        return None, False

    return new_token, True


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, command: CommandObject) -> None:
    """Handle /start with a payload: `provider_*` and `conn_*` deep links."""
    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    if command.args == "token":
        text, has_token, _ = await _token_info_text(user.id, t)
        await message.answer(text, reply_markup=token_actions(has_token, t))
        return

    parsed = parse_deep_link_payload(command.args)
    if parsed is None:
        await message.answer(t("DEEP_LINK_INVALID"))
        return

    # Imported here to avoid a circular import between start.py and provider.py.
    from v2hub_bot.handlers.provider import handle_provider_deep_link

    kind, provider_name, hmac = parsed
    await handle_provider_deep_link(message, user.id, kind, provider_name, hmac, t)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user, t = await get_user_info_and_translator(message)
    if not user or not message.from_user:
        return

    name = html.escape(message.from_user.first_name)

    _, is_new = await _ensure_token(user.id)

    await message.answer(
        text=t("WELCOME_NEW" if is_new else "WELCOME_RETURNING").format(name=name),
        reply_markup=main_menu(t, is_admin=user.id in settings.bot_admins),
    )


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery) -> None:
    name = html.escape(call.from_user.first_name)

    if call.message and isinstance(call.message, Message):
        user, t = await get_user_info_and_translator(call)
        if not user:
            return

        await call.message.edit_text(
            t("WELCOME_RETURNING").format(name=name),
            reply_markup=main_menu(
                t,
                is_admin=call.from_user.id in settings.bot_admins,
            ),
        )
    await call.answer()


@router.callback_query(F.data == "menu:extended")
async def cb_extended_menu(call: CallbackQuery) -> None:
    name = html.escape(call.from_user.first_name)

    if call.message and isinstance(call.message, Message):
        user, t = await get_user_info_and_translator(call)
        if not user:
            return

        await call.message.edit_text(
            t("WELCOME_RETURNING").format(name=name),
            reply_markup=extended_menu(
                t,
                is_admin=call.from_user.id in settings.bot_admins,
            ),
        )
    await call.answer()
