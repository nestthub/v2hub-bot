from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from v2hub_bot.locales import i18n
from v2hub_bot.locales.compile_locales import LOCALES_DIR, compile_locales, parse_po

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

pytestmark = pytest.mark.unit


@pytest.fixture
def custom_locales(tmp_path: Path) -> Iterator[Callable[[str, str], None]]:
    """Point i18n at a temporary locales dir; `add(lang, po_source)` creates a catalog."""

    def add(lang: str, po_source: str) -> None:
        messages_dir = tmp_path / lang / "LC_MESSAGES"
        messages_dir.mkdir(parents=True)
        (messages_dir / "messages.po").write_text(po_source, encoding="utf-8")
        compile_locales(tmp_path)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(i18n, "LOCALES_DIR", tmp_path)
        patch.setattr(i18n, "SUPPORTED_LANGUAGES", frozenset({"en", "xx"}))
        i18n._translation.cache_clear()
        yield add
    # The cache must be cleared again once the real LOCALES_DIR is restored.
    i18n._translation.cache_clear()


# ── supported languages / normalisation ──────────────────────────────────────


def test_supported_languages_match_shipped_catalogs() -> None:
    assert {"en", "ru", "fa", "zh"} <= i18n.SUPPORTED_LANGUAGES
    assert i18n.DEFAULT_LANG in i18n.SUPPORTED_LANGUAGES


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (None, "en"),
        ("", "en"),
        ("en", "en"),
        ("ru", "ru"),
        ("RU", "ru"),
        ("ru-RU", "ru"),
        ("zh-hans", "zh"),
        ("zh_CN", "zh"),
        ("fa", "fa"),
        ("pt-BR", "en"),  # no catalog -> default
        ("klingon", "en"),
    ],
)
def test_normalize_lang(code: str | None, expected: str) -> None:
    assert i18n.normalize_lang(code) == expected


# ── translators ──────────────────────────────────────────────────────────────


def test_translator_returns_text_in_requested_language() -> None:
    en = i18n.get_translator("en")("WELCOME_RETURNING")
    ru = i18n.get_translator("ru")("WELCOME_RETURNING")

    assert en != "WELCOME_RETURNING"
    assert ru not in {en, "WELCOME_RETURNING"}


def test_translator_defaults_to_english_and_handles_unknown_languages() -> None:
    en = i18n.get_translator("en")("WELCOME_RETURNING")

    assert i18n.get_translator()("WELCOME_RETURNING") == en
    assert i18n.get_translator("pt-BR")("WELCOME_RETURNING") == en


def test_unknown_key_is_returned_as_is() -> None:
    assert i18n.get_translator("ru")("NO_SUCH_KEY") == "NO_SUCH_KEY"


def test_translator_is_cached() -> None:
    assert i18n._translation("ru") is i18n._translation("ru")


def test_missing_key_falls_back_to_english(custom_locales: Callable[[str, str], None]) -> None:
    custom_locales(
        "en",
        'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\nmsgid "A"\nmsgstr "english A"\n\nmsgid "B"\nmsgstr "english B"\n',
    )
    custom_locales(
        "xx",
        'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\nmsgid "A"\nmsgstr "xx A"\n',
    )

    t = i18n.get_translator("xx")

    assert t("A") == "xx A"
    assert t("B") == "english B"  # not translated in xx
    assert t("C") == "C"  # not translated anywhere


def test_missing_catalog_does_not_crash(tmp_path: Path) -> None:
    """If the .mo files were never compiled, keys are shown instead of crashing."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(i18n, "LOCALES_DIR", tmp_path)
        i18n._translation.cache_clear()
        try:
            assert i18n.get_translator("ru")("WELCOME_RETURNING") == "WELCOME_RETURNING"
        finally:
            i18n._translation.cache_clear()


# ── catalog consistency ──────────────────────────────────────────────────────


def _catalogs() -> dict[str, dict[str, str]]:
    return {
        po.parent.parent.name: parse_po(po.read_text(encoding="utf-8"))
        for po in LOCALES_DIR.glob("*/LC_MESSAGES/messages.po")
    }


def _placeholders(text: str) -> list[str]:
    return sorted(re.findall(r"\{[^{}]*\}", text))


@pytest.mark.parametrize("lang", sorted(set(_catalogs()) - {"en"}))
def test_catalog_has_same_keys_and_placeholders_as_english(lang: str) -> None:
    catalogs = _catalogs()
    english, other = catalogs["en"], catalogs[lang]

    assert set(other) == set(english), f"{lang}: keys differ from en"
    mismatched = [k for k in english if _placeholders(other[k]) != _placeholders(english[k])]
    assert not mismatched, f"{lang}: placeholders differ for {mismatched}"
