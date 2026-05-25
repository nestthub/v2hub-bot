from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Telegram
    BOT_TOKEN: str
    MINIAPP_URL: str
    SUPPORT_URL: str

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "v2hub"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    # v2hub Admin API (v2hub-admin library)
    V2HUB_API_URL: str
    V2HUB_SECRET_KEY: str  # HMAC-SHA256 secret

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
