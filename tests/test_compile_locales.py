from __future__ import annotations

import gettext
import io
from typing import TYPE_CHECKING

import pytest

from v2hub_bot.locales import compile_locales as module
from v2hub_bot.locales.compile_locales import LOCALES_DIR, build_mo, compile_locales, parse_po

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.unit

SAMPLE_PO = r"""
# translator comment
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Plural-Forms: nplurals=2; plural=(n != 1);"

#. extracted comment
msgid "HELLO"
msgstr "Hello, <b>{name}</b>!\n"
"Second \"quoted\" line\\"

msgid "EMPTY"
msgstr ""

#, fuzzy
msgid "FUZZY"
msgstr "skipped"

msgid "UNICODE"
msgstr "Привет — 你好"

msgid "ITEM"
msgid_plural "ITEMS"
msgstr[0] "one item"
msgstr[1] "many items"
"""


def _translations(messages: dict[str, str]) -> gettext.GNUTranslations:
    return gettext.GNUTranslations(io.BytesIO(build_mo(messages)))


# ── parser ───────────────────────────────────────────────────────────────────


def test_parse_po_handles_continuations_escapes_and_skips_untranslated_and_fuzzy() -> None:
    messages = parse_po(SAMPLE_PO)

    assert messages["HELLO"] == 'Hello, <b>{name}</b>!\nSecond "quoted" line\\'
    assert messages["UNICODE"] == "Привет — 你好"
    assert "EMPTY" not in messages
    assert "FUZZY" not in messages
    assert "" in messages  # header is kept


def test_parse_po_joins_multiline_msgid_and_msgid_plural() -> None:
    messages = parse_po(
        'msgid "LONG_"\n"KEY"\nmsgid_plural "LONG_"\n"KEYS"\nmsgstr[0] "a"\nmsgstr[1] "b"\n'
    )

    assert messages == {"LONG_KEY\0LONG_KEYS": "a\0b"}


def test_parse_po_keeps_a_fuzzy_header() -> None:
    messages = parse_po('#, fuzzy\nmsgid ""\nmsgstr "Language: ru\\n"\n')

    assert messages == {"": "Language: ru\n"}


def test_parse_po_comment_between_entries_does_not_leak() -> None:
    messages = parse_po('msgid "A"\nmsgstr "1"\n# comment\nmsgid "B"\nmsgstr "2"\n')

    assert messages == {"A": "1", "B": "2"}


@pytest.mark.parametrize(
    "broken",
    [
        'msgid "A"\nmsgstr B',  # unquoted value
        "garbage line",
        '"orphan"',  # continuation outside of an entry
        'msgctxt "ctx"\nmsgid "A"\nmsgstr "1"',  # unsupported
        'msgid "A"\nmsgstr "bad \\x escape"',  # invalid escape sequence
        'msgid "A"\nmsgstr "unescaped "quote" inside"',
    ],
)
def test_parse_po_rejects_invalid_syntax(broken: str) -> None:
    with pytest.raises(ValueError, match="line"):
        parse_po(broken)


# ── binary format ────────────────────────────────────────────────────────────


def test_built_mo_is_readable_by_gettext() -> None:
    translations = _translations(parse_po(SAMPLE_PO))

    assert translations.gettext("HELLO") == 'Hello, <b>{name}</b>!\nSecond "quoted" line\\'
    assert translations.gettext("UNICODE") == "Привет — 你好"
    assert translations.gettext("MISSING") == "MISSING"
    assert translations.ngettext("ITEM", "ITEMS", 1) == "one item"
    assert translations.ngettext("ITEM", "ITEMS", 5) == "many items"
    assert translations.charset() == "UTF-8"


def test_empty_catalog_is_a_valid_mo() -> None:
    assert _translations({}).gettext("anything") == "anything"


# ── compile_locales / main ───────────────────────────────────────────────────


def test_compile_locales_writes_mo_next_to_po(tmp_path: Path) -> None:
    messages_dir = tmp_path / "xx" / "LC_MESSAGES"
    messages_dir.mkdir(parents=True)
    (messages_dir / "messages.po").write_text(SAMPLE_PO, encoding="utf-8")

    written = compile_locales(tmp_path)

    assert written == [messages_dir / "messages.mo"]
    translation = gettext.translation("messages", localedir=tmp_path, languages=["xx"])
    assert translation.gettext("UNICODE") == "Привет — 你好"


def test_compile_locales_without_po_files_returns_empty(tmp_path: Path) -> None:
    assert compile_locales(tmp_path) == []


def test_every_shipped_catalog_compiles_and_loads() -> None:
    written = compile_locales()

    assert {path.parent.parent.name for path in written} >= {"en", "ru", "fa", "zh"}
    for mo_path in written:
        with mo_path.open("rb") as fh:
            translations = gettext.GNUTranslations(fh)
        assert translations.charset() == "UTF-8"
        assert translations.gettext("WELCOME_RETURNING") != "WELCOME_RETURNING"


def test_main_reports_compiled_files(capsys: pytest.CaptureFixture[str]) -> None:
    module.main()

    out = capsys.readouterr().out
    assert "compiled en/LC_MESSAGES/messages.po" in out.replace("\\", "/") or "messages.mo" in out
    assert (LOCALES_DIR / "en" / "LC_MESSAGES" / "messages.mo").exists()


def test_main_exits_when_nothing_to_compile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "compile_locales", list)

    with pytest.raises(SystemExit, match=r"no \.po files"):
        module.main()
