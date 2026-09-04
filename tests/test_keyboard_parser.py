import pytest

from v2hub_bot.utils.keyboard_parser import KeyboardData, parse_keyboard


def test_parse_none():
    assert parse_keyboard(None) == []


def test_parse_empty_string():
    assert parse_keyboard("") == []


def test_parse_whitespace():
    assert parse_keyboard("   \n  \n   ") == []


def test_parse_callback_button():
    result = parse_keyboard("Кнопка - callback")

    assert result == [
        [
            KeyboardData(
                text="Кнопка",
                callback_data="callback",
            )
        ]
    ]


def test_parse_url_button():
    result = parse_keyboard("Сайт - https://example.com")

    assert result == [
        [
            KeyboardData(
                text="Сайт",
                url="https://example.com",
            )
        ]
    ]


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "https://v2hub.link/test",
        "t.me/example",
        "t.me/example?start=123",
        "tg://user?id=123",
    ],
)
def test_parse_url_prefixes(url):
    result = parse_keyboard(f"Ссылка - {url}")

    assert result[0][0].url == url
    assert result[0][0].callback_data is None


@pytest.mark.parametrize("style", ["success", "primary", "danger"])
def test_parse_style(style):
    result = parse_keyboard(f"Кнопка - callback [style={style}]")

    assert result[0][0].style == style


def test_parse_invalid_style():
    result = parse_keyboard("Кнопка - callback [style=unknown]")

    assert result[0][0].style is None


def test_parse_emoji():
    result = parse_keyboard("Кнопка - callback [emoji=1234567890]")

    assert result[0][0].emoji_id == "1234567890"


def test_parse_telegram_emoji():
    result = parse_keyboard(
        'Кнопка - action [emoji=<tg-emoji emoji-id="5875465628285931233">✈️</tg-emoji>]'
    )

    assert result[0][0] == KeyboardData(
        text="Кнопка",
        callback_data="action",
        emoji_id="5875465628285931233",
    )


def test_parse_telegram_emoji_with_style():
    result = parse_keyboard(
        'Кнопка - action [emoji=<tg-emoji emoji-id="5875465628285931233">✈️</tg-emoji> style=primary]'
    )

    assert result[0][0] == KeyboardData(
        text="Кнопка",
        callback_data="action",
        style="primary",
        emoji_id="5875465628285931233",
    )


def test_parse_telegram_emoji_before_style():
    result = parse_keyboard(
        'Кнопка - action [style=primary emoji=<tg-emoji emoji-id="5875465628285931233">✈️</tg-emoji>]'
    )

    assert result[0][0] == KeyboardData(
        text="Кнопка",
        callback_data="action",
        style="primary",
        emoji_id="5875465628285931233",
    )


def test_parse_multiple_telegram_emojis():
    result = parse_keyboard(
        'Кнопка - action [emoji=<tg-emoji emoji-id="123">✈️</tg-emoji>] | '
        'Вторая - test [emoji=<tg-emoji emoji-id="456">❤️</tg-emoji>]'
    )

    assert result == [
        [
            KeyboardData(
                text="Кнопка",
                callback_data="action",
                emoji_id="123",
            ),
            KeyboardData(
                text="Вторая",
                callback_data="test",
                emoji_id="456",
            ),
        ]
    ]


def test_parse_style_and_emoji():
    result = parse_keyboard("Кнопка - callback [style=primary emoji=1234567890]")

    assert result[0][0] == KeyboardData(
        text="Кнопка",
        callback_data="callback",
        style="primary",
        emoji_id="1234567890",
    )


def test_parse_empty_attributes():
    result = parse_keyboard("Кнопка - action []")

    assert result[0][0] == KeyboardData(
        text="Кнопка",
        callback_data="action",
    )


def test_parse_empty_attribute_values():
    result = parse_keyboard("Кнопка - action [style= emoji=]")

    assert result[0][0] == KeyboardData(
        text="Кнопка",
        callback_data="action",
    )


def test_parse_unknown_attributes():
    result = parse_keyboard("Кнопка - action [foo=bar style=primary]")

    assert result[0][0] == KeyboardData(
        text="Кнопка",
        callback_data="action",
        style="primary",
    )


def test_parse_multiple_buttons():
    result = parse_keyboard("Кнопка 1 - callback1 | Кнопка 2 - callback2")

    assert result == [
        [
            KeyboardData(text="Кнопка 1", callback_data="callback1"),
            KeyboardData(text="Кнопка 2", callback_data="callback2"),
        ]
    ]


