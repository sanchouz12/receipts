from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import config

engine = create_async_engine(
    config.database_url, echo=config.ENVIRONMENT == "dev", pool_size=10, max_overflow=20, pool_pre_ping=True
)
session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session() as db:
        yield db
