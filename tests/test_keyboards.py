from __future__ import annotations

import pytest

from v2hub.models import ProviderAuthorizationStatus
from v2hub_bot.services import keyboards

pytestmark = pytest.mark.unit


def _flat_callback_data(markup: object) -> list[str]:
    buttons = [btn for row in markup.inline_keyboard for btn in row]  # type: ignore[attr-defined]
    return [btn.callback_data for btn in buttons if btn.callback_data]


def test_main_menu_without_token_shows_generate_button() -> None:
    markup = keyboards.main_menu(has_token=False)

    callbacks = _flat_callback_data(markup)
    assert "token:generate" in callbacks
    assert "token:info" not in callbacks


def test_main_menu_with_token_shows_panel_and_info_buttons() -> None:
    markup = keyboards.main_menu(has_token=True)

    callbacks = _flat_callback_data(markup)
    assert "token:info" in callbacks
    assert "token:generate" not in callbacks

    web_app_buttons = [
        btn
        for row in markup.inline_keyboard
        for btn in row
        if getattr(btn, "web_app", None) is not None
    ]
    assert len(web_app_buttons) == 1


def test_main_menu_always_has_help_and_support() -> None:
    markup = keyboards.main_menu(has_token=False)

    callbacks = _flat_callback_data(markup)
    assert "help" in callbacks
    assert "support" in callbacks


def test_token_first_time_has_webapp_and_menu_button() -> None:
    markup = keyboards.token_first_time()

    callbacks = _flat_callback_data(markup)
    assert "menu" in callbacks

    web_app_buttons = [
        btn
        for row in markup.inline_keyboard
        for btn in row
        if getattr(btn, "web_app", None) is not None
    ]
    assert len(web_app_buttons) == 1


def test_token_actions_with_token_shows_refresh() -> None:
    markup = keyboards.token_actions(has_token=True)

    callbacks = _flat_callback_data(markup)
    assert "token:refresh" in callbacks
    assert "token:generate" not in callbacks
    assert "menu" in callbacks


def test_token_actions_without_token_shows_generate() -> None:
    markup = keyboards.token_actions(has_token=False)

    callbacks = _flat_callback_data(markup)
    assert "token:generate" in callbacks
    assert "token:refresh" not in callbacks
    assert "menu" in callbacks


def test_back_to_menu_only_has_menu_button() -> None:
    markup = keyboards.back_to_menu()

    callbacks = _flat_callback_data(markup)
    assert callbacks == ["menu"]


def test_support_keyboard_has_url_and_back_button() -> None:
    markup = keyboards.support()

    url_buttons = [
        btn for row in markup.inline_keyboard for btn in row if getattr(btn, "url", None)
    ]
    callbacks = _flat_callback_data(markup)

    assert len(url_buttons) == 1
    assert "menu" in callbacks


def test_main_menu_links_to_extended_menu() -> None:
    markup = keyboards.main_menu(has_token=True)

    callbacks = _flat_callback_data(markup)
    assert "menu:extended" in callbacks


def test_extended_menu_shows_provider_buttons() -> None:
    markup = keyboards.extended_menu(has_token=True)

    callbacks = _flat_callback_data(markup)
    assert "provider:menu" in callbacks
    assert "provider:my" in callbacks


def test_provider_intro_has_support_url_and_back() -> None:
    markup = keyboards.provider_intro()

    url_buttons = [
        btn for row in markup.inline_keyboard for btn in row if getattr(btn, "url", None)
    ]
    callbacks = _flat_callback_data(markup)

    assert len(url_buttons) == 1
    assert "menu" in callbacks


def test_provider_management_has_token_and_back() -> None:
    markup = keyboards.provider_management()

    callbacks = _flat_callback_data(markup)
    assert "provider:token" in callbacks
    assert "menu" in callbacks


def test_provider_token_actions_has_refresh_and_back() -> None:
    markup = keyboards.provider_token_actions()

    callbacks = _flat_callback_data(markup)
    assert "provider:token_refresh" in callbacks
    assert "provider:menu" in callbacks


def test_provider_page_pending_shows_connect_and_reject() -> None:
    markup = keyboards.provider_page("vpn123", pending=True)

    callbacks = _flat_callback_data(markup)
    assert "provider:approve:vpn123" in callbacks
    assert "provider:reject:vpn123" in callbacks
    assert "provider:disconnect:vpn123" not in callbacks


def test_provider_page_connected_shows_disconnect_only() -> None:
    markup = keyboards.provider_page("vpn123", connected=True)

    callbacks = _flat_callback_data(markup)
    assert "provider:disconnect:vpn123" in callbacks
    assert "provider:approve:vpn123" not in callbacks
    assert "provider:reject:vpn123" not in callbacks


def test_provider_page_no_state_shows_only_back() -> None:
    markup = keyboards.provider_page("vpn123")

    callbacks = _flat_callback_data(markup)
    assert callbacks == ["menu"]


def test_my_providers_lists_each_provider_and_back() -> None:
    markup = keyboards.my_providers(
        {
            ProviderAuthorizationStatus.APPROVED: ["vpn123"],
            ProviderAuthorizationStatus.PENDING: ["vpn456"],
        }
    )

    callbacks = _flat_callback_data(markup)
    assert "provider:view:vpn123" in callbacks
    assert "provider:view:vpn456" in callbacks
    assert "menu" in callbacks
