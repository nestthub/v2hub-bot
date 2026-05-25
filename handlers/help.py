from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from locales import ru as t
from services import keyboards

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(t.HELP_TEXT, reply_markup=keyboards.back_to_menu())


@router.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery) -> None:
    await call.message.edit_text(t.HELP_TEXT, reply_markup=keyboards.back_to_menu())
    await call.answer()
