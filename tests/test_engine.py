from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from v2hub_bot.db.engine import get_session
from v2hub_bot.db.models import Base, User

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_init_db_creates_users_table_only() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    import v2hub_bot.db.engine as engine_module

    original_engine = engine_module.engine
    original_session = engine_module.async_session
    engine_module.engine = engine
    engine_module.async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with engine_module.async_session() as session:
            session.add(User(id=1))
            await session.commit()

        async with engine.connect() as conn:
            tables = await conn.run_sync(lambda _: Base.metadata.tables.keys())
        assert set(tables) == {"users"}
    finally:
        engine_module.engine = original_engine
        engine_module.async_session = original_session
        await engine.dispose()


@pytest.mark.asyncio
async def test_get_session_yields_an_async_session() -> None:
    generator = get_session()
    session = await generator.__anext__()

    try:
        assert isinstance(session, AsyncSession)
    finally:
        await generator.aclose()
