from __future__ import annotations

import pytest
from pydantic import ValidationError

from v2hub_bot.config import Settings

pytestmark = pytest.mark.unit


REQUIRED_ENV = {
    "BOT_TOKEN": "123456789:ABCdef...",
    "MINIAPP_URL": "https://your-miniapp.example.com",
    "SUPPORT_URL": "t.me/your_support",
    "DATABASE_URL": "postgresql+asyncpg://postgres:secret@db:5432/v2hub",
    "V2HUB_API_URL": "https://api.v2hub.example.com",
    "V2HUB_SECRET_KEY": "your_hmac_sha256_secret_here",
}


def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)


def test_settings_load_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)

    monkeypatch.setenv("API_URL", "https://v2hub.link")
    monkeypatch.setenv(
        "GITHUB_URL",
        "https://github.com/nestthub/nestthub/blob/main/ecosystems/v2hub/README.md",
    )

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.bot_token == "123456789:ABCdef..."
    assert settings.miniapp_url == "https://your-miniapp.example.com"
    assert settings.support_url == "t.me/your_support"
    assert settings.database_url == ("postgresql+asyncpg://postgres:secret@db:5432/v2hub")
    assert settings.api_url == "https://v2hub.link"
    assert settings.github_url == (
        "https://github.com/nestthub/nestthub/blob/main/ecosystems/v2hub/README.md"
    )
    assert settings.v2hub_api_url == "https://api.v2hub.example.com"
    assert settings.v2hub_secret_key == "your_hmac_sha256_secret_here"


def test_settings_optional_fields_default_to_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)

    monkeypatch.delenv("API_URL", raising=False)
    monkeypatch.delenv("GITHUB_URL", raising=False)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.api_url is None
    assert settings.github_url is None


def test_settings_optional_fields_are_read_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)

    monkeypatch.setenv("API_URL", "https://v2hub.link")
    monkeypatch.setenv(
        "GITHUB_URL",
        "https://github.com/nestthub/nestthub/blob/main/ecosystems/v2hub/README.md",
    )

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.api_url == "https://v2hub.link"
    assert settings.github_url == (
        "https://github.com/nestthub/nestthub/blob/main/ecosystems/v2hub/README.md"
    )


@pytest.mark.parametrize("missing_key", REQUIRED_ENV)
def test_settings_missing_required_field_raises(
    monkeypatch: pytest.MonkeyPatch,
    missing_key: str,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.delenv(missing_key, raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_settings_uses_final_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.database_url == ("postgresql+asyncpg://postgres:secret@db:5432/v2hub")


def test_settings_does_not_build_database_url_from_db_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key, value in REQUIRED_ENV.items():
        if key != "DATABASE_URL":
            monkeypatch.setenv(key, value)

    monkeypatch.delenv("DATABASE_URL", raising=False)

    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "v2hub")
    monkeypatch.setenv("DB_USER", "postgres")
    monkeypatch.setenv("DB_PASSWORD", "secret")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]
