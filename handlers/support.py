from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from locales import ru as t
from services import keyboards

router = Router()


@router.message(Command("support"))
async def cmd_support(message: Message) -> None:
    await message.answer(t.SUPPORT_TEXT, reply_markup=keyboards.support())


@router.callback_query(F.data == "support")
async def cb_support(call: CallbackQuery) -> None:
    await call.message.edit_text(t.SUPPORT_TEXT, reply_markup=keyboards.support())
    await call.answer()
