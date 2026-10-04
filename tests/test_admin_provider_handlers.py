from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from helpers import ADMIN_ID, make_callback, make_message, make_provider, make_state, t, tg_user

from v2hub_admin.models import AllProvidersResponse
from v2hub_bot.handlers import admin
from v2hub_bot.handlers.admin_states import AdminStates
from v2hub_bot.services import v2hubError

pytestmark = pytest.mark.unit


# ── Список провайдеров ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_providers_lists_all_providers() -> None:
    user = tg_user(ADMIN_ID)
    call = make_callback(user, "admin:providers")
    state = make_state()

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
    user = tg_user(ADMIN_ID)
    call = make_callback(user, "admin:providers")
    state = make_state()

    with patch.object(
        admin.v2hub_client,
        "get_all_providers",
        AsyncMock(return_value=AllProvidersResponse(provider_hashes={})),
    ):
        await admin.admin_providers(call, state)

    text, _kwargs = call.message.edit_text.await_args
    assert text[0] == t("ADMIN_PROVIDERS_LIST_EMPTY")


# ── Просмотр деталей ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_provider_view_shows_details() -> None:
    user = tg_user(ADMIN_ID)
    call = make_callback(user, "admin:provider:view:hash1")
    state = make_state()

    with patch.object(
        admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=make_provider())
    ):
        await admin.admin_provider_view(call, state)

    text, _kwargs = call.message.edit_text.await_args
    assert "vpn123" in text[0]
    state.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_provider_view_not_found() -> None:
    user = tg_user(ADMIN_ID)
    call = make_callback(user, "admin:provider:view:missing")
    state = make_state()

    with patch.object(admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=None)):
        await admin.admin_provider_view(call, state)

    text, _kwargs = call.message.edit_text.await_args
    assert text[0] == t("ADMIN_PROVIDER_NOT_FOUND")


# ── Создание провайдера ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_provider_create_start_prompts_for_owner() -> None:
    user = tg_user(ADMIN_ID)
    call = make_callback(user, "admin:provider:create")
    state = make_state()

    await admin.admin_provider_create_start(call, state)

    call.message.edit_text.assert_awaited_once()
    state.set_state.assert_awaited_once_with(AdminStates.waiting_provider_create_owner_id)


@pytest.mark.asyncio
async def test_admin_provider_create_receive_owner_rejects_non_numeric() -> None:
    message = make_message(tg_user(ADMIN_ID), text="not-a-number")
    state = make_state()

    await admin.admin_provider_create_receive_owner(message, state)

    message.answer.assert_awaited_once()
    state.update_data.assert_not_called()


@pytest.mark.asyncio
async def test_admin_provider_create_receive_owner_stores_id_and_advances() -> None:
    message = make_message(tg_user(ADMIN_ID), text="12345")
    state = make_state()

    await admin.admin_provider_create_receive_owner(message, state)

    state.update_data.assert_awaited_once_with(provider_owner_id=12345)
    state.set_state.assert_awaited_once_with(AdminStates.waiting_provider_create_name)


@pytest.mark.asyncio
async def test_admin_provider_create_receive_name_rejects_empty() -> None:
    message = make_message(tg_user(ADMIN_ID), text="   ")
    state = make_state()

    await admin.admin_provider_create_receive_name(message, state)

    message.answer.assert_awaited_once()
    text, _kwargs = message.answer.await_args
    assert text[0] == t("ADMIN_PROVIDER_CREATE_NAME_INVALID")


@pytest.mark.asyncio
async def test_admin_provider_create_receive_name_advances_to_url_step() -> None:
    message = make_message(tg_user(ADMIN_ID), text="vpn123")
    state = make_state()

    await admin.admin_provider_create_receive_name(message, state)

    state.update_data.assert_awaited_once_with(provider_name="vpn123")
    state.set_state.assert_awaited_once_with(AdminStates.waiting_provider_create_url)


