from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

from v2hub.models import ProviderAuthorizationStatus
from v2hub_bot.config import settings
from v2hub_bot.locales import ru as t


def main_menu(has_token: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if has_token:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_OPEN_PANEL,
                    web_app=WebAppInfo(url=settings.miniapp_url),
                    icon_custom_emoji_id="5985833664884250583",
                    style="success",
                )
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_MY_TOKEN,
                    callback_data="token:info",
                    icon_custom_emoji_id="6005570495603282482",
                    style="primary",
                )
            ]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_GET_TOKEN,
                    callback_data="token:generate",
                    icon_custom_emoji_id="6008135256798927387",
                    style="success",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_EXTENDED_MENU,
                callback_data="menu:extended",
                icon_custom_emoji_id="5886707481844912001",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_HELP, callback_data="help", icon_custom_emoji_id="6030848053177486888"
            ),
            InlineKeyboardButton(
                text=t.BTN_SUPPORT,
                callback_data="support",
                icon_custom_emoji_id="5936017305585586269",
            ),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def extended_menu(has_token: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if has_token:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_OPEN_PANEL,
                    web_app=WebAppInfo(url=settings.miniapp_url),
                    icon_custom_emoji_id="5985833664884250583",
                    style="success",
                )
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_MY_TOKEN,
                    callback_data="token:info",
                    icon_custom_emoji_id="6005570495603282482",
                    style="primary",
                )
            ]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_GET_TOKEN,
                    callback_data="token:generate",
                    icon_custom_emoji_id="6008135256798927387",
                    style="success",
                )
            ]
        )

    if settings.api_url and settings.github_url:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_V2HUB_API,
                    url=settings.api_url,
                    icon_custom_emoji_id="5884343982816759327",
                    style="primary",
                ),
                InlineKeyboardButton(
                    text=t.BTN_V2HUB_GITHUB,
                    url=settings.github_url,
                    icon_custom_emoji_id="5884343982816759327",
                    style="primary",
                ),
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_PROVIDER,
                callback_data="provider:menu",
                icon_custom_emoji_id="5931347928810526429",
                style="primary",
            ),
            InlineKeyboardButton(
                text=t.BTN_MY_PROVIDERS,
                callback_data="provider:my",
                icon_custom_emoji_id="6005570495603282482",
                style="primary",
            ),
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_EXTENDED_MENU,
                callback_data="menu",
                icon_custom_emoji_id="5886762118123886049",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_HELP, callback_data="help", icon_custom_emoji_id="6030848053177486888"
            ),
            InlineKeyboardButton(
                text=t.BTN_SUPPORT,
                callback_data="support",
                icon_custom_emoji_id="5936017305585586269",
            ),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def token_first_time() -> InlineKeyboardMarkup:
    """Клавиатура после автосоздания токена при первом запуске."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_OPEN_PANEL,
                    web_app=WebAppInfo(url=settings.miniapp_url),
                    icon_custom_emoji_id="5985833664884250583",
                    style="primary",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_MAIN_MENU,
                    callback_data="menu",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
        ]
    )


def token_actions(has_token: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if has_token:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_REFRESH_TOKEN,
                    callback_data="token:refresh",
                    icon_custom_emoji_id="6005843436479975944",
                    style="danger",
                )
            ]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_GET_TOKEN,
                    callback_data="token:generate",
                    icon_custom_emoji_id="6008135256798927387",
                    style="success",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_BACK, callback_data="menu", icon_custom_emoji_id="5875082500023258804"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_MAIN_MENU,
                    callback_data="menu",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ]
        ]
    )


def provider_intro() -> InlineKeyboardMarkup:
    """Клавиатура раздела 'Провайдер' для пользователей без роли provider."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_CONTACT_SUPPORT,
                    url=settings.support_url,
                    icon_custom_emoji_id="5936017305585586269",
                    style="primary",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_BACK,
                    callback_data="menu",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
        ]
    )


def provider_management() -> InlineKeyboardMarkup:
    """Клавиатура раздела 'Провайдер' для пользователей с ролью provider."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_PROVIDER_TOKEN,
                    callback_data="provider:token",
                    icon_custom_emoji_id="6005570495603282482",
                    style="primary",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_BACK,
                    callback_data="menu",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
        ]
    )


def provider_token_actions() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_PROVIDER_REFRESH_TOKEN,
                    callback_data="provider:token_refresh",
                    icon_custom_emoji_id="6005843436479975944",
                    style="danger",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_BACK,
                    callback_data="provider:menu",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
        ]
    )


def provider_page(
    provider_name: str,
    *,
    pending: bool = False,
    connected: bool = False,
) -> InlineKeyboardMarkup:
    """Клавиатура публичной страницы провайдера / запроса подключения.

    - pending=True  → показываем Connect / Reject
    - connected=True → показываем Disconnect
    - иначе          → только кнопка "Назад"
    """
    rows: list[list[InlineKeyboardButton]] = []

    if pending:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_CONNECT,
                    callback_data=f"provider:approve:{provider_name}",
                    icon_custom_emoji_id="6030445631921721471",
                    style="success",
                ),
                InlineKeyboardButton(
                    text=t.BTN_REJECT,
                    callback_data=f"provider:reject:{provider_name}",
                    icon_custom_emoji_id="6032636795387121097",
                    style="danger",
                ),
            ]
        )
    elif connected:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_DISCONNECT,
                    callback_data=f"provider:disconnect:{provider_name}",
                    icon_custom_emoji_id="6032636795387121097",
                    style="danger",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_BACK, callback_data="menu", icon_custom_emoji_id="5875082500023258804"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def my_providers(
    connections: dict[ProviderAuthorizationStatus, list[str]],
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    for name in connections.get(ProviderAuthorizationStatus.APPROVED, []):
        rows.append(
            [
                InlineKeyboardButton(
                    text=name,
                    callback_data=f"provider:view:{name}",
                    icon_custom_emoji_id="6005570495603282482",
                    style="success",
                )
            ]
        )

    for status, provider_names in connections.items():
        if status == ProviderAuthorizationStatus.APPROVED:
            continue

        for name in provider_names:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=name,
                        callback_data=f"provider:view:{name}",
                        icon_custom_emoji_id="5873121512445187130",
                        style="primary",
                    )
                ]
            )

    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_BACK,
                callback_data="menu",
                icon_custom_emoji_id="5875082500023258804",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def support() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_WRITE_SUPPORT,
                    url=settings.support_url,
                    icon_custom_emoji_id="5936017305585586269",
                    style="primary",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_BACK,
                    callback_data="menu",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
        ]
    )
