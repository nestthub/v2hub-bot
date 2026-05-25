from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from db.crud import get_or_create_user, get_user, save_token
from db.engine import async_session
from locales import ru as t
from services.keyboards import back_to_menu, token_actions
from services.v2hub import V2HubError, v2hub_client

router = Router()


async def _token_info_text(user_id: int) -> tuple[str, bool, str | None]:
    """Returns (message_text, has_token, token_value)."""
    async with async_session() as session:
        db_user = await get_user(session, user_id)

    if not db_user or not db_user.api_token:
        return t.TOKEN_NONE, False, None

    generated = (
        db_user.token_generated_at.strftime("%d.%m.%Y %H:%M UTC")
        if db_user.token_generated_at
        else "неизвестно"
    )

    text = t.TOKEN_INFO.format(token=db_user.api_token, generated_at=generated)
    return text, True, db_user.api_token


# ── /token ────────────────────────────────────────────────────────────────────

@router.message(Command("token"))
async def cmd_token(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    text, has_token, _ = await _token_info_text(user.id)
    await message.answer(text, reply_markup=token_actions(has_token))


# ── Callbacks ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "token:info")
async def cb_token_info(call: CallbackQuery) -> None:
    text, has_token, _ = await _token_info_text(call.from_user.id)
    await call.message.edit_text(text, reply_markup=token_actions(has_token))
    await call.answer()


@router.callback_query(F.data == "token:generate")
async def cb_token_generate(call: CallbackQuery) -> None:
    await call.answer(t.TOKEN_GENERATING)

    try:
        new_token = await v2hub_client.create_user(user_id=call.from_user.id)
    except V2HubError as exc:
        await call.message.edit_text(
            t.TOKEN_ERROR_GENERATE.format(error=exc),
            reply_markup=back_to_menu(),
        )
        return

    async with async_session() as session:
        await get_or_create_user(session, user_id=call.from_user.id)
        await save_token(session, call.from_user.id, new_token)

    await call.message.edit_text(
        t.TOKEN_CREATED.format(token=new_token),
        reply_markup=back_to_menu(),
    )


@router.callback_query(F.data == "token:refresh")
async def cb_token_refresh(call: CallbackQuery) -> None:
    async with async_session() as session:
        db_user = await get_user(session, call.from_user.id)

    if not db_user or not db_user.api_token:
        await call.answer(t.TOKEN_NO_ACTIVE, show_alert=True)
        return

    await call.answer(t.TOKEN_REFRESHING)

    try:
        new_token = await v2hub_client.refresh_token(user_id=call.from_user.id)
    except V2HubError as exc:
        await call.message.edit_text(
            t.TOKEN_ERROR_REFRESH.format(error=exc),
            reply_markup=back_to_menu(),
        )
        return

    async with async_session() as session:
        await save_token(session, call.from_user.id, new_token)

    await call.message.edit_text(
        t.TOKEN_REFRESHED.format(token=new_token),
        reply_markup=back_to_menu(),
    )
