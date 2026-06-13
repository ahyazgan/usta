"""Uygulama ayarları. Ortam değişkenlerinden okunur."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="USTA_", extra="ignore")

    app_name: str = "Usta API"
    debug: bool = True

    # Veritabanı (MVP: tek Postgres / testte SQLite). pgvector/Redis/S3 YOK.
    database_url: str = "sqlite+aiosqlite:///./usta.db"

    # Kimlik doğrulama
    jwt_secret: str = "dev-secret-degistir-beni-en-az-32-bayt-olsun-prod"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    bcrypt_rounds: int = 12

    # CORS — debug'da "*", prod'da sadece resmi alan adı
    prod_cors_origin: str = "https://usta.app"

    # Claude / maliyet kuralları
    anthropic_api_key: str = ""
    # MALİYET KURALI: vision = sonnet, Opus YASAK. Frame max 1024px JPEG 0.7.
    vision_model: str = "claude-sonnet-4-5"
    audio_model: str = "claude-sonnet-4-5"
    max_frame_px: int = 1024
    jpeg_quality: float = 0.7
    ai_timeout_seconds: float = 30.0
    ai_max_retries: int = 2  # tenacity retry(2) => toplam 3 deneme
    ai_max_tokens: int = 1024

    # Kullanıcı-bazlı rate limit (dakikada istek)
    rate_limit_per_minute: int = 30

    # Parça "Satın Al" linki (affiliate iskeleti). {q} = arama sorgusu.
    # Şimdilik jenerik arama; affiliate anlaşması gelince env ile değiştir:
    #   USTA_PARTS_BUY_URL_TEMPLATE="https://ORTAK.com/ara?q={q}&aff=USTA"
    # Boş string → "Satın Al" linki gösterilmez.
    parts_buy_url_template: str = "https://www.google.com/search?q={q}"

    # Canlı sesli rehber (Gemini Live). Anahtar boşsa canlı mod KAPALI (503).
    # API anahtarı SADECE ortam değişkeniyle verilir (koda/git'e ASLA yazma):
    #   USTA_GEMINI_API_KEY=...
    gemini_api_key: str = ""
    # Model adı API ile doğrulandı (models?key= → mevcut). Gerekirse "models/" öneki
    # ya da güncel sürüm için env ile değiştir: USTA_GEMINI_LIVE_MODEL=...
    gemini_live_model: str = "gemini-3.1-flash-live-preview"
    gemini_default_voice: str = "Puck"  # Gemini Live ses adı
    # Ücretsiz katmanda aylık canlı saniye sınırı (maliyet freni). Premium = sınırsız.
    free_live_seconds_per_month: int = 600  # 10 dk/ay
    # Tek oturum sert üst sınırı (saniye) — kaçak maliyeti engeller.
    live_session_max_seconds: int = 600

    @property
    def cors_origins(self) -> list[str]:
        return ["*"] if self.debug else [self.prod_cors_origin]

    @property
    def sqlalchemy_url(self) -> str:
        """DB URL'ini async sürücüye normalize eder.

        Render/Heroku gibi sağlayıcılar `postgres://` verir; SQLAlchemy async
        motoru `postgresql+asyncpg://` ister.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url[len("postgres://") :]
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            return "postgresql+asyncpg://" + url[len("postgresql://") :]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
