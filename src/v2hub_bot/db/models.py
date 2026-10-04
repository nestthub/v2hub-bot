from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    """Telegram user known to the bot.

    All v2hub-related information (api_token, provider link, statuses,
    etc.) lives on the server and is fetched fresh via the v2hub /
    v2hub-admin API. The bot's own database stores nothing about that —
    only the fact that this Telegram user has started the bot, and language of interface, and when.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user_id

    lang: Mapped[str] = mapped_column(
        String(16), server_default="en", nullable=False
    )  # Interface's language

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<User id={self.id}, lang={self.lang}>"
