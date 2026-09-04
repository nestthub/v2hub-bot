import re
from dataclasses import dataclass, field
from typing import Literal, cast, get_args

Style = Literal["success", "primary", "danger"]
_STYLE_VALUES = get_args(Style)
_MAX_CALLBACK_DATA_LENGTH = 64


@dataclass
class KeyboardData:
    text: str
    callback_data: str | None = field(
        default=None, metadata={"max_length": _MAX_CALLBACK_DATA_LENGTH}
    )
    url: str | None = None
    style: Style | None = None
    emoji_id: str | None = None


_ATTRS_RE = re.compile(r"\[([^\]]*)\]\s*$")

_URL_PREFIXES = (
    "https://",
    "http://",
    "t.me/",
    "tg://",
)

_EMOJI_RE = re.compile(r'<tg-emoji emoji-id="(\d+)">.*?</tg-emoji>')


def _normalize_emojis(text: str) -> str:
    return _EMOJI_RE.sub(r"\1", text)


def parse_keyboard(block: str | None) -> list[list[KeyboardData]]:
    keyboard: list[list[KeyboardData]] = []

    if block is None:
        return keyboard

    block = _normalize_emojis(block)

    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue

        row = []

        for button in re.split(r"\s*\|\s*", line):
            button = button.strip()
            if not button:
                continue

            parsed_button = _parse_button(button)
            if parsed_button is not None:
                row.append(parsed_button)

        if row:
            keyboard.append(row)

    return keyboard


def _parse_button(button: str) -> KeyboardData | None:
    # Убираем блок атрибутов в конце:
    # [style=primary emoji=1234567890]
    attrs_match = _ATTRS_RE.search(button)

    if attrs_match:
        attrs = attrs_match.group(1)
        button = button[: attrs_match.start()].rstrip()
    else:
        attrs = ""

    style: Style | None = None
    emoji_id: str | None = None

    # Парсим атрибуты.
    for attr in attrs.split():
        key, separator, value = attr.partition("=")
        if not separator:
            continue

        key = key.strip()
        value = value.strip()

        if key == "style" and value in _STYLE_VALUES:
            style = cast("Style", value)
        elif key == "emoji" and value:
            emoji_id = value

    # Формат:
    # text - target
    try:
        text, target = button.rsplit(" - ", 1)  # Разделяем только по последнему " - "
    except ValueError as exc:
        raise ValueError(
            f"Invalid keyboard button: {button!r}. Expected format: 'text - target [attributes]'"
        ) from exc

    text = text.strip()
    target = target.strip()

    # URL определяется исключительно по префиксу target.
    if target.startswith(_URL_PREFIXES):
        return KeyboardData(
            text=text,
            url=target,
            style=style,
            emoji_id=emoji_id,
        )

    if len(target) <= _MAX_CALLBACK_DATA_LENGTH:
        return KeyboardData(
            text=text,
            callback_data=target,
            style=style,
            emoji_id=emoji_id,
        )

    return None
