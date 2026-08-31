from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    bot_token: str
    miniapp_url: str
    support_url: str

    api_url: str | None = None
    github_url: str | None = None

    # Database
    database_url: str

    # v2hub Admin API (v2hub-admin library)
    v2hub_api_url: str
    v2hub_secret_key: str  # HMAC-SHA256 secret


settings = Settings()
