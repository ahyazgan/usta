"""Async SQLAlchemy motoru ve oturum yönetimi."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings


class Base(DeclarativeBase):
    """Tüm ORM modellerinin temel sınıfı."""


_settings = get_settings()

engine = create_async_engine(_settings.sqlalchemy_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI bağımlılığı: istek başına bir DB oturumu."""
    async with SessionLocal() as session:
        yield session


async def create_all() -> None:
    """Tabloları oluştur (MVP: migration aracı yok)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
