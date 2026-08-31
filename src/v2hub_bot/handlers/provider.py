import html
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from v2hub.models import ProviderAuthorizationStatus
from v2hub_bot.locales import ru as t
from v2hub_bot.services import (
    ConflictError,
    NotFoundError,
    V2HubError,
    v2hub_client,
)
from v2hub_bot.services.keyboards import (
    back_to_menu,
    my_providers,
    provider_intro,
    provider_management,
    provider_page,
    provider_token_actions,
)

logger = logging.getLogger(__name__)

router = Router()


# ── Status formatting ────────────────────────────────────────────────────────

_STATUS_LABELS = {
    ProviderAuthorizationStatus.PENDING: t.PROVIDER_STATUS_PENDING,
    ProviderAuthorizationStatus.APPROVED: t.PROVIDER_STATUS_APPROVED,
    ProviderAuthorizationStatus.REVOKED: t.PROVIDER_STATUS_REVOKED,
}


def _status_label(status: ProviderAuthorizationStatus | None) -> str:
    if status is None:
        return t.PROVIDER_STATUS_NONE
    return _STATUS_LABELS.get(status, t.PROVIDER_STATUS_NONE)


def _is_pending(status: ProviderAuthorizationStatus | None) -> bool:
    return status == ProviderAuthorizationStatus.PENDING


def _is_approved(status: ProviderAuthorizationStatus | None) -> bool:
    return status == ProviderAuthorizationStatus.APPROVED


def _extract_provider_name(call: CallbackQuery) -> str | None:
    """Extract the provider name suffix from a `provider:action:name` callback."""
    if not call.data:
        return None
    parts = call.data.split(":", 2)
    if len(parts) != 3 or not parts[2]:
        return None
    return parts[2]


# ── Deep-link entry points (called from handlers/start.py) ─────────────────────


async def handle_provider_deep_link(
    message: Message,
    user_id: int,
    kind: str,
    provider_name: str,
    hmac: str | None,
) -> None:
    if kind == "provider":
        await _show_provider_page(message, user_id, provider_name)
    elif kind == "conn":
        await _process_connection_link(message, user_id, provider_name, hmac)


async def _show_provider_page(message: Message, user_id: int, provider_name: str) -> None:
    """`/start provider_{provider-name}` — show provider info + auth state.

    The deep link itself proves nothing: the actual authorization state is
    always fetched fresh from the Admin API.
    """
    auth = await v2hub_client.get_provider_authorization(provider_name, user_id)

    if auth is None:
        provider = await v2hub_client.get_provider_by_name(provider_name)
        if provider is None:
            await message.answer(
                t.PROVIDER_NOT_FOUND.format(provider_name=html.escape(provider_name))
            )
            return
        text = t.PROVIDER_PUBLIC_INFO.format(
            provider_name=html.escape(provider.provider_name),
            provider_url=html.escape(provider.provider_url or "—"),
            status=t.PROVIDER_STATUS_NONE,
        )
        await message.answer(text, reply_markup=provider_page(provider.provider_name))
        return

    text = t.PROVIDER_PUBLIC_INFO.format(
        provider_name=html.escape(auth.provider_name),
        provider_url=html.escape(auth.provider_url or "—"),
        status=_status_label(auth.status),
    )
    await message.answer(
        text,
        reply_markup=provider_page(
            auth.provider_name,
            pending=_is_pending(auth.status),
            connected=_is_approved(auth.status),
        ),
    )


async def _process_connection_link(
    message: Message,
    user_id: int,
    provider_name: str,
    hmac: str | None,
) -> None:
    """`/start conn_{hmac}_{provider-name}` — process a fresh connection invite.

    The hmac is forwarded to the Admin API unchanged; the bot never
    interprets or validates it locally.
    """
    try:
        auth = await v2hub_client.process_provider_authorization(
            user_id=user_id,
            provider_name=provider_name,
            hmac=hmac,
        )
    except V2HubError as exc:
        await message.answer(t.PROVIDER_CONNECTION_LINK_INVALID.format(error=exc))
        return

    text = t.PROVIDER_CONNECTION_REQUEST.format(
        provider_name=html.escape(auth.provider_name),
        provider_url=html.escape(auth.provider_url or "—"),
    )
    await message.answer(
        text,
        reply_markup=provider_page(
            auth.provider_name,
            pending=_is_pending(auth.status),
            connected=_is_approved(auth.status),
        ),
    )


