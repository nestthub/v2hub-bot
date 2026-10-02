from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

from v2hub.models import ProviderAuthorizationStatus
from v2hub_admin.models import ProviderResponse
from v2hub_bot.config import settings
from v2hub_bot.locales import ru as t
from v2hub_bot.utils import KeyboardData


def main_menu(has_token: bool = False, is_admin: bool = False) -> InlineKeyboardMarkup:
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

    if is_admin:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_PANEL,
                    callback_data="admin:panel",
                    icon_custom_emoji_id="5926783847453692661",
                    style="danger",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def extended_menu(has_token: bool = False, is_admin: bool = False) -> InlineKeyboardMarkup:
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

    if is_admin:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_PANEL,
                    callback_data="admin:panel",
                    icon_custom_emoji_id="5926783847453692661",
                    style="danger",
                )
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


def back(callback_data: str = "menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_MAIN_MENU if callback_data == "menu" else t.BTN_BACK,
                    callback_data=callback_data,
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
                    callback_data="menu:extended",
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


def admin_panel() -> InlineKeyboardMarkup:
    """Клавиатура администратора"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=t.BTN_ADMIN_STATS,
                callback_data="admin:stats",
                icon_custom_emoji_id="5994378914636500516",
                style="primary",
            )
        ],
        [
            InlineKeyboardButton(
                text=t.BTN_ADMIN_USERS,
                callback_data="admin:users",
                icon_custom_emoji_id="5886412370347036129",
                style="primary",
            ),
            InlineKeyboardButton(
                text=t.BTN_ADMIN_PROVIDERS,
                callback_data="admin:providers",
                icon_custom_emoji_id="5931347928810526429",
                style="primary",
            ),
        ],
        [
            InlineKeyboardButton(
                text=t.BTN_ADMIN_BROADCAST,
                callback_data="admin:broadcast",
                icon_custom_emoji_id="5771868281212245617",
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

    if settings.admin_panel_url:
        keyboard.insert(
            0,
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_PANEL_SETTINGS,
                    web_app=WebAppInfo(url=settings.admin_panel_url),
                    icon_custom_emoji_id="5985833664884250583",
                    style="success",
                )
            ],
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def stats() -> InlineKeyboardMarkup:
    """Статистика сервера"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_STATS_DAY,
                    callback_data="admin:stats:day",
                    icon_custom_emoji_id="5778546792148766155",
                    style="primary",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_STATS_WEEK,
                    callback_data="admin:stats:week",
                    icon_custom_emoji_id="5778158488450502097",
                    style="primary",
                ),
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_STATS_MONTH,
                    callback_data="admin:stats:month",
                    icon_custom_emoji_id="5778496382117613636",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_STATS_ALL,
                    callback_data="admin:stats:all",
                    icon_custom_emoji_id="5900104897885376843",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_STATS_OPTIONAL,
                    callback_data="admin:stats:optional",
                    icon_custom_emoji_id="5850317551090800862",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_BACK,
                    callback_data="admin:panel",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
        ]
    )


def admin_users_result(
    user_id: int, provider: ProviderResponse | None = None, is_exist: bool = True
) -> InlineKeyboardMarkup:
    """Клавиатура после поиска пользователя."""

    rows: list[list[InlineKeyboardButton]] = []

    if is_exist:
        providers_row = []

        if provider:
            providers_row.append(
                InlineKeyboardButton(
                    text=provider.provider_name,
                    callback_data=f"admin:provider:view:{provider.provider_hash}",
                    icon_custom_emoji_id="5931347928810526429",
                    style="primary",
                )
            )

        providers_row.append(
            InlineKeyboardButton(
                text=t.BTN_ADMIN_PROVIDERS,
                callback_data=f"admin:users:providers:{user_id}",
                icon_custom_emoji_id="5931347928810526429",
            )
        )

        rows.append(providers_row)

        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_USER_DELETE,
                    callback_data=f"admin:users:del:{user_id}",
                    icon_custom_emoji_id="6032636795387121097",
                    style="danger",
                )
            ]
        )

    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_USER_CREATE,
                    callback_data=f"admin:users:create:{user_id}",
                    icon_custom_emoji_id="5920090136627908485",
                    style="primary",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_BACK,
                callback_data="admin:panel",
                icon_custom_emoji_id="5875082500023258804",
            )
        ],
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_user_delete_confirm(user_id: int) -> InlineKeyboardMarkup:
    """Подтверждение необратимого удаления пользователя."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_USER_DELETE,
                    callback_data=f"admin:users:del_ok:{user_id}",
                    icon_custom_emoji_id="6032636795387121097",
                    style="danger",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_BROADCAST_CANCEL,
                    callback_data=f"admin:users:view:{user_id}",
                    icon_custom_emoji_id="5875082500023258804",
                ),
            ],
        ]
    )


def admin_broadcast_confirm() -> InlineKeyboardMarkup:
    """Подтверждение рассылки после предпросмотра."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_BROADCAST_CONFIRM,
                    callback_data="admin:broadcast:confirm",
                    icon_custom_emoji_id="6030445631921721471",
                    style="success",
                ),
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_BROADCAST_CANCEL,
                    callback_data="admin:broadcast:cancel",
                    icon_custom_emoji_id="6032636795387121097",
                    style="danger",
                ),
            ]
        ]
    )


