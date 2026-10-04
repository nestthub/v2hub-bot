import gettext
from collections.abc import Callable
from functools import cache
from pathlib import Path
from typing import TypeAlias

LOCALES_DIR = Path(__file__).parent
DEFAULT_LANG = "en"
DOMAIN = "messages"

Translator: TypeAlias = Callable[[str], str]


def _discover_languages() -> frozenset[str]:
    """Return languages with compiled gettext catalogs."""
    return frozenset(
        path.parent.parent.name for path in LOCALES_DIR.glob(f"*/LC_MESSAGES/{DOMAIN}.mo")
    )


SUPPORTED_LANGUAGES: frozenset[str] = _discover_languages()


def normalize_lang(lang: str | None) -> str:
    """Map any language code to a supported one.

    Accepts Telegram's `language_code` ("ru", "pt-BR", "zh-hans", "zh_CN", None)
    and falls back to DEFAULT_LANG when there is no catalog for it.
    """
    if not lang:
        return DEFAULT_LANG

    code = lang.strip().lower().replace("_", "-")
    by_lowercase = {supported.lower(): supported for supported in SUPPORTED_LANGUAGES}
    for candidate in (code, code.split("-")[0]):
        if candidate in by_lowercase:
            return by_lowercase[candidate]
    return DEFAULT_LANG


@cache
def _translation(lang: str) -> gettext.NullTranslations:
    translation = gettext.translation(
        DOMAIN,
        localedir=str(LOCALES_DIR),
        languages=[lang],
        fallback=True,  # a missing .mo must not crash the bot; keys are shown instead
    )
    if lang != DEFAULT_LANG:
        # Keys missing in a translation fall back to English instead of a raw key.
        translation.add_fallback(_translation(DEFAULT_LANG))
    return translation


def get_translator(lang: str | None = None) -> Translator:
    return _translation(normalize_lang(lang)).gettext
