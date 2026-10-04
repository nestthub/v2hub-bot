from __future__ import annotations

import pytest
from helpers import t

from v2hub.models import ProviderAuthorizationStatus
from v2hub_bot.locales import i18n
from v2hub_bot.services import keyboards

pytestmark = pytest.mark.unit


def _flat_callback_data(markup: object) -> list[str]:
    buttons = [btn for row in markup.inline_keyboard for btn in row]  # type: ignore[attr-defined]
    return [btn.callback_data for btn in buttons if btn.callback_data]


def test_main_menu_always_has_help_and_support() -> None:
    markup = keyboards.main_menu(t)

    callbacks = _flat_callback_data(markup)
    assert "help" in callbacks
    assert "support" in callbacks


def test_token_actions_with_token_shows_refresh() -> None:
    markup = keyboards.token_actions(has_token=True, t=t)

    callbacks = _flat_callback_data(markup)
    assert "token:refresh" in callbacks
    assert "token:generate" not in callbacks
    assert "menu" in callbacks


def test_token_actions_without_token_shows_generate() -> None:
    markup = keyboards.token_actions(has_token=False, t=t)

    callbacks = _flat_callback_data(markup)
    assert "token:generate" in callbacks
    assert "token:refresh" not in callbacks
    assert "menu" in callbacks


def test_back_to_menu_only_has_menu_button() -> None:
    markup = keyboards.back(t)

    callbacks = _flat_callback_data(markup)
    assert callbacks == ["menu"]


def test_support_keyboard_has_url_and_back_button() -> None:
    markup = keyboards.support(t)

    url_buttons = [
        btn for row in markup.inline_keyboard for btn in row if getattr(btn, "url", None)
    ]
    callbacks = _flat_callback_data(markup)

    assert len(url_buttons) == 1
    assert "menu" in callbacks


def test_main_menu_links_to_extended_menu() -> None:
    markup = keyboards.main_menu(t)

    callbacks = _flat_callback_data(markup)
    assert "menu:extended" in callbacks


def test_extended_menu_shows_provider_buttons() -> None:
    markup = keyboards.extended_menu(t)

    callbacks = _flat_callback_data(markup)
    assert "provider:menu" in callbacks
    assert "provider:my" in callbacks


def test_provider_intro_has_support_url_and_back() -> None:
    markup = keyboards.provider_intro(t)

    url_buttons = [
        btn for row in markup.inline_keyboard for btn in row if getattr(btn, "url", None)
    ]
    callbacks = _flat_callback_data(markup)

    assert len(url_buttons) == 1
    assert "menu" in callbacks


def test_provider_management_has_token_and_back() -> None:
    markup = keyboards.provider_management(t)

    callbacks = _flat_callback_data(markup)
    assert "provider:token" in callbacks
    assert "menu:extended" in callbacks


def test_provider_token_actions_has_refresh_and_back() -> None:
    markup = keyboards.provider_token_actions(t)

    callbacks = _flat_callback_data(markup)
    assert "provider:token_refresh" in callbacks
    assert "provider:menu" in callbacks


def test_provider_page_pending_shows_connect_and_reject() -> None:
    markup = keyboards.provider_page("vpn123", pending=True, t=t)

    callbacks = _flat_callback_data(markup)
    assert "provider:approve:vpn123" in callbacks
    assert "provider:reject:vpn123" in callbacks
    assert "provider:disconnect:vpn123" not in callbacks


def test_provider_page_connected_shows_disconnect_only() -> None:
    markup = keyboards.provider_page("vpn123", connected=True, t=t)

    callbacks = _flat_callback_data(markup)
    assert "provider:disconnect:vpn123" in callbacks
    assert "provider:approve:vpn123" not in callbacks
    assert "provider:reject:vpn123" not in callbacks


def test_provider_page_no_state_shows_only_back() -> None:
    markup = keyboards.provider_page("vpn123", t=t)

    callbacks = _flat_callback_data(markup)
    assert callbacks == ["menu"]


def test_my_providers_lists_each_provider_and_back() -> None:
    markup = keyboards.my_providers(
        {
            ProviderAuthorizationStatus.APPROVED: ["vpn123"],
            ProviderAuthorizationStatus.PENDING: ["vpn456"],
        },
        t=t,
    )

    callbacks = _flat_callback_data(markup)
    assert "provider:view:vpn123" in callbacks
    assert "provider:view:vpn456" in callbacks
    assert "menu" in callbacks


def test_main_menu_without_admin_hides_admin_panel_button() -> None:
    markup = keyboards.main_menu(t, is_admin=False)

    callbacks = _flat_callback_data(markup)
    assert "admin:panel" not in callbacks


def test_main_menu_with_admin_shows_admin_panel_button() -> None:
    markup = keyboards.main_menu(t, is_admin=True)

    callbacks = _flat_callback_data(markup)
    assert "admin:panel" in callbacks


def test_extended_menu_with_admin_shows_admin_panel_button() -> None:
    markup = keyboards.extended_menu(t, is_admin=True)

    callbacks = _flat_callback_data(markup)
    assert "admin:panel" in callbacks


def test_admin_panel_lists_all_sections_and_back() -> None:
    markup = keyboards.admin_panel(t)

    callbacks = _flat_callback_data(markup)
    assert "admin:stats" in callbacks
    assert "admin:users" in callbacks
    assert "admin:providers" in callbacks
    assert "admin:broadcast" in callbacks
    assert "menu" in callbacks


def test_stats_lists_all_periods_and_back_to_panel() -> None:
    markup = keyboards.stats(t)

    callbacks = _flat_callback_data(markup)
    assert "admin:stats:day" in callbacks
    assert "admin:stats:week" in callbacks
    assert "admin:stats:month" in callbacks
    assert "admin:stats:all" in callbacks
    assert "admin:stats:optional" in callbacks
    assert "admin:panel" in callbacks


def test_admin_broadcast_confirm_has_confirm_and_cancel() -> None:
    markup = keyboards.admin_broadcast_confirm(t)

    callbacks = _flat_callback_data(markup)
    assert "admin:broadcast:confirm" in callbacks
    assert "admin:broadcast:cancel" in callbacks


def test_back_with_custom_callback_data_shows_back_label() -> None:
    markup = keyboards.back(t, callback_data="admin:panel")

    button = markup.inline_keyboard[0][0]
    assert button.callback_data == "admin:panel"
    assert button.text == "Back"


# ── settings ─────────────────────────────────────────────────────────────────


def test_bot_settings_offers_language_and_back_to_menu() -> None:
    markup = keyboards.bot_settings(t)

    callbacks = _flat_callback_data(markup)
    assert callbacks == ["settings:language", "menu"]


def test_language_settings_offers_exactly_the_supported_languages() -> None:
    markup = keyboards.language_settings(t)

    prefix = "settings:language:"
    offered = [c.removeprefix(prefix) for c in _flat_callback_data(markup) if c.startswith(prefix)]
    assert sorted(offered) == sorted(i18n.SUPPORTED_LANGUAGES)
    assert len(offered) == len(set(offered))


def test_language_settings_goes_back_to_settings() -> None:
    markup = keyboards.language_settings(t)

    back = markup.inline_keyboard[-1][0]
    assert back.callback_data == "settings"
    assert back.text == t("BTN_BACK")
