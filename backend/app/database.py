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
    # Tarih-bazlı hatırlatıcılar (muayene / sigorta).
    ("vehicles", "muayene_date", "DATE"),
    ("vehicles", "sigorta_date", "DATE"),
    # Teşhis geçmişi özeti (AISession).
    ("ai_sessions", "task", "VARCHAR(60)"),
    ("ai_sessions", "tespit", "VARCHAR(500)"),
    ("ai_sessions", "guven", "VARCHAR(10)"),
    ("ai_sessions", "tamirciye_git", "BOOLEAN"),
    # Veri çarkı: kategori + kullanıcı geri bildirimi; log'da teşhis bağı + maliyet.
    ("ai_sessions", "kategori", "VARCHAR(30)"),
    ("ai_sessions", "feedback_dogru", "BOOLEAN"),
    ("maintenance_logs", "ai_session_id", "INTEGER"),
    ("maintenance_logs", "cost_try", "INTEGER"),
    # Arıza taksonomisi + kapanış sinyali (toplama katmanını tamamlar).
    ("ai_sessions", "ariza_sistem", "VARCHAR(20)"),
    ("ai_sessions", "resolution", "VARCHAR(20)"),
    # KVKK açık rızası.
    ("users", "consent_analytics", "BOOLEAN"),
    ("users", "consent_data", "BOOLEAN"),
    ("users", "consent_at", "TIMESTAMP"),
)


async def _add_missing_columns() -> None:
    """Eksik kolonları idempotent ekler.

    Her ALTER KENDİ transaction'ında çalışır: bir kolonun hatası diğerlerini
    etkilemez (tek transaction'da bir hata sonraki ifadeleri bozabilirdi).
    SQLite'da IF NOT EXISTS yoktur; yalnızca "kolon zaten var" hatası yutulur,
    beklenmedik hatalar yüzeye çıkar (sessiz migration kaybını önler).
    """
    dialect = engine.dialect.name
    for table, column, ddl_type in _COLUMN_MIGRATIONS:
        try:
            async with engine.begin() as conn:
                if dialect == "postgresql":
                    await conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {ddl_type}")
                    )
                else:
                    await conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")
                    )
        except Exception as exc:  # noqa: BLE001
            # "duplicate column name" (SQLite) dışındaki hatalar yeniden fırlatılır.
            if "duplicate column" not in str(exc).lower():
                raise


async def create_all() -> None:
    """Tabloları oluştur (MVP: migration aracı yok) + eksik kolonları ekle."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _add_missing_columns()