# ── "Провайдер" section from the main menu ──────────────────────────────────────


@router.callback_query(F.data == "provider:menu")
async def cb_provider_menu(call: CallbackQuery) -> None:
    """Show the 'Провайдер' section.

    This is an additional role on top of the regular user account: a user
    without a linked provider sees the intro/how-to-apply screen; a user
    with one sees their provider's info. Either way, all regular user
    functionality (token, panel, etc.) stays available via the main menu
    regardless of provider status.

    Provider ownership itself is never cached in the bot's own database —
    it's always looked up fresh from the Admin API by the caller's
    Telegram user_id.
    """
    provider = await v2hub_client.get_provider_by_owner_id(call.from_user.id)

    if provider is None:
        if call.message and isinstance(call.message, Message):
            await call.message.edit_text(t.PROVIDER_INTRO, reply_markup=provider_intro())
        await call.answer()
        return

    status = t.PROVIDER_STATUS_ACTIVE if provider.is_active else t.PROVIDER_STATUS_INACTIVE
    text = t.PROVIDER_INFO.format(
        provider_name=html.escape(provider.provider_name),
        provider_url=html.escape(provider.provider_url or "—"),
        status=status,
    )
    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(text, reply_markup=provider_management())
    await call.answer()


# ── Provider's own token management (mirrors handlers/token.py UX) ─────────────
# The provider's token is never cached locally — it's always read fresh
# from the Admin API (ProviderResponse.api_token), independent of the
# owning user's regular API token.


@router.callback_query(F.data == "provider:token")
async def cb_provider_token(call: CallbackQuery) -> None:
    provider = await v2hub_client.get_provider_by_owner_id(call.from_user.id)

    if provider is None:
        if call.message and isinstance(call.message, Message):
            await call.message.edit_text(t.PROVIDER_NOT_FOUND_FOR_ROLE, reply_markup=back_to_menu())
        await call.answer()
        return

    text = t.PROVIDER_TOKEN_INFO.format(token=provider.api_token)
    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(text, reply_markup=provider_token_actions())
    await call.answer()


@router.callback_query(F.data == "provider:token_refresh")
async def cb_provider_token_refresh(call: CallbackQuery) -> None:
    provider = await v2hub_client.get_provider_by_owner_id(call.from_user.id)

    if provider is None:
        if call.message and isinstance(call.message, Message):
            await call.message.edit_text(t.PROVIDER_NOT_FOUND_FOR_ROLE, reply_markup=back_to_menu())
        await call.answer()
        return

    await call.answer(t.PROVIDER_TOKEN_REFRESHING)

    try:
        new_token = await v2hub_client.refresh_provider_token(provider.provider_hash)
    except V2HubError as exc:
        if call.message and isinstance(call.message, Message):
            await call.message.edit_text(
                t.PROVIDER_TOKEN_ERROR_REFRESH.format(error=exc),
                reply_markup=provider_token_actions(),
            )
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t.PROVIDER_TOKEN_REFRESHED.format(token=new_token),
            reply_markup=provider_token_actions(),
        )


# ── "Мои провайдеры" (user's own authorized providers) ─────────────────────────


@router.callback_query(F.data == "provider:my")
async def cb_my_providers(call: CallbackQuery) -> None:
    """List providers the current user has an authorization record with."""
    connections = await v2hub_client.get_user_connections(call.from_user.id)

    my_connections: dict[ProviderAuthorizationStatus, list[str]] = {}

    for connection in connections.connections:
        if connection.status and (
            _is_approved(connection.status) or _is_pending(connection.status)
        ):
            my_connections.setdefault(connection.status, []).append(connection.provider_name)

    if call.message and isinstance(call.message, Message):
        if not my_connections:
            await call.message.edit_text(
                t.MY_PROVIDERS_EMPTY,
                reply_markup=back_to_menu(),
            )
        else:
            await call.message.edit_text(
                t.MY_PROVIDERS_TITLE,
                reply_markup=my_providers(my_connections),
            )

    await call.answer()


