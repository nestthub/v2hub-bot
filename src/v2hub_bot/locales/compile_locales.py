"""Compile every locales/<lang>/LC_MESSAGES/*.po into a .mo file.

The .mo files are build artifacts (git-ignored). Pure Python, no `msgfmt`
(GNU gettext) required. The Docker entrypoint runs this on every container
start, right before the bot is launched; the test suite does the same at
session start. Manual use:

    python -m v2hub_bot.locales.compile_locales
"""

import ast
import struct
import sys
from pathlib import Path

LOCALES_DIR = Path(__file__).parent

_MO_MAGIC = 0x950412DE


def parse_po(text: str) -> dict[str, str]:
    """Parse .po source into {msgid: msgstr}.

    Supports what the project uses: comments, multi-line strings, escapes and
    plural forms. Untranslated (empty msgstr) and fuzzy entries are skipped,
    like `msgfmt` does; the header entry (empty msgid) is always kept.
    """
    messages: dict[str, str] = {}
    msgid = ""
    msgid_plural: str | None = None
    msgstrs: dict[int, str] = {}
    section: str | None = None  # "id" | "plural" | "str"
    str_index = 0
    fuzzy = False
    in_entry = False

    def flush() -> None:
        nonlocal msgid, msgid_plural, msgstrs, section, fuzzy, in_entry
        if in_entry and (not fuzzy or msgid == ""):
            key = msgid if msgid_plural is None else f"{msgid}\0{msgid_plural}"
            value = "\0".join(msgstrs[i] for i in sorted(msgstrs))
            if value.replace("\0", "") or msgid == "":
                messages[key] = value
        msgid, msgid_plural, msgstrs, section, fuzzy, in_entry = "", None, {}, None, False, False

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            # A comment after a finished entry starts the next one.
            if in_entry and section == "str":
                flush()
            if line.startswith("#,") and "fuzzy" in line:
                fuzzy = True
            continue

        keyword, _, rest = line.partition(" ")
        if keyword == "msgid":
            if in_entry and section == "str":
                flush()
            in_entry, section = True, "id"
            msgid = _unquote(rest, lineno)
        elif keyword == "msgid_plural":
            section = "plural"
            msgid_plural = _unquote(rest, lineno)
        elif keyword.startswith("msgstr"):
            section = "str"
            str_index = int(keyword[7:-1]) if keyword.startswith("msgstr[") else 0
            msgstrs[str_index] = _unquote(rest, lineno)
        elif keyword.startswith('"'):  # continuation line
            piece = _unquote(line, lineno)
            if section == "id":
                msgid += piece
            elif section == "plural":
                msgid_plural = (msgid_plural or "") + piece
            elif section == "str":
                msgstrs[str_index] += piece
            else:
                raise ValueError(f"line {lineno}: string outside of an entry")
        elif keyword == "msgctxt":
            raise ValueError(f"line {lineno}: msgctxt is not supported")
        else:
            raise ValueError(f"line {lineno}: unexpected syntax: {raw!r}")
    flush()
    return messages


def _unquote(literal: str, lineno: int) -> str:
    literal = literal.strip()
    if len(literal) < 2 or literal[0] != '"' or literal[-1] != '"':
        raise ValueError(f"line {lineno}: expected a quoted string, got {literal!r}")
    try:
        return str(ast.literal_eval(literal))
    except (SyntaxError, ValueError) as exc:  # bad escape, unescaped quote, ...
        raise ValueError(f"line {lineno}: invalid string literal {literal!r}") from exc


def build_mo(messages: dict[str, str]) -> bytes:
    """Serialize a catalog into the GNU .mo binary format (UTF-8, no hash table)."""
    keys = sorted(messages, key=lambda k: k.encode("utf-8"))
    ids = [k.encode("utf-8") for k in keys]
    strs = [messages[k].encode("utf-8") for k in keys]

    count = len(keys)
    keystart = 7 * 4 + 16 * count  # header + both offset tables
    id_blob = b""
    str_blob = b""
    id_offsets: list[tuple[int, int]] = []
    str_offsets: list[tuple[int, int]] = []
    for key in ids:
        id_offsets.append((len(key), keystart + len(id_blob)))
        id_blob += key + b"\0"
    valuestart = keystart + len(id_blob)
    for value in strs:
        str_offsets.append((len(value), valuestart + len(str_blob)))
        str_blob += value + b"\0"

    tables = [n for pair in id_offsets for n in pair] + [n for pair in str_offsets for n in pair]
    header = struct.pack("<7I", _MO_MAGIC, 0, count, 7 * 4, 7 * 4 + count * 8, 0, 0)
    return header + struct.pack(f"<{len(tables)}I", *tables) + id_blob + str_blob


def compile_locales(locales_dir: Path = LOCALES_DIR) -> list[Path]:
    """Compile all .po files below `locales_dir`; return the written .mo paths."""
    written: list[Path] = []
    for po_path in sorted(locales_dir.glob("*/LC_MESSAGES/*.po")):
        mo_path = po_path.with_suffix(".mo")
        messages = parse_po(po_path.read_text(encoding="utf-8"))
        mo_path.write_bytes(build_mo(messages))
        written.append(mo_path)
    return written


def main() -> None:
    compiled = compile_locales()
    if not compiled:
        sys.exit(f"no .po files found in {LOCALES_DIR}")
    for path in compiled:
        sys.stdout.write(f"compiled {path.relative_to(LOCALES_DIR)}\n")


if __name__ == "__main__":
    main()
