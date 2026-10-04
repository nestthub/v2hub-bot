from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from v2hub_bot.services import get_user_info_and_translator, keyboards

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    await message.answer(t("HELP_TEXT"), reply_markup=keyboards.back(t))


@router.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(t("HELP_TEXT"), reply_markup=keyboards.back(t))
        await call.answer()