@pytest.mark.asyncio
async def test_admin_provider_create_skip_url_creates_provider_without_url() -> None:
    call = make_callback(tg_user(ADMIN_ID), "admin:provider:create:url:skip")
    state = make_state()
    state.get_data = AsyncMock(return_value={"provider_owner_id": 12345, "provider_name": "vpn123"})

    with patch.object(
        admin.v2hub_client, "create_provider", AsyncMock(return_value=make_provider())
    ) as create_mock:
        await admin.admin_provider_create_skip_url(call, state)

    create_mock.assert_awaited_once_with(
        owner_user_id=12345, provider_name="vpn123", provider_url=None
    )
    call.message.answer.assert_awaited_once()
    state.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_provider_create_receive_url_creates_provider_with_url() -> None:
    message = make_message(tg_user(ADMIN_ID), text="https://vpn.example.com")
    state = make_state()
    state.get_data = AsyncMock(return_value={"provider_owner_id": 12345, "provider_name": "vpn123"})

    with patch.object(
        admin.v2hub_client, "create_provider", AsyncMock(return_value=make_provider())
    ) as create_mock:
        await admin.admin_provider_create_receive_url(message, state)

    create_mock.assert_awaited_once_with(
        owner_user_id=12345,
        provider_name="vpn123",
        provider_url="https://vpn.example.com",
    )


@pytest.mark.asyncio
async def test_admin_provider_create_conflict_shows_conflict_message() -> None:
    message = make_message(tg_user(ADMIN_ID), text="https://vpn.example.com")
    state = make_state()
    state.get_data = AsyncMock(return_value={"provider_owner_id": 12345, "provider_name": "vpn123"})

    with patch.object(
        admin.v2hub_client,
        "create_provider",
        AsyncMock(side_effect=v2hubError("Provider already exists")),
    ):
        await admin.admin_provider_create_receive_url(message, state)

    message.answer.assert_awaited_once()
    text, _kwargs = message.answer.await_args
    assert text[0] == t("ADMIN_PROVIDER_CREATE_CONFLICT").format(provider_name="vpn123")


# ── Переименование ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_provider_rename_start_prompts_and_stores_hash() -> None:
    call = make_callback(tg_user(ADMIN_ID), "admin:provider:rename:hash1")
    state = make_state()

    with patch.object(
        admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=make_provider())
    ):
        await admin.admin_provider_rename_start(call, state)

    state.update_data.assert_awaited_once_with(provider_hash="hash1")
    state.set_state.assert_awaited_once_with(AdminStates.waiting_provider_rename)


@pytest.mark.asyncio
async def test_admin_provider_rename_receive_updates_name() -> None:
    message = make_message(tg_user(ADMIN_ID), text="new-name")
    state = make_state()
    state.get_data = AsyncMock(return_value={"provider_hash": "hash1"})

    with (
        patch.object(
            admin.v2hub_client, "update_provider_name", AsyncMock(return_value=None)
        ) as rename_mock,
        patch.object(
            admin.v2hub_client,
            "get_provider_by_hash",
            AsyncMock(return_value=make_provider(provider_name="new-name")),
        ),
    ):
        await admin.admin_provider_rename_receive(message, state)

    rename_mock.assert_awaited_once_with("hash1", "new-name")
    state.clear.assert_awaited_once()


# ── Удаление ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_provider_delete_confirm_shows_warning() -> None:
    call = make_callback(tg_user(ADMIN_ID), "admin:provider:del:hash1")
    state = make_state()

    with patch.object(
        admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=make_provider())
    ):
        await admin.admin_provider_delete_confirm(call, state)

    text, _kwargs = call.message.edit_text.await_args
    assert "vpn123" in text[0]


@pytest.mark.asyncio
async def test_admin_provider_delete_execute_calls_delete_and_confirms() -> None:
    call = make_callback(tg_user(ADMIN_ID), "admin:provider:del_ok:hash1")
    state = make_state()

    with (
        patch.object(
            admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=make_provider())
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
    call = make_callback(tg_user(ADMIN_ID), "admin:provider:del_ok:hash1")
    state = make_state()

    with (
        patch.object(
            admin.v2hub_client, "get_provider_by_hash", AsyncMock(return_value=make_provider())
        ),
        patch.object(
            admin.v2hub_client,
            "delete_provider",
            AsyncMock(side_effect=v2hubError("boom")),
        ),
    ):
        await admin.admin_provider_delete_execute(call, state)

    text, _kwargs = call.message.edit_text.await_args
    assert "boom" in text[0]
