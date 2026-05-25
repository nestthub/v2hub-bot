from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User


# ── Users ─────────────────────────────────────────────────────────────────────

async def get_or_create_user(session: AsyncSession, user_id: int) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=user_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def save_token(session: AsyncSession, user_id: int, token: str) -> None:
    user = await get_user(session, user_id)
    if user:
        user.api_token = token
        user.token_generated_at = datetime.now(timezone.utc)
        await session.commit()
