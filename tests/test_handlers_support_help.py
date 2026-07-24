from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message

from v2hub_bot.handlers import help as help_handler
from v2hub_bot.handlers import support as support_handler

pytestmark = pytest.mark.unit


def _message() -> MagicMock:
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    return message


def _callback() -> MagicMock:
    call = MagicMock(spec=CallbackQuery)
    call.message = MagicMock(spec=Message)
    call.message.edit_text = AsyncMock()
    call.answer = AsyncMock()
    return call


# ── /support ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cmd_support_answers_with_keyboard() -> None:
    message = _message()

    await support_handler.cmd_support(message)

    message.answer.assert_awaited_once()
    assert message.answer.await_args.kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_cb_support_edits_message() -> None:
    call = _callback()

    await support_handler.cb_support(call)

    call.message.edit_text.assert_awaited_once()
    call.answer.assert_awaited_once()


# ── /help ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cmd_help_answers_with_keyboard() -> None:
    message = _message()

    await help_handler.cmd_help(message)

    message.answer.assert_awaited_once()
    assert message.answer.await_args.kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_cb_help_edits_message_and_answers() -> None:
    call = _callback()

    await help_handler.cb_help(call)

    call.message.edit_text.assert_awaited_once()
    call.answer.assert_awaited_once()
