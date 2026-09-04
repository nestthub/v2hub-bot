from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TgUser

from v2hub_admin.models import AllProvidersResponse, ProviderResponse
from v2hub_bot.handlers import admin
from v2hub_bot.handlers.admin_states import AdminStates
from v2hub_bot.services import V2HubError

pytestmark = pytest.mark.unit


def _tg_user(user_id: int = 7) -> MagicMock:
    user = MagicMock(spec=TgUser)
    user.id = user_id
    return user


def _message(user: MagicMock | None = None, text: str | None = None) -> MagicMock:
    message = MagicMock(spec=Message)
    message.from_user = user
    message.text = text
    message.html_text = text
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    return message


def _callback(user: MagicMock, data: str) -> MagicMock:
    call = MagicMock(spec=CallbackQuery)
    call.from_user = user
    call.data = data
    call.message = MagicMock(spec=Message)
    call.message.edit_text = AsyncMock()
    call.message.answer = AsyncMock()
    call.answer = AsyncMock()
    return call


def _state() -> MagicMock:
    state = MagicMock(spec=FSMContext)
    state.clear = AsyncMock()
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    return state


def _provider(
    *,
    provider_hash: str = "hash1",
    provider_name: str = "vpn123",
    owner_hash: str = "owner-hash",
    provider_url: str | None = "https://example.com",
    api_token: str = "token123",
    is_active: bool = True,
) -> ProviderResponse:
    return ProviderResponse(
        provider_hash=provider_hash,
        owner_hash=owner_hash,
        provider_name=provider_name,
        api_token=api_token,
        provider_url=provider_url,
        is_active=is_active,
    )


# ── Список провайдеров ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_providers_lists_all_providers() -> None:
    user = _tg_user()
    call = _callback(user, "admin:providers")
    state = _state()

    all_providers = AllProvidersResponse(provider_hashes={"vpn123": "hash1"})

    with patch.object(
        admin.v2hub_client, "get_all_providers", AsyncMock(return_value=all_providers)
    ):
        await admin.admin_providers(call, state)

    call.message.edit_text.assert_awaited_once()
    text, _kwargs = call.message.edit_text.await_args
    assert "1" in text[0]
    call.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_providers_empty_shows_empty_text() -> None:
    user = _tg_user()
    call = _callback(user, "admin:providers")
    state = _state()

    with patch.object(
        admin.v2hub_client,
        "get_all_providers",
        AsyncMock(return_value=AllProvidersResponse(provider_hashes={})),
    ):
        await admin.admin_providers(call, state)

    text, _kwargs = call.message.edit_text.await_args
    assert text[0] == admin.t.ADMIN_PROVIDERS_LIST_EMPTY


# ── Просмотр деталей ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_provider_view_shows_details() -> None:
    user = _tg_user()
    call = _callback(user, "admin:provider:view:hash1")
    state = _state()

    with patch.object(
        admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=_provider())
    ):
        await admin.admin_provider_view(call, state)

    text, _kwargs = call.message.edit_text.await_args
    assert "vpn123" in text[0]
    state.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_provider_view_not_found() -> None:
    user = _tg_user()
    call = _callback(user, "admin:provider:view:missing")
    state = _state()

    with patch.object(admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=None)):
        await admin.admin_provider_view(call, state)

    text, _kwargs = call.message.edit_text.await_args
    assert text[0] == admin.t.ADMIN_PROVIDER_NOT_FOUND


# ── Создание провайдера ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_provider_create_start_prompts_for_owner() -> None:
    user = _tg_user()
    call = _callback(user, "admin:provider:create")
    state = _state()

    await admin.admin_provider_create_start(call, state)

    call.message.edit_text.assert_awaited_once()
    state.set_state.assert_awaited_once_with(AdminStates.waiting_provider_create_owner_id)


@pytest.mark.asyncio
async def test_admin_provider_create_receive_owner_rejects_non_numeric() -> None:
    message = _message(_tg_user(), text="not-a-number")
    state = _state()

    await admin.admin_provider_create_receive_owner(message, state)

    message.answer.assert_awaited_once()
    state.update_data.assert_not_called()


@pytest.mark.asyncio
async def test_admin_provider_create_receive_owner_stores_id_and_advances() -> None:
    message = _message(_tg_user(), text="12345")
    state = _state()

    await admin.admin_provider_create_receive_owner(message, state)

    state.update_data.assert_awaited_once_with(provider_owner_id=12345)
    state.set_state.assert_awaited_once_with(AdminStates.waiting_provider_create_name)


@pytest.mark.asyncio
async def test_admin_provider_create_receive_name_rejects_empty() -> None:
    message = _message(_tg_user(), text="   ")
    state = _state()

    await admin.admin_provider_create_receive_name(message, state)

    message.answer.assert_awaited_once()
    text, _kwargs = message.answer.await_args
    assert text[0] == admin.t.ADMIN_PROVIDER_CREATE_NAME_INVALID


