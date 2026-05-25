from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

from config import settings
from locales import ru as t


def main_menu(has_token: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if has_token:
        rows.append([
            InlineKeyboardButton(
                text=t.BTN_OPEN_PANEL,
                web_app=WebAppInfo(url=settings.MINIAPP_URL),
                icon_custom_emoji_id='5985833664884250583',
                style="success"
            )
        ])
        rows.append([
            InlineKeyboardButton(
                text=t.BTN_MY_TOKEN,
                callback_data="token:info",
                icon_custom_emoji_id='6005570495603282482',
                style="primary",
            )
        ])
    else:
        rows.append([
            InlineKeyboardButton(
                text=t.BTN_GET_TOKEN,
                callback_data="token:generate",
                icon_custom_emoji_id="6008135256798927387",
                style="success",
            )
        ])

    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_HELP,
                callback_data="help",
                icon_custom_emoji_id="6030848053177486888"
                ),
            InlineKeyboardButton(
                text=t.BTN_SUPPORT,
                callback_data="support",
                icon_custom_emoji_id="5936017305585586269"
                ),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def token_first_time() -> InlineKeyboardMarkup:
    """Клавиатура после автосоздания токена при первом запуске."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t.BTN_OPEN_PANEL,
                web_app=WebAppInfo(url=settings.MINIAPP_URL),
                icon_custom_emoji_id='5985833664884250583',
                style="primary"
            )
        ],
        [
            InlineKeyboardButton(
                text=t.BTN_MAIN_MENU,
                callback_data="menu",
                icon_custom_emoji_id="5875082500023258804"
            )
        ],
    ])


def token_actions(has_token: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if has_token:
        rows.append([
            InlineKeyboardButton(
                text=t.BTN_REFRESH_TOKEN,
                callback_data="token:refresh",
                icon_custom_emoji_id="6005843436479975944",
                style="danger",
            )
        ])
    else:
        rows.append([
            InlineKeyboardButton(
                text=t.BTN_GET_TOKEN,
                callback_data="token:generate",
                icon_custom_emoji_id="6008135256798927387",
                style="success",
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text=t.BTN_BACK,
            callback_data="menu",
            icon_custom_emoji_id="5875082500023258804"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t.BTN_MAIN_MENU,
            callback_data="menu",
            icon_custom_emoji_id="5875082500023258804"
        )
    ]])


def support() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t.BTN_WRITE_SUPPORT,
                url=settings.SUPPORT_URL,
                icon_custom_emoji_id="5936017305585586269",
                style="primary"
            )
        ],
        [
            InlineKeyboardButton(
                text=t.BTN_BACK,
                callback_data="menu",
                icon_custom_emoji_id="5875082500023258804"
            )
        ],
    ])
