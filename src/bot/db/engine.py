from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.bot.db.models import Base, SystemConfig


async def init_db(db_path: str) -> async_sessionmaker[AsyncSession]:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_async_engine(f"sqlite+aiosqlite:///{path}", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Seed SystemConfig if not exists
    async with session_factory() as session:
        result = await session.get(SystemConfig, 1)
        if result is None:
            session.add(SystemConfig(id=1, reservations_enabled=True))
            await session.commit()

    return session_factory