@router.callback_query(F.data.startswith("provider:view:"))
async def cb_provider_view(call: CallbackQuery) -> None:
    provider_name = _extract_provider_name(call)
    if provider_name is None:
        await call.answer()
        return
    auth = await v2hub_client.get_provider_authorization(provider_name, call.from_user.id)

    if auth is None:
        if call.message and isinstance(call.message, Message):
            await call.message.edit_text(
                t.PROVIDER_NOT_FOUND.format(provider_name=html.escape(provider_name)),
                reply_markup=back_to_menu(),
            )
        await call.answer()
        return

    text = t.PROVIDER_PUBLIC_INFO.format(
        provider_name=html.escape(auth.provider_name),
        provider_url=html.escape(auth.provider_url or "—"),
        status=_status_label(auth.status),
    )
    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            text,
            reply_markup=provider_page(
                auth.provider_name,
                pending=_is_pending(auth.status),
                connected=_is_approved(auth.status),
            ),
        )
    await call.answer()


# ── Approve / reject / disconnect ───────────────────────────────────────────────


@router.callback_query(F.data.startswith("provider:approve:"))
async def cb_provider_approve(call: CallbackQuery) -> None:
    provider_name = _extract_provider_name(call)
    if provider_name is None:
        await call.answer()
        return
    await call.answer(t.PROVIDER_APPROVING)

    try:
        auth = await v2hub_client.approve_provider_authorization(
            user_id=call.from_user.id,
            provider_name=provider_name,
        )
    except (NotFoundError, ConflictError, V2HubError) as exc:
        if call.message and isinstance(call.message, Message):
            if "maximum allowed" in str(exc):
                await call.message.edit_text(
                    t.PROVIDER_LIMIT_ERROR,
                    reply_markup=back_to_menu(),
                )
            else:
                await call.message.edit_text(
                    t.PROVIDER_APPROVE_ERROR.format(error=exc),
                    reply_markup=back_to_menu(),
                )
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t.PROVIDER_APPROVED.format(provider_name=html.escape(auth.provider_name)),
            reply_markup=provider_page(auth.provider_name, connected=True),
        )


@router.callback_query(F.data.startswith("provider:reject:"))
async def cb_provider_reject(call: CallbackQuery) -> None:
    provider_name = _extract_provider_name(call)
    if provider_name is None:
        await call.answer()
        return
    await call.answer(t.PROVIDER_REJECTING)

    try:
        await v2hub_client.reject_provider_authorization(
            user_id=call.from_user.id,
            provider_name=provider_name,
        )
    except (NotFoundError, ConflictError, V2HubError) as exc:
        if call.message and isinstance(call.message, Message):
            await call.message.edit_text(
                t.PROVIDER_REJECT_ERROR.format(error=exc),
                reply_markup=back_to_menu(),
            )
        return

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(
            t.PROVIDER_REJECTED.format(provider_name=html.escape(provider_name)),
            reply_markup=back_to_menu(),
        )


@router.callback_query(F.data.startswith("provider:disconnect:"))
async def cb_provider_disconnect(call: CallbackQuery) -> None:
    provider_name = _extract_provider_name(call)
    if provider_name is None:
        await call.answer()
        return
    await call.answer(t.PROVIDER_DISCONNECTING)

    try:
        result = await v2hub_client.reject_provider_authorization(
            user_id=call.from_user.id,
            provider_name=provider_name,
        )
    except (NotFoundError, V2HubError) as exc:
        if call.message and isinstance(call.message, Message):
            await call.message.edit_text(
                t.PROVIDER_DISCONNECT_ERROR.format(error=exc),
                reply_markup=back_to_menu(),
            )
        return

    escaped_name = html.escape(provider_name)
    if result.status is None:
        # Server deleted the authorization: no subscriptions existed for it.
        text = t.PROVIDER_DISCONNECTED_DELETED.format(provider_name=escaped_name)
    else:
        # Server preserved it as REVOKED because subscriptions still exist.
        text = t.PROVIDER_DISCONNECTED_REVOKED.format(provider_name=escaped_name)

    if call.message and isinstance(call.message, Message):
        await call.message.edit_text(text, reply_markup=back_to_menu())
