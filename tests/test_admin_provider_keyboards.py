from __future__ import annotations

import pytest
from helpers import t

from v2hub_bot.services import keyboards

pytestmark = pytest.mark.unit


def _flat_callback_data(markup: object) -> list[str]:
    buttons = [btn for row in markup.inline_keyboard for btn in row]  # type: ignore[attr-defined]
    return [btn.callback_data for btn in buttons if btn.callback_data]


def test_admin_providers_list_shows_each_provider_and_create_button() -> None:
    markup = keyboards.admin_providers_list({"vpn123": "hash1", "vpn456": "hash2"}, t)

    callbacks = _flat_callback_data(markup)
    assert "admin:provider:view:hash1" in callbacks
    assert "admin:provider:view:hash2" in callbacks
    assert "admin:provider:create" in callbacks
    assert "admin:panel" in callbacks


def test_admin_providers_list_empty_still_shows_create_and_back() -> None:
    markup = keyboards.admin_providers_list({}, t)

    callbacks = _flat_callback_data(markup)
    assert "admin:provider:create" in callbacks
    assert "admin:panel" in callbacks


def test_admin_provider_details_shows_actions_and_back() -> None:
    markup = keyboards.admin_provider_details("hash1", t)

    callbacks = _flat_callback_data(markup)
    assert "admin:provider:rename:hash1" in callbacks
    assert "admin:provider:seturl:hash1" in callbacks
    assert "admin:provider:del:hash1" in callbacks
    assert "admin:providers" in callbacks


def test_admin_provider_create_url_has_skip_and_back() -> None:
    markup = keyboards.admin_provider_create_url(t)

    callbacks = _flat_callback_data(markup)
    assert "admin:provider:create:url:skip" in callbacks
    assert "admin:providers" in callbacks


def test_admin_provider_set_url_prompt_has_clear_and_cancel_back() -> None:
    markup = keyboards.admin_provider_set_url_prompt("hash1", t)

    callbacks = _flat_callback_data(markup)
    assert "admin:provider:clearurl:hash1" in callbacks
    # Cancelling must return to the provider's own details screen, not
    # silently apply a change or dead-end the flow.
    assert "admin:provider:view:hash1" in callbacks


def test_admin_provider_delete_confirm_has_confirm_and_cancel_to_details() -> None:
    markup = keyboards.admin_provider_delete_confirm("hash1", t)

    callbacks = _flat_callback_data(markup)
    assert "admin:provider:del_ok:hash1" in callbacks
    assert "admin:provider:view:hash1" in callbacks


def test_admin_users_result_existing_shows_delete_and_providers() -> None:
    markup = keyboards.admin_users_result(user_id=42, t=t, is_exist=True)

    callbacks = _flat_callback_data(markup)
    assert "admin:users:del:42" in callbacks
    assert "admin:users:providers:42" in callbacks
    assert "admin:panel" in callbacks


def test_admin_users_result_missing_shows_create_only() -> None:
    markup = keyboards.admin_users_result(user_id=42, t=t, is_exist=False)

    callbacks = _flat_callback_data(markup)
    assert "admin:users:create:42" in callbacks
    assert "admin:users:del:42" not in callbacks
    assert "admin:panel" in callbacks


def test_admin_user_delete_confirm_has_confirm_and_cancel_to_view() -> None:
    markup = keyboards.admin_user_delete_confirm(42, t)

    callbacks = _flat_callback_data(markup)
    assert "admin:users:del_ok:42" in callbacks
    assert "admin:users:view:42" in callbacks
