from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# ── Environment ──────────────────────────────────────────────────────────────
# Settings() reads from the environment / .env at import time, so we set safe
# dummy values before any v2hub_bot module gets imported by a test.
os.environ.setdefault("BOT_TOKEN", "123456:test-token")
os.environ.setdefault("MINIAPP_URL", "https://panel.example.com")
os.environ.setdefault("SUPPORT_URL", "https://t.me/support_test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("V2HUB_API_URL", "https://v2hub.example.com")
os.environ.setdefault("V2HUB_SECRET_KEY", "test-secret-key")
os.environ.setdefault("BOT_ADMINS", "[7]")

from v2hub_bot.db.models import Base, User
from v2hub_bot.locales.compile_locales import compile_locales


def pytest_configure() -> None:
    """Build the git-ignored .mo files so translations work without manual steps."""
    compile_locales()


@pytest.fixture
def sample_user_id() -> int:
    return 42


@pytest.fixture
def sample_admin_id() -> int:
    """Matches the BOT_ADMINS test env var (see above)."""
    return 7


@pytest_asyncio.fixture
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Isolated in-memory SQLite database, fresh schema per test.

    The bot's own database only ever stores the fact that a Telegram
    user_id has started the bot (User.id / created_at / is_banned) — all
    v2hub account data (tokens, provider ownership, ...) lives on the
    server and is never persisted here.
    """
    # StaticPool: every connection shares the same in-memory database.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(engine, expire_on_commit=False)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


@pytest.fixture(autouse=True)
def _local_db(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Point the handlers' user lookup at the test database.

    Every handler goes through services.users.get_user_info_and_translator,
    which opens its own session — without this it would hit the real engine
    (no tables).
    """
    monkeypatch.setattr("v2hub_bot.services.users.async_session", session_factory)


@pytest_asyncio.fixture
async def existing_user(db_session: AsyncSession, sample_user_id: int) -> User:
    """A user row that already exists locally (i.e. has started the bot before)."""
    user = User(id=sample_user_id, lang="en")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
