from __future__ import annotations

import pytest

from v2hub_bot.handlers.start import parse_deep_link_payload

pytestmark = pytest.mark.unit


def test_parse_none_payload_returns_none() -> None:
    assert parse_deep_link_payload(None) is None


def test_parse_empty_payload_returns_none() -> None:
    assert parse_deep_link_payload("") is None


def test_parse_unrelated_payload_returns_none() -> None:
    assert parse_deep_link_payload("something_else") is None


def test_parse_provider_payload() -> None:
    result = parse_deep_link_payload("provider_vpn123")

    assert result == ("provider", "vpn123", None)


def test_parse_provider_payload_with_empty_name_returns_none() -> None:
    assert parse_deep_link_payload("provider_") is None


def test_parse_conn_payload() -> None:
    result = parse_deep_link_payload("conn_abc123hmac_vpn123")

    assert result == ("conn", "vpn123", "abc123hmac")


def test_parse_conn_payload_with_underscore_in_provider_name() -> None:
    """Provider name may itself contain underscores; only the hmac is split off first."""
    result = parse_deep_link_payload("conn_abc123hmac_vpn_provider_name")

    assert result == ("conn", "vpn_provider_name", "abc123hmac")


def test_parse_conn_payload_missing_provider_name_returns_none() -> None:
    assert parse_deep_link_payload("conn_abc123hmac") is None


def test_parse_conn_payload_missing_hmac_returns_none() -> None:
    assert parse_deep_link_payload("conn_") is None


def test_parse_conn_payload_empty_hmac_returns_none() -> None:
    assert parse_deep_link_payload("conn__vpn123") is None
