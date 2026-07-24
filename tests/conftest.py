from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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

from v2hub_bot.db.models import Base, User


@pytest.fixture
def sample_user_id() -> int:
    return 42


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Isolated in-memory SQLite session, fresh schema per test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def existing_user(db_session: AsyncSession, sample_user_id: int) -> User:
    """A user row that already has a token, pre-inserted into db_session."""
    user = User(
        id=sample_user_id,
        api_token="existing-token-abc",
        token_generated_at=datetime.now(UTC),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