def test_parse_multiple_rows():
    result = parse_keyboard(
        """
        Кнопка 1 - callback1 | Кнопка 2 - callback2
        Кнопка 3 - callback3
        """
    )

    assert result == [
        [
            KeyboardData(text="Кнопка 1", callback_data="callback1"),
            KeyboardData(text="Кнопка 2", callback_data="callback2"),
        ],
        [
            KeyboardData(text="Кнопка 3", callback_data="callback3"),
        ],
    ]


def test_parse_mixed_rows():
    result = parse_keyboard(
        """
        Каталог - catalog | Сайт - https://v2hub.link
        Самолёт - action [emoji=<tg-emoji emoji-id="123">✈️</tg-emoji> style=primary]
        """
    )

    assert result == [
        [
            KeyboardData(
                text="Каталог",
                callback_data="catalog",
            ),
            KeyboardData(
                text="Сайт",
                url="https://v2hub.link",
            ),
        ],
        [
            KeyboardData(
                text="Самолёт",
                callback_data="action",
                style="primary",
                emoji_id="123",
            ),
        ],
    ]


def test_parse_button_with_dash_in_text():
    result = parse_keyboard("Кнопка - с дефисом - callback")

    assert result[0][0] == KeyboardData(
        text="Кнопка - с дефисом",
        callback_data="callback",
    )


def test_parse_button_with_dash_in_target():
    result = parse_keyboard("Кнопка - admin-123")

    assert result[0][0] == KeyboardData(
        text="Кнопка",
        callback_data="admin-123",
    )


def test_parse_url_with_dash_in_target():
    result = parse_keyboard("Кнопка - https://v2hub.link/test-path")

    assert result[0][0] == KeyboardData(
        text="Кнопка",
        url="https://v2hub.link/test-path",
    )


def test_parse_attributes_are_only_at_the_end():
    result = parse_keyboard("Кнопка [style=primary] - callback")

    assert result[0][0] == KeyboardData(
        text="Кнопка [style=primary]",
        callback_data="callback",
    )


def test_parse_attributes_with_trailing_spaces():
    result = parse_keyboard("Кнопка - callback [style=primary emoji=123]   ")

    assert result[0][0] == KeyboardData(
        text="Кнопка",
        callback_data="callback",
        style="primary",
        emoji_id="123",
    )


def test_parse_empty_buttons():
    result = parse_keyboard("Кнопка 1 - callback1 | | Кнопка 2 - callback2")

    assert result == [
        [
            KeyboardData(text="Кнопка 1", callback_data="callback1"),
            KeyboardData(text="Кнопка 2", callback_data="callback2"),
        ]
    ]


def test_parse_blank_lines_between_rows():
    result = parse_keyboard(
        """
        Кнопка 1 - callback1

        Кнопка 2 - callback2

        """
    )

    assert result == [
        [
            KeyboardData(text="Кнопка 1", callback_data="callback1"),
        ],
        [
            KeyboardData(text="Кнопка 2", callback_data="callback2"),
        ],
    ]


def test_invalid_button_format():
    with pytest.raises(ValueError, match="Invalid keyboard button"):
        parse_keyboard("Кнопка без target")


@pytest.mark.parametrize(
    "button",
    [
        "Кнопка",
        "Кнопка callback",
        "Кнопка -",
        "Кнопка- callback",
    ],
)
def test_invalid_button_formats(button):
    with pytest.raises(ValueError, match="Invalid keyboard button"):
        parse_keyboard(button)


def test_parse_complete_example():
    result = parse_keyboard(
        'Кнопка - action [emoji=<tg-emoji emoji-id="5875465628285931233">✈️</tg-emoji>] | '
        "Кнопка -30 - https://v2hub.link\n"
        "Кнопка - action [] | "
        "Кнопка - action [emoji=5850317551090800862 style=primary]"
    )

    assert result == [
        [
            KeyboardData(
                text="Кнопка",
                callback_data="action",
                emoji_id="5875465628285931233",
            ),
            KeyboardData(
                text="Кнопка -30",
                url="https://v2hub.link",
            ),
        ],
        [
            KeyboardData(
                text="Кнопка",
                callback_data="action",
            ),
            KeyboardData(
                text="Кнопка",
                callback_data="action",
                emoji_id="5850317551090800862",
                style="primary",
            ),
        ],
    ]
