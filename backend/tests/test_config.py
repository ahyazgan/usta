"""DB URL normalizasyonu testleri (Render/Heroku postgres:// -> asyncpg)."""

from app.config import Settings


def test_normalizes_postgres_scheme():
    s = Settings(database_url="postgres://u:p@host:5432/db")
    assert s.sqlalchemy_url == "postgresql+asyncpg://u:p@host:5432/db"


def test_normalizes_postgresql_scheme():
    s = Settings(database_url="postgresql://u:p@host/db")
    assert s.sqlalchemy_url == "postgresql+asyncpg://u:p@host/db"


def test_leaves_asyncpg_untouched():
    url = "postgresql+asyncpg://u:p@host/db"
    assert Settings(database_url=url).sqlalchemy_url == url


def test_leaves_sqlite_untouched():
    url = "sqlite+aiosqlite:///./usta.db"
    assert Settings(database_url=url).sqlalchemy_url == url
