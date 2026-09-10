from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from v2hub_bot.locales import ru as t
from v2hub_bot.services import v2hub_client, v2hubError
from v2hub_bot.services.keyboards import back, token_actions

router = Router()


async def _token_info_text(user_id: int) -> tuple[str, bool, str | None]:
    """Returns (message_text, has_token, token_value).

    Always reads straight from the server — the bot never stores the
    token locally.
    """
    user = await v2hub_client.get_user(user_id)

    if not user or not user.api_token:
        return t.TOKEN_NONE, False, None

    text = t.TOKEN_INFO.format(token=user.api_token)
    return text, True, user.api_token


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
    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(text, reply_markup=token_actions(has_token))
    await call.answer()


@router.callback_query(F.data == "token:generate")
async def cb_token_generate(call: CallbackQuery) -> None:
    await call.answer(t.TOKEN_GENERATING)

    try:
        user = await v2hub_client.create_user(user_id=call.from_user.id)
        new_token = user.api_token
    except v2hubError as exc:
        if call.message and isinstance(call.message, Message):
            await call.message.edit_text(
                t.TOKEN_ERROR_GENERATE.format(error=exc),
                reply_markup=back(),
            )
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t.TOKEN_CREATED.format(token=new_token),
            reply_markup=back(),
        )


@router.callback_query(F.data == "token:refresh")
async def cb_token_refresh(call: CallbackQuery) -> None:
    user = await v2hub_client.get_user(call.from_user.id)

    if not user or not user.api_token:
        await call.answer(t.TOKEN_NO_ACTIVE, show_alert=True)
        return

    await call.answer(t.TOKEN_REFRESHING)

    try:
        new_token = await v2hub_client.refresh_token(user_id=call.from_user.id)
    except v2hubError as exc:
        if call.message and isinstance(call.message, Message):
            await call.message.edit_text(
                t.TOKEN_ERROR_REFRESH.format(error=exc),
                reply_markup=back(),
            )
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t.TOKEN_REFRESHED.format(token=new_token),
            reply_markup=back(),
        )