def admin_broadcast_mode_select() -> InlineKeyboardMarkup:
    """Выбор способа подготовки рассылки: копировать целиком или собрать."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_BROADCAST_MODE_COPY,
                    callback_data="admin:broadcast:mode:copy",
                    icon_custom_emoji_id="5771868281212245617",
                    style="primary",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_BROADCAST_MODE_COMPOSE,
                    callback_data="admin:broadcast:mode:compose",
                    icon_custom_emoji_id="5931347928810526429",
                    style="primary",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_BACK,
                    callback_data="admin:panel",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
        ]
    )


def admin_broadcast_keyboard_builder() -> InlineKeyboardMarkup:
    """Клавиатура шага получения кнопок рассыли (режим «Собрать сообщение»)."""
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=t.BTN_ADMIN_BROADCAST_NO_KEYBOARD,
                callback_data="admin:broadcast:kb:finish",
                icon_custom_emoji_id="5875082500023258804",
                style="success",
            )
        ],
        [
            InlineKeyboardButton(
                text=t.BTN_ADMIN_BROADCAST_CANCEL,
                callback_data="admin:broadcast:cancel",
                icon_custom_emoji_id="6032636795387121097",
                style="danger",
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=rows)


def broadcast_custom_keyboard(
    keyboard_data: list[list[KeyboardData]] | None,
) -> InlineKeyboardMarkup | None:
    """Build an inline keyboard from parsed keyboard data."""

    if not keyboard_data:
        return None

    rows: list[list[InlineKeyboardButton]] = []

    for row in keyboard_data:
        keyboard_row: list[InlineKeyboardButton] = []

        for button in row:
            keyboard_row.append(
                InlineKeyboardButton(
                    text=button.text,
                    callback_data=button.callback_data,
                    url=button.url,
                    style=button.style,
                    icon_custom_emoji_id=button.emoji_id,
                )
            )
        rows.append(keyboard_row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_providers_list(provider_hashes: dict[str, str]) -> InlineKeyboardMarkup:
    """Список всех провайдеров + кнопка создания.

    provider_hashes maps provider_name -> provider_hash, as returned by
    AllProvidersResponse. The hash (not the name) is used in callback_data
    since it has a fixed, callback-data-safe length.
    """
    rows: list[list[InlineKeyboardButton]] = []

    for name, provider_hash in provider_hashes.items():
        rows.append(
            [
                InlineKeyboardButton(
                    text=name,
                    callback_data=f"admin:provider:view:{provider_hash}",
                    icon_custom_emoji_id="5931347928810526429",
                    style="primary",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_ADMIN_PROVIDER_CREATE,
                callback_data="admin:provider:create",
                icon_custom_emoji_id="6030445631921721471",
                style="success",
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=t.BTN_BACK,
                callback_data="admin:panel",
                icon_custom_emoji_id="5875082500023258804",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_provider_details(provider_hash: str) -> InlineKeyboardMarkup:
    """Управление конкретным провайдером: переименовать, URL, удалить."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_PROVIDER_RENAME,
                    callback_data=f"admin:provider:rename:{provider_hash}",
                    icon_custom_emoji_id="5931347928810526429",
                    style="primary",
                ),
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_PROVIDER_SET_URL,
                    callback_data=f"admin:provider:seturl:{provider_hash}",
                    icon_custom_emoji_id="5931347928810526429",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_PROVIDER_DELETE,
                    callback_data=f"admin:provider:del:{provider_hash}",
                    icon_custom_emoji_id="6032636795387121097",
                    style="danger",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_BACK,
                    callback_data="admin:providers",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
        ]
    )


def admin_provider_create_url() -> InlineKeyboardMarkup:
    """Показывается на шаге ввода URL при создании провайдера."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_PROVIDER_SKIP,
                    callback_data="admin:provider:create:url:skip",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_BACK,
                    callback_data="admin:providers",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
        ]
    )


def admin_provider_set_url_prompt(provider_hash: str) -> InlineKeyboardMarkup:
    """Показывается на шаге ввода нового URL для существующего провайдера."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_PROVIDER_CLEAR,
                    callback_data=f"admin:provider:clearurl:{provider_hash}",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t.BTN_BACK,
                    callback_data=f"admin:provider:view:{provider_hash}",
                    icon_custom_emoji_id="5875082500023258804",
                )
            ],
        ]
    )


def admin_provider_delete_confirm(provider_hash: str) -> InlineKeyboardMarkup:
    """Подтверждение необратимого удаления провайдера."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_PROVIDER_DELETE,
                    callback_data=f"admin:provider:del_ok:{provider_hash}",
                    icon_custom_emoji_id="6032636795387121097",
                    style="danger",
                ),
                InlineKeyboardButton(
                    text=t.BTN_ADMIN_BROADCAST_CANCEL,
                    callback_data=f"admin:provider:view:{provider_hash}",
                    icon_custom_emoji_id="5875082500023258804",
                ),
            ]
        ]
    )
