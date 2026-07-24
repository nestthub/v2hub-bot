from __future__ import annotations

import pytest
from pydantic import ValidationError

from v2hub_bot.config import Settings

pytestmark = pytest.mark.unit


REQUIRED_ENV = {
    "BOT_TOKEN": "111:abc",
    "MINIAPP_URL": "https://panel.example.com",
    "SUPPORT_URL": "https://t.me/support",
    "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
    "V2HUB_API_URL": "https://v2hub.example.com",
    "V2HUB_SECRET_KEY": "secret",
}


def test_settings_load_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.bot_token == "111:abc"
    assert settings.miniapp_url == "https://panel.example.com"
    assert settings.support_url == "https://t.me/support"
    assert settings.database_url == "postgresql+asyncpg://u:p@localhost:5432/db"
    assert settings.v2hub_api_url == "https://v2hub.example.com"
    assert settings.v2hub_secret_key == "secret"


@pytest.mark.parametrize("missing_key", list(REQUIRED_ENV.keys()))
def test_settings_missing_required_field_raises(
    monkeypatch: pytest.MonkeyPatch, missing_key: str
) -> None:
    for key, value in REQUIRED_ENV.items():
        if key != missing_key:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    with pytest.raises(ValidationError):  # pydantic ValidationError
        Settings(_env_file=None)  # type: ignore[call-arg]
