from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from v2hub_bot.db import async_session, get_or_create_user, get_user, save_token
from v2hub_bot.locales import ru as t
from v2hub_bot.services import V2HubError, v2hub_client
from v2hub_bot.services.keyboards import main_menu, token_first_time

router = Router()


async def _ensure_token(user_id: int) -> str | None:
    """
    Создаёт токен автоматически, если его нет.
    Возвращает токен (новый или существующий), либо None при ошибке API.
    """
    async with async_session() as session:
        db_user = await get_or_create_user(session, user_id)

    if db_user.api_token:
        return db_user.api_token

    try:
        new_token = await v2hub_client.create_user(user_id=user_id)
    except V2HubError:
        return None

    async with async_session() as session:
        await save_token(session, user_id, new_token)

    return new_token


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    import html

    name = html.escape(user.first_name)

    # Проверяем, новый ли пользователь (нет токена до этого вызова)
    async with async_session() as session:
        existing = await get_user(session, user.id)
    is_new = existing is None or not existing.api_token

    token = await _ensure_token(user.id)

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
            reply_markup=main_menu(has_token=bool(token)),
        )


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery) -> None:
    import html

    name = html.escape(call.from_user.first_name)

    async with async_session() as session:
        db_user = await get_or_create_user(session, call.from_user.id)

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t.WELCOME_RETURNING.format(name=name),
            reply_markup=main_menu(has_token=bool(db_user.api_token)),
        )
    await call.answer()
