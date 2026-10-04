from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TgUser

from v2hub_bot.db import User, async_session, get_or_create_user, get_user, update_user_lang
from v2hub_bot.locales import i18n


async def get_user_info_and_translator(
    event: Message | CallbackQuery,
) -> tuple[User | None, i18n.Translator]:
    """Return the local user (created on first contact) and a translator
    for the language the user picked (Telegram's language on first contact)."""
    if not event.from_user:
        return None, i18n.get_translator()

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            user_id=event.from_user.id,
            lang=i18n.normalize_lang(event.from_user.language_code),
        )

        return user, i18n.get_translator(user.lang)


async def get_translator_for(tg_user: TgUser) -> i18n.Translator:
    """Translator for a Telegram user without creating a local record.

    Prefers the language chosen in the bot's settings, then Telegram's language.
    """
    async with async_session() as session:
        user = await get_user(session, tg_user.id)

    return i18n.get_translator(user.lang if user else tg_user.language_code)


async def set_user_language(user_id: int, lang: str) -> i18n.Translator:
    """Persist the interface language and return the matching translator."""
    if lang not in i18n.SUPPORTED_LANGUAGES:
        raise ValueError(f"unsupported language: {lang!r}")

    async with async_session() as session:
        await get_or_create_user(session, user_id=user_id, lang=lang)
        await update_user_lang(session, user_id, lang)

    return i18n.get_translator(lang)
