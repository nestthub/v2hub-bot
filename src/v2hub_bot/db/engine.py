from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from v2hub_bot.config import settings
from v2hub_bot.db.models import Base

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    async with async_session() as session:
        yield session
