import asyncio
import contextlib
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from v2hub_bot.db import async_session, delete_local_user, get_all_user_ids
from v2hub_bot.db import get_user as get_local_user
from v2hub_bot.handlers.admin_states import AdminStates
from v2hub_bot.locales.i18n import Translator
from v2hub_bot.middlewares import AdminMiddleware
from v2hub_bot.services import get_user_info_and_translator, keyboards, v2hub_client, v2hubError
from v2hub_bot.utils import parse_keyboard

if TYPE_CHECKING:
    from v2hub.models import ProviderAuthorizationStatus

logger = logging.getLogger(__name__)

router = Router()
router.callback_query.middleware(AdminMiddleware())
router.message.middleware(AdminMiddleware())

# Keep strong references to in-flight broadcast tasks so they are not
# garbage-collected while still running (asyncio only keeps weak references).
_broadcast_tasks: set[asyncio.Task[None]] = set()

# Telegram Bot API tolerates roughly 30 messages/sec globally, but we cap
# broadcasts well below that (16/sec) to leave headroom for other bot traffic
# and to reduce the risk of hitting per-chat flood limits.
_BROADCAST_MAX_PER_SECOND = 16
_BROADCAST_MIN_INTERVAL = 1 / _BROADCAST_MAX_PER_SECOND


# ── Main admin panel ──────────────────────────────────────────────────────────


@router.callback_query(F.data == "admin:panel")
async def admin_panel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(t("ADMIN_PANEL_TITLE"), reply_markup=keyboards.admin_panel(t))
    await call.answer()


# ── Statistics ────────────────────────────────────────────────────────────────


