"""Async SQLAlchemy motoru ve oturum yönetimi."""

from collections.abc import AsyncGenerator

from sqlalchemy import text
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


# Mevcut tablolara sonradan eklenen kolonlar. create_all() yeni tablo açar ama
# var olan tabloyu DEĞİŞTİRMEZ; migration aracı (alembic) MVP dışı olduğundan
# idempotent ADD COLUMN ifadeleriyle kapatıyoruz. (tablo, kolon, tip)
_COLUMN_MIGRATIONS: tuple[tuple[str, str, str], ...] = (
    ("vehicles", "plate", "VARCHAR(15)"),
)


async def _add_missing_columns() -> None:
    async with engine.begin() as conn:
        dialect = conn.dialect.name
        for table, column, ddl_type in _COLUMN_MIGRATIONS:
            if dialect == "postgresql":
                await conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {ddl_type}")
                )
            else:
                # SQLite: IF NOT EXISTS yok — kolon zaten varsa hatayı yut.
                try:
                    await conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")
                    )
                except Exception:  # noqa: BLE001 — duplicate column
                    pass


async def create_all() -> None:
    """Tabloları oluştur (MVP: migration aracı yok) + eksik kolonları ekle."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _add_missing_columns()
