import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from v2hub_bot.config import settings
from v2hub_bot.locales import i18n
from v2hub_bot.services import get_user_info_and_translator, keyboards, set_user_language

router = Router()

LANGUAGE_PREFIX = "settings:language:"


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    await message.answer(t("SETTINGS_TEXT"), reply_markup=keyboards.bot_settings(t))


@router.callback_query(F.data == "settings")
async def cb_settings(call: CallbackQuery) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if isinstance(call.message, Message):
        await call.message.edit_text(t("SETTINGS_TEXT"), reply_markup=keyboards.bot_settings(t))
    await call.answer()


@router.callback_query(F.data == "settings:language")
async def cb_settings_language(call: CallbackQuery) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if isinstance(call.message, Message):
        await call.message.edit_text(
            t("SETTINGS_LANGUAGE_TEXT"),
            reply_markup=keyboards.language_settings(t),
        )
    await call.answer()


@router.callback_query(F.data.startswith(LANGUAGE_PREFIX))
async def cb_settings_language_select(call: CallbackQuery) -> None:
    if not call.data or not call.from_user or not isinstance(call.message, Message):
        return

    lang = call.data.removeprefix(LANGUAGE_PREFIX)
    if lang not in i18n.SUPPORTED_LANGUAGES:
        # Callback data is client-controlled: never store arbitrary values.
        await call.answer()
        return

    t = await set_user_language(call.from_user.id, lang)

    await call.message.edit_text(
        t("WELCOME_RETURNING").format(name=html.escape(call.from_user.first_name)),
        reply_markup=keyboards.main_menu(
            t,
            is_admin=call.from_user.id in settings.bot_admins,
        ),
    )
    await call.answer()