@router.callback_query(F.data == "admin:stats")
async def admin_stats(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(t("ADMIN_STATS_SELECT"), reply_markup=keyboards.stats(t))
    await call.answer()


@router.callback_query(F.data.startswith("admin:stats:"))
async def get_stats(call: CallbackQuery, state: FSMContext) -> None:
    if not call.message or not isinstance(call.message, Message) or not call.data:
        return

    selected = call.data.split(":")[-1]

    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if selected == "optional":
        await call.message.edit_text(
            t("ADMIN_STATS_GET_OPTIONAL_PERIOD"),
            reply_markup=keyboards.back(t, callback_data="admin:stats"),
        )
        await state.set_state(AdminStates.waiting_stats_period)
        await call.answer()
        return

    if selected not in ("day", "week", "month", "all"):
        await call.answer()
        return

    period_map: dict[str, Literal["day", "week", "month"] | None] = {
        "day": "day",
        "week": "week",
        "month": "month",
        "all": None,
    }
    period = period_map[selected]

    _PERIOD_LABELS = {
        "day": t("ADMIN_STATS_PERIOD_LABEL_DAY"),
        "week": t("ADMIN_STATS_PERIOD_LABEL_WEEK"),
        "month": t("ADMIN_STATS_PERIOD_LABEL_MONTH"),
        "all": t("ADMIN_STATS_PERIOD_LABEL_ALL"),
    }

    await _render_stats(call, period=period, label=_PERIOD_LABELS[selected], t=t)
    await call.answer()


@router.message(AdminStates.waiting_stats_period)
async def receive_stats_period(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    start_date, end_date = _parse_period(raw)

    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    if start_date is None and end_date is None:
        await message.answer(
            t("ADMIN_STATS_PERIOD_INVALID"),
            reply_markup=keyboards.back(t, callback_data="admin:stats"),
        )
        return

    label = t("ADMIN_STATS_PERIOD_LABEL_CUSTOM").format(
        start_date=start_date.strftime("%Y-%m-%d")
        if start_date
        else t("ADMIN_STATS_PERIOD_LABEL_CUSTOM_START"),
        end_date=end_date.strftime("%Y-%m-%d")
        if end_date
        else t("ADMIN_STATS_PERIOD_LABEL_CUSTOM_END"),
    )

    await state.clear()
    await _render_stats(
        message,
        start_date=start_date,
        end_date=end_date,
        label=label,
        t=t,
    )


def _parse_period(raw: str) -> tuple[datetime | None, datetime | None]:
    """Parse a `YYYY-MM-DD : YYYY-MM-DD` date range with either side optional."""
    if ":" not in raw:
        return None, None

    start_raw, _, end_raw = raw.partition(":")
    start_raw = start_raw.strip()
    end_raw = end_raw.strip()

    try:
        start_date = datetime.fromisoformat(start_raw) if start_raw else None
        end_date = datetime.fromisoformat(end_raw) if end_raw else None
    except ValueError:
        return None, None

    if start_date is None and end_date is None:
        return None, None

    return start_date, end_date


async def _render_stats(
    event: Message | CallbackQuery,
    *,
    label: str,
    period: Literal["day", "week", "month"] | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    t: Translator,
) -> None:
    try:
        stats = await v2hub_client.get_stats(
            start_date=start_date, end_date=end_date, period=period
        )
    except v2hubError as exc:
        if (
            isinstance(event, CallbackQuery)
            and event.message
            and isinstance(event.message, Message)
        ):
            await event.message.edit_text(
                t("ADMIN_STATS_ERROR").format(error=exc),
                reply_markup=keyboards.back(t, callback_data="admin:stats"),
            )

        else:
            await event.answer(
                t("ADMIN_STATS_ERROR").format(error=exc),
                reply_markup=keyboards.back(t, callback_data="admin:stats"),
            )
        return

    if isinstance(event, CallbackQuery) and event.message and isinstance(event.message, Message):
        await event.message.edit_text(
            t("ADMIN_STATS_INFO").format(
                period=label,
                total_users=stats.general.total_users,
                new_users=stats.general.new_users,
                new_subs=stats.general.new_subscriptions,
            ),
            reply_markup=keyboards.back(t, callback_data="admin:stats"),
        )

    else:
        await event.answer(
            t("ADMIN_STATS_INFO").format(
                period=label,
                total_users=stats.general.total_users,
                new_users=stats.general.new_users,
                new_subs=stats.general.new_subscriptions,
            ),
            reply_markup=keyboards.back(t, callback_data="admin:stats"),
        )


# ── Users ─────────────────────────────────────────────────────────────────────


async def _admin_users_view(user_id: int, event: Message | CallbackQuery, t: Translator) -> None:
    user = await v2hub_client.get_user(user_id)

    if user is None:
        if isinstance(event, Message):
            await event.answer(
                t("ADMIN_USERS_NOT_FOUND").format(user_id=user_id),
                reply_markup=keyboards.admin_users_result(user_id=user_id, t=t, is_exist=False),
            )
        elif event.message and isinstance(event.message, Message):
            await event.message.edit_text(
                t("ADMIN_USERS_NOT_FOUND").format(user_id=user_id),
                reply_markup=keyboards.admin_users_result(user_id=user_id, t=t, is_exist=False),
            )
        return

    provider = await v2hub_client.get_provider_by_owner_id(owner_id=user_id)

    provider_name = provider.provider_name if provider else None

    async with async_session() as session:
        local_user = await get_local_user(session, user_id)

    created_at = (
        local_user.created_at.strftime("%Y-%m-%d %H:%M") if local_user else t("ADMIN_USERS_UNKNOWN")
    )

    is_banned = "yes" if local_user and local_user.is_banned else "no"

    text = t("ADMIN_USERS_INFO").format(
        user_id=user_id,
        api_token=user.api_token,
        provider_name=provider_name or "-",
        created_at=created_at,
        is_banned=is_banned,
    )

    reply_markup = keyboards.admin_users_result(user_id=user_id, t=t, provider=provider)

    if isinstance(event, Message):
        await event.answer(text=text, reply_markup=reply_markup)
    elif event.message and isinstance(event.message, Message):
        await event.message.edit_text(text=text, reply_markup=reply_markup)


@router.callback_query(F.data == "admin:users")
async def admin_users(call: CallbackQuery, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t("ADMIN_USERS_PROMPT"),
            reply_markup=keyboards.back(t, callback_data="admin:panel"),
        )
    await state.set_state(AdminStates.waiting_user_id)
    await call.answer()


@router.message(AdminStates.waiting_user_id)
async def receive_user_id(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()

    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    if not raw.lstrip("-").isdigit():
        await message.answer(
            t("ADMIN_USERS_INVALID_ID"),
            reply_markup=keyboards.back(t, callback_data="admin:panel"),
        )
        return

    user_id = int(raw)
    await state.clear()

    await _admin_users_view(user_id, message, t)


@router.callback_query(F.data.startswith("admin:users:create:"))
async def admin_users_create(call: CallbackQuery) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.data and len(call.data.split(":")) == 4 and call.data.split(":")[-1].isdigit():
        user_id = int(call.data.split(":")[-1])
    else:
        await call.answer()
        return

    await v2hub_client.create_user(user_id)

    await _admin_users_view(user_id, call, t)

    await call.answer()


@router.callback_query(F.data.startswith("admin:users:view:"))
async def admin_users_view(call: CallbackQuery) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.data and len(call.data.split(":")) == 4 and call.data.split(":")[-1].isdigit():
        user_id = int(call.data.split(":")[-1])
    else:
        await call.answer()
        return

    await _admin_users_view(user_id, call, t)

    await call.answer()


@router.callback_query(F.data.startswith("admin:users:providers:"))
async def admin_users_providers(call: CallbackQuery) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.data and len(call.data.split(":")) == 4 and call.data.split(":")[-1].isdigit():
        user_id = int(call.data.split(":")[-1])
    else:
        await call.answer()
        return

    connections = await v2hub_client.get_user_connections(user_id)

    my_connections: dict[ProviderAuthorizationStatus, list[str]] = {}

    for connection in connections.connections:
        if connection.status:
            my_connections.setdefault(connection.status, []).append(connection.provider_name)

    if call.message and isinstance(call.message, Message):
        if not my_connections:
            await call.message.edit_text(
                t("ADMIN_USERS_PROVIDERS_NOT_FOUND"),
                reply_markup=keyboards.back(t, f"admin:users:view:{user_id}"),
            )
        else:
            await call.message.edit_text(
                t("MY_PROVIDERS_TITLE"),
                reply_markup=keyboards.my_providers(my_connections, t),
            )

    await call.answer()


# ── User deletion ─────────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin:users:del:"))
async def admin_users_delete_confirm(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if not (call.data and len(call.data.split(":")) == 4 and call.data.split(":")[-1].isdigit()):
        await call.answer()
        return
    user_id = int(call.data.split(":")[-1])

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t("ADMIN_USERS_DELETE_CONFIRM").format(user_id=user_id),
            reply_markup=keyboards.admin_user_delete_confirm(user_id, t),
        )
    await call.answer()


@router.callback_query(F.data.startswith("admin:users:del_ok:"))
async def admin_users_delete_execute(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if not (call.data and len(call.data.split(":")) == 4 and call.data.split(":")[-1].isdigit()):
        await call.answer()
        return
    user_id = int(call.data.split(":")[-1])

    try:
        await v2hub_client.delete_user(user_id)
    except v2hubError as exc:
        if call.message and isinstance(call.message, Message):
            await call.message.edit_text(
                t("ADMIN_USERS_DELETE_ERROR").format(error=exc),
                reply_markup=keyboards.back(t, callback_data="admin:panel"),
            )
        await call.answer()
        return

    async with async_session() as session:
        await delete_local_user(session, user_id)

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t("ADMIN_USERS_DELETED").format(user_id=user_id),
            reply_markup=keyboards.back(t, callback_data="admin:panel"),
        )
    await call.answer()


# ── Broadcast ─────────────────────────────────────────────────────────────────
# Two authoring modes share the same delivery mechanism:
#
#   "copy"    — the admin sends one ready-made message (text/media/etc.) and
#               it is re-sent to every recipient via Bot.copy_message.
#
#   "compose" — the admin sends content (text and/or media) and then builds
#               an inline keyboard on top of it. Each button can be either
#               a URL button or a callback_data button.
#
# Both modes end up as a (source_chat_id, source_message_id, reply_markup)
# triple delivered to every recipient via Bot.copy_message. This copies
# any supported content type and optionally applies a custom reply_markup,
# allowing both flows to share the same delivery path.


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t("ADMIN_BROADCAST_SELECT_MODE"),
            reply_markup=keyboards.admin_broadcast_mode_select(t),
        )
    await state.set_state(AdminStates.choosing_broadcast_mode)
    await call.answer()


@router.callback_query(AdminStates.choosing_broadcast_mode, F.data == "admin:broadcast:mode:copy")
async def admin_broadcast_mode_copy(call: CallbackQuery, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t("ADMIN_BROADCAST_PROMPT"),
            reply_markup=keyboards.back(t, callback_data="admin:broadcast"),
        )
    await state.set_state(AdminStates.waiting_broadcast_message)
    await call.answer()


@router.callback_query(
    AdminStates.choosing_broadcast_mode, F.data == "admin:broadcast:mode:compose"
)
async def admin_broadcast_mode_compose(call: CallbackQuery, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t("ADMIN_BROADCAST_CONTENT_PROMPT"),
            reply_markup=keyboards.back(t, callback_data="admin:broadcast"),
        )
    await state.set_state(AdminStates.waiting_broadcast_content)
    await call.answer()


# ── "Copy as is" mode ─────────────────────────────────────────────────────────


@router.message(AdminStates.waiting_broadcast_message)
async def receive_broadcast_message(message: Message, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    await _stage_broadcast_source(message, state)
    await _show_broadcast_preview(message, state, t)


# ── "Compose message" mode ────────────────────────────────────────────────────


@router.message(AdminStates.waiting_broadcast_content)
async def receive_broadcast_content(message: Message, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    await _stage_broadcast_source(message, state)
    await state.set_state(AdminStates.waiting_broadcast_keyboard)
    await message.answer(
        t("ADMIN_BROADCAST_KEYBOARD_BUILDER"),
        reply_markup=keyboards.admin_broadcast_keyboard_builder(t),
    )


async def _stage_broadcast_source(message: Message, state: FSMContext) -> None:
    """Store the message that will be copied to every recipient.

    In "copy" mode, the message already contains any reply_markup it had.
    In "compose" mode, the keyboard is built separately and passed explicitly
    during delivery.
    """
    await state.update_data(
        broadcast_chat_id=message.chat.id,
        broadcast_message_id=message.message_id,
        reply_markup=message.reply_markup.model_dump() if message.reply_markup else None,
    )


@router.message(AdminStates.waiting_broadcast_keyboard)
async def receive_broadcast_keyboard(message: Message, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    keyboard_text = message.html_text

    keyboard_data = parse_keyboard(keyboard_text)

    reply_markup = keyboards.broadcast_custom_keyboard(keyboard_data=keyboard_data)

    await state.update_data(reply_markup=reply_markup.model_dump() if reply_markup else None)

    await _show_broadcast_preview(message, state, t)


@router.callback_query(
    AdminStates.waiting_broadcast_keyboard, F.data == "admin:broadcast:kb:finish"
)
async def admin_broadcast_kb_finish(call: CallbackQuery, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.message and isinstance(call.message, Message):
        await _show_broadcast_preview(call.message, state, t)
    await call.answer()


async def _show_broadcast_preview(message: Message, state: FSMContext, t: Translator) -> None:
    data = await state.get_data()
    source_chat_id: int | None = data.get("broadcast_chat_id")
    source_message_id: int | None = data.get("broadcast_message_id")
    reply_markup_data = data.get("reply_markup")

    reply_markup = InlineKeyboardMarkup(**reply_markup_data) if reply_markup_data else None

    if source_chat_id is None or source_message_id is None or message.bot is None:
        await message.answer(
            t("ADMIN_BROADCAST_NO_CONTENT"),
            reply_markup=keyboards.back(t, callback_data="admin:panel"),
        )
        await state.clear()
        return

    async with async_session() as session:
        user_ids = await get_all_user_ids(session)

    await state.update_data(recipient_ids=list(user_ids))
    await state.set_state(AdminStates.confirming_broadcast)

    # Show a preview that matches what recipients will receive.
    with contextlib.suppress(Exception):
        final_message_id = await message.bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=source_chat_id,
            message_id=source_message_id,
            reply_markup=reply_markup,
        )

        await state.update_data(broadcast_message_id=final_message_id.message_id)

    await message.answer(
        t("ADMIN_BROADCAST_PREVIEW").format(count=len(user_ids)),
        reply_markup=keyboards.admin_broadcast_confirm(t),
    )


@router.callback_query(AdminStates.confirming_broadcast, F.data == "admin:broadcast:cancel")
async def cancel_broadcast(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t("ADMIN_BROADCAST_CANCELLED"),
            reply_markup=keyboards.back(t, callback_data="admin:panel"),
        )
    await call.answer()


@router.callback_query(AdminStates.confirming_broadcast, F.data == "admin:broadcast:confirm")
async def confirm_broadcast(call: CallbackQuery, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    data = await state.get_data()
    source_chat_id: int | None = data.get("broadcast_chat_id")
    source_message_id: int | None = data.get("broadcast_message_id")
    recipient_ids: list[int] = data.get("recipient_ids", [])
    reply_markup_data = data.get("reply_markup")

    reply_markup = InlineKeyboardMarkup(**reply_markup_data) if reply_markup_data else None
    await state.clear()

    if (
        source_chat_id is None
        or source_message_id is None
        or not call.message
        or not isinstance(call.message, Message)
    ):
        await call.answer()
        return

    await call.message.edit_text(t("ADMIN_BROADCAST_STARTED").format(count=len(recipient_ids)))
    await call.answer()

    bot = call.message.bot
    if bot is None:
        return

    # Run the broadcast in the background so normal bot update handling
    # remains responsive.
    task = asyncio.create_task(
        _run_broadcast(
            bot,
            call.message,
            source_chat_id=source_chat_id,
            reply_markup=reply_markup,
            source_message_id=source_message_id,
            recipient_ids=recipient_ids,
            t=t,
        )
    )
    _broadcast_tasks.add(task)
    task.add_done_callback(_broadcast_tasks.discard)


async def _run_broadcast(
    bot: Any,
    progress_message: Message,
    *,
    reply_markup: InlineKeyboardMarkup | None,
    source_chat_id: int,
    source_message_id: int,
    recipient_ids: list[int],
    t: Translator,
) -> None:
    """Deliver the prepared broadcast to every recipient.

    The broadcast is rate-limited to _BROADCAST_MAX_PER_SECOND messages/sec.
    The timestamp of the previous send is tracked so the minimum interval
    is respected regardless of how long the Telegram API call takes.
    """
    total = len(recipient_ids)
    success = 0
    failed = 0
    loop = asyncio.get_event_loop()
    last_sent_at: float | None = None

    for i, user_id in enumerate(recipient_ids, start=1):
        if last_sent_at is not None:
            elapsed = loop.time() - last_sent_at
            remaining = _BROADCAST_MIN_INTERVAL - elapsed
            if remaining > 0:
                await asyncio.sleep(remaining)

        last_sent_at = loop.time()
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=source_chat_id,
                message_id=source_message_id,
                reply_markup=reply_markup,
            )
            success += 1
        except Exception:
            logger.exception("Broadcast failed to deliver to user %s", user_id)
            failed += 1

        if i % 25 == 0 or i == total:
            with contextlib.suppress(Exception):
                await progress_message.edit_text(
                    t("ADMIN_BROADCAST_PROGRESS").format(sent=i, total=total)
                )

    await progress_message.edit_text(
        t("ADMIN_BROADCAST_DONE").format(total=total, success=success, failed=failed),
        reply_markup=keyboards.back(t, callback_data="admin:panel"),
    )


# ── Providers ─────────────────────────────────────────────────────────────────
# Full CRUD for provider accounts: list, create, inspect, rename, change URL,
# and delete. Providers are identified by their stable `provider_hash` in
# callback_data because it has a fixed, callback-data-safe length.


def _extract_hash(call: CallbackQuery, prefix: str) -> str | None:
    """Extract the provider_hash suffix from a `{prefix}{hash}` callback."""
    if not call.data or not call.data.startswith(prefix):
        return None
    provider_hash = call.data[len(prefix) :]
    return provider_hash or None


async def _render_provider_details(message: Message, provider_hash: str, t: Translator) -> None:
    provider = await v2hub_client.get_provider_by_hash(provider_hash)

    if provider is None:
        await message.edit_text(
            t("ADMIN_PROVIDER_NOT_FOUND"),
            reply_markup=keyboards.back(t, callback_data="admin:providers"),
        )
        return

    await message.edit_text(
        t("ADMIN_PROVIDER_DETAILS").format(
            provider_name=provider.provider_name,
            provider_hash=provider.provider_hash,
            owner_hash=provider.owner_hash,
            provider_url=provider.provider_url or "—",
            api_token=provider.api_token,
        ),
        reply_markup=keyboards.admin_provider_details(provider.provider_hash, t),
    )


@router.callback_query(F.data == "admin:providers")
async def admin_providers(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    all_providers = await v2hub_client.get_all_providers()

    if call.message and isinstance(call.message, Message):
        if not all_providers.provider_hashes:
            await call.message.edit_text(
                t("ADMIN_PROVIDERS_LIST_EMPTY"),
                reply_markup=keyboards.admin_providers_list({}, t),
            )
        else:
            await call.message.edit_text(
                t("ADMIN_PROVIDERS_LIST_TITLE").format(count=len(all_providers.provider_hashes)),
                reply_markup=keyboards.admin_providers_list(all_providers.provider_hashes, t),
            )
    await call.answer()


@router.callback_query(F.data.startswith("admin:provider:view:"))
async def admin_provider_view(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    provider_hash = _extract_hash(call, "admin:provider:view:")
    if provider_hash is None or not call.message or not isinstance(call.message, Message):
        await call.answer()
        return

    await _render_provider_details(call.message, provider_hash, t)
    await call.answer()


# ── Provider creation: owner_id → name → URL ─────────────────────────────────


@router.callback_query(F.data == "admin:provider:create")
async def admin_provider_create_start(call: CallbackQuery, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t("ADMIN_PROVIDER_CREATE_PROMPT_OWNER"),
            reply_markup=keyboards.back(t, callback_data="admin:providers"),
        )
    await state.set_state(AdminStates.waiting_provider_create_owner_id)
    await call.answer()


@router.message(AdminStates.waiting_provider_create_owner_id)
async def admin_provider_create_receive_owner(message: Message, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    raw = (message.text or "").strip()

    if not raw.lstrip("-").isdigit():
        await message.answer(
            t("ADMIN_USERS_INVALID_ID"),
            reply_markup=keyboards.back(t, callback_data="admin:providers"),
        )
        return

    await state.update_data(provider_owner_id=int(raw))
    await state.set_state(AdminStates.waiting_provider_create_name)
    await message.answer(
        t("ADMIN_PROVIDER_CREATE_PROMPT_NAME"),
        reply_markup=keyboards.back(t, callback_data="admin:providers"),
    )


@router.message(AdminStates.waiting_provider_create_name)
async def admin_provider_create_receive_name(message: Message, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    provider_name = (message.text or "").strip()

    if not provider_name:
        await message.answer(
            t("ADMIN_PROVIDER_CREATE_NAME_INVALID"),
            reply_markup=keyboards.back(t, callback_data="admin:providers"),
        )
        return

    await state.update_data(provider_name=provider_name)
    await state.set_state(AdminStates.waiting_provider_create_url)
    await message.answer(
        t("ADMIN_PROVIDER_CREATE_PROMPT_URL"),
        reply_markup=keyboards.admin_provider_create_url(t),
    )


@router.callback_query(
    AdminStates.waiting_provider_create_url, F.data == "admin:provider:create:url:skip"
)
async def admin_provider_create_skip_url(call: CallbackQuery, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    target = call.message if isinstance(call.message, Message) else None
    await _finish_provider_create(target, state, provider_url=None, t=t)
    await call.answer()


@router.message(AdminStates.waiting_provider_create_url)
async def admin_provider_create_receive_url(message: Message, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    provider_url = (message.text or "").strip() or None
    await _finish_provider_create(message, state, provider_url=provider_url, t=t)


async def _finish_provider_create(
    target: Message | None,
    state: FSMContext,
    *,
    provider_url: str | None,
    t: Translator,
) -> None:
    data = await state.get_data()
    owner_id: int | None = data.get("provider_owner_id")
    provider_name: str | None = data.get("provider_name")
    await state.clear()

    if target is None or not isinstance(target, Message) or owner_id is None or not provider_name:
        return

    try:
        provider = await v2hub_client.create_provider(
            owner_user_id=owner_id,
            provider_name=provider_name,
            provider_url=provider_url,
        )
    except v2hubError as exc:
        text = (
            t("ADMIN_PROVIDER_CREATE_CONFLICT").format(provider_name=provider_name)
            if "already exists" in str(exc).lower() or "conflict" in str(exc).lower()
            else t("ADMIN_PROVIDER_CREATE_ERROR").format(error=exc)
        )
        await target.answer(text, reply_markup=keyboards.back(t, callback_data="admin:providers"))
        return

    await target.answer(
        t("ADMIN_PROVIDER_CREATED").format(
            provider_name=provider.provider_name,
            owner_id=owner_id,
            api_token=provider.api_token,
        ),
        reply_markup=keyboards.admin_provider_details(provider.provider_hash, t),
    )


# ── Provider renaming ─────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin:provider:rename:"))
async def admin_provider_rename_start(call: CallbackQuery, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    provider_hash = _extract_hash(call, "admin:provider:rename:")
    if provider_hash is None or not call.message or not isinstance(call.message, Message):
        await call.answer()
        return

    provider = await v2hub_client.get_provider_by_hash(provider_hash)
    if provider is None:
        await call.message.edit_text(
            t("ADMIN_PROVIDER_NOT_FOUND"),
            reply_markup=keyboards.back(t, callback_data="admin:providers"),
        )
        await call.answer()
        return

    await state.update_data(provider_hash=provider_hash)
    await state.set_state(AdminStates.waiting_provider_rename)
    await call.message.edit_text(
        t("ADMIN_PROVIDER_RENAME_PROMPT").format(provider_name=provider.provider_name),
        reply_markup=keyboards.back(t, callback_data=f"admin:provider:view:{provider_hash}"),
    )
    await call.answer()


@router.message(AdminStates.waiting_provider_rename)
async def admin_provider_rename_receive(message: Message, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    data = await state.get_data()
    provider_hash: str | None = data.get("provider_hash")
    new_name = (message.text or "").strip()
    await state.clear()

    if not provider_hash:
        return

    if not new_name:
        await message.answer(
            t("ADMIN_PROVIDER_CREATE_NAME_INVALID"),
            reply_markup=keyboards.back(t, callback_data=f"admin:provider:view:{provider_hash}"),
        )
        return

    try:
        await v2hub_client.update_provider_name(provider_hash, new_name)
    except v2hubError as exc:
        text = (
            t("ADMIN_PROVIDER_RENAME_CONFLICT").format(provider_name=new_name)
            if "already" in str(exc).lower() or "conflict" in str(exc).lower()
            else t("ADMIN_PROVIDER_UPDATE_ERROR").format(error=exc)
        )
        await message.answer(
            text,
            reply_markup=keyboards.back(t, callback_data=f"admin:provider:view:{provider_hash}"),
        )
        return

    await message.answer(t("ADMIN_PROVIDER_RENAMED").format(provider_name=new_name))
    provider = await v2hub_client.get_provider_by_hash(provider_hash)
    if provider is not None:
        await message.answer(
            t("ADMIN_PROVIDER_DETAILS").format(
                provider_name=provider.provider_name,
                provider_hash=provider.provider_hash,
                owner_hash=provider.owner_hash,
                provider_url=provider.provider_url or "—",
                api_token=provider.api_token,
            ),
            reply_markup=keyboards.admin_provider_details(provider.provider_hash, t),
        )


# ── Provider URL ──────────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin:provider:seturl:"))
async def admin_provider_set_url_start(call: CallbackQuery, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    provider_hash = _extract_hash(call, "admin:provider:seturl:")
    if provider_hash is None or not call.message or not isinstance(call.message, Message):
        await call.answer()
        return

    provider = await v2hub_client.get_provider_by_hash(provider_hash)
    if provider is None:
        await call.message.edit_text(
            t("ADMIN_PROVIDER_NOT_FOUND"),
            reply_markup=keyboards.back(t, callback_data="admin:providers"),
        )
        await call.answer()
        return

    await state.update_data(provider_hash=provider_hash)
    await state.set_state(AdminStates.waiting_provider_new_url)
    await call.message.edit_text(
        t("ADMIN_PROVIDER_SET_URL_PROMPT").format(provider_name=provider.provider_name),
        reply_markup=keyboards.admin_provider_set_url_prompt(provider_hash, t),
    )
    await call.answer()


@router.callback_query(
    AdminStates.waiting_provider_new_url, F.data.startswith("admin:provider:clearurl:")
)
async def admin_provider_clear_url(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    provider_hash = _extract_hash(call, "admin:provider:clearurl:")
    if provider_hash is None or not call.message or not isinstance(call.message, Message):
        await call.answer()
        return

    await _apply_provider_url(call.message, provider_hash, provider_url=None, t=t)
    await call.answer()


@router.message(AdminStates.waiting_provider_new_url)
async def admin_provider_set_url_receive(message: Message, state: FSMContext) -> None:
    user, t = await get_user_info_and_translator(message)
    if not user:
        return

    data = await state.get_data()
    provider_hash: str | None = data.get("provider_hash")
    await state.clear()

    if not provider_hash:
        return

    provider_url = (message.text or "").strip() or None
    await _apply_provider_url(message, provider_hash, provider_url=provider_url, t=t)


async def _apply_provider_url(
    target: Message,
    provider_hash: str,
    *,
    provider_url: str | None,
    t: Translator,
) -> None:
    try:
        await v2hub_client.update_provider_url(provider_hash, provider_url)
    except v2hubError as exc:
        await target.answer(
            t("ADMIN_PROVIDER_UPDATE_ERROR").format(error=exc),
            reply_markup=keyboards.back(t, callback_data=f"admin:provider:view:{provider_hash}"),
        )
        return

    await target.answer(t("ADMIN_PROVIDER_URL_UPDATED"))
    provider = await v2hub_client.get_provider_by_hash(provider_hash)
    if provider is not None:
        await target.answer(
            t("ADMIN_PROVIDER_DETAILS").format(
                provider_name=provider.provider_name,
                provider_hash=provider.provider_hash,
                owner_hash=provider.owner_hash,
                provider_url=provider.provider_url or "—",
                api_token=provider.api_token,
            ),
            reply_markup=keyboards.admin_provider_details(provider.provider_hash, t),
        )


# ── Provider deletion ─────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin:provider:del:"))
async def admin_provider_delete_confirm(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    provider_hash = _extract_hash(call, "admin:provider:del:")
    if provider_hash is None or not call.message or not isinstance(call.message, Message):
        await call.answer()
        return

    provider = await v2hub_client.get_provider_by_hash(provider_hash)
    if provider is None:
        await call.message.edit_text(
            t("ADMIN_PROVIDER_NOT_FOUND"),
            reply_markup=keyboards.back(t, callback_data="admin:providers"),
        )
        await call.answer()
        return

    await call.message.edit_text(
        t("ADMIN_PROVIDER_DELETE_CONFIRM").format(provider_name=provider.provider_name),
        reply_markup=keyboards.admin_provider_delete_confirm(provider_hash, t),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:provider:del_ok:"))
async def admin_provider_delete_execute(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user, t = await get_user_info_and_translator(call)
    if not user:
        return

    provider_hash = _extract_hash(call, "admin:provider:del_ok:")
    if provider_hash is None or not call.message or not isinstance(call.message, Message):
        await call.answer()
        return

    provider = await v2hub_client.get_provider_by_hash(provider_hash)
    provider_name = provider.provider_name if provider else provider_hash

    try:
        await v2hub_client.delete_provider(provider_hash)
    except v2hubError as exc:
        await call.message.edit_text(
            t("ADMIN_PROVIDER_DELETE_ERROR").format(error=exc),
            reply_markup=keyboards.back(t, callback_data="admin:providers"),
        )
        await call.answer()
        return

    await call.message.edit_text(
        t("ADMIN_PROVIDER_DELETED").format(provider_name=provider_name),
        reply_markup=keyboards.back(t, callback_data="admin:providers"),
    )
    await call.answer()