@pytest.mark.asyncio
async def test_admin_provider_create_receive_name_advances_to_url_step() -> None:
    message = _message(_tg_user(), text="vpn123")
    state = _state()

    await admin.admin_provider_create_receive_name(message, state)

    state.update_data.assert_awaited_once_with(provider_name="vpn123")
    state.set_state.assert_awaited_once_with(AdminStates.waiting_provider_create_url)


@pytest.mark.asyncio
async def test_admin_provider_create_skip_url_creates_provider_without_url() -> None:
    call = _callback(_tg_user(), "admin:provider:create:url:skip")
    state = _state()
    state.get_data = AsyncMock(return_value={"provider_owner_id": 12345, "provider_name": "vpn123"})

    with patch.object(
        admin.v2hub_client, "create_provider", AsyncMock(return_value=_provider())
    ) as create_mock:
        await admin.admin_provider_create_skip_url(call, state)

    create_mock.assert_awaited_once_with(
        owner_user_id=12345, provider_name="vpn123", provider_url=None
    )
    call.message.answer.assert_awaited_once()
    state.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_provider_create_receive_url_creates_provider_with_url() -> None:
    message = _message(_tg_user(), text="https://vpn.example.com")
    state = _state()
    state.get_data = AsyncMock(return_value={"provider_owner_id": 12345, "provider_name": "vpn123"})

    with patch.object(
        admin.v2hub_client, "create_provider", AsyncMock(return_value=_provider())
    ) as create_mock:
        await admin.admin_provider_create_receive_url(message, state)

    create_mock.assert_awaited_once_with(
        owner_user_id=12345,
        provider_name="vpn123",
        provider_url="https://vpn.example.com",
    )


@pytest.mark.asyncio
async def test_admin_provider_create_conflict_shows_conflict_message() -> None:
    message = _message(_tg_user(), text="https://vpn.example.com")
    state = _state()
    state.get_data = AsyncMock(return_value={"provider_owner_id": 12345, "provider_name": "vpn123"})

    with patch.object(
        admin.v2hub_client,
        "create_provider",
        AsyncMock(side_effect=V2HubError("Provider already exists")),
    ):
        await admin.admin_provider_create_receive_url(message, state)

    message.answer.assert_awaited_once()
    text, _kwargs = message.answer.await_args
    assert text[0] == admin.t.ADMIN_PROVIDER_CREATE_CONFLICT.format(provider_name="vpn123")


# ── Переименование ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_provider_rename_start_prompts_and_stores_hash() -> None:
    call = _callback(_tg_user(), "admin:provider:rename:hash1")
    state = _state()

    with patch.object(
        admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=_provider())
    ):
        await admin.admin_provider_rename_start(call, state)

    state.update_data.assert_awaited_once_with(provider_hash="hash1")
    state.set_state.assert_awaited_once_with(AdminStates.waiting_provider_rename)


@pytest.mark.asyncio
async def test_admin_provider_rename_receive_updates_name() -> None:
    message = _message(_tg_user(), text="new-name")
    state = _state()
    state.get_data = AsyncMock(return_value={"provider_hash": "hash1"})

    with (
        patch.object(
            admin.v2hub_client, "update_provider_name", AsyncMock(return_value=None)
        ) as rename_mock,
        patch.object(
            admin.v2hub_client,
            "get_provider_by_hash",
            AsyncMock(return_value=_provider(provider_name="new-name")),
        ),
    ):
        await admin.admin_provider_rename_receive(message, state)

    rename_mock.assert_awaited_once_with("hash1", "new-name")
    state.clear.assert_awaited_once()


# ── Удаление ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_provider_delete_confirm_shows_warning() -> None:
    call = _callback(_tg_user(), "admin:provider:del:hash1")
    state = _state()

    with patch.object(
        admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=_provider())
    ):
        await admin.admin_provider_delete_confirm(call, state)

    text, _kwargs = call.message.edit_text.await_args
    assert "vpn123" in text[0]


@pytest.mark.asyncio
async def test_admin_provider_delete_execute_calls_delete_and_confirms() -> None:
    call = _callback(_tg_user(), "admin:provider:del_ok:hash1")
    state = _state()

    with (
        patch.object(
            admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=_provider())
        ),
        patch.object(
            admin.v2hub_client, "delete_provider", AsyncMock(return_value=None)
        ) as delete_mock,
    ):
        await admin.admin_provider_delete_execute(call, state)

    delete_mock.assert_awaited_once_with("hash1")
    text, _kwargs = call.message.edit_text.await_args
    assert "vpn123" in text[0]


@pytest.mark.asyncio
async def test_admin_provider_delete_execute_handles_error() -> None:
    call = _callback(_tg_user(), "admin:provider:del_ok:hash1")
    state = _state()

    with (
        patch.object(
            admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=_provider())
        ),
        patch.object(
            admin.v2hub_client,
            "delete_provider",
            AsyncMock(side_effect=V2HubError("boom")),
        ),
    ):
        await admin.admin_provider_delete_execute(call, state)

    text, _kwargs = call.message.edit_text.await_args
    assert "boom" in text[0]
