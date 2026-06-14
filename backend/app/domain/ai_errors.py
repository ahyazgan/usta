"""AI servisi hataları — temiz HTTP durumlarına eşlenir (çıplak 500 yerine).

Bu hatalar servis/istemci katmanından fırlatılır; api katmanındaki tek bir
exception handler bunları kullanıcı-dostu JSON yanıtlara çevirir.
"""

from __future__ import annotations


class AIError(Exception):
    """AI çağrısıyla ilgili tüm hataların temeli."""

    status_code: int = 503
    code: str = "ai_unavailable"
    default_message: str = "AI servisi şu an kullanılamıyor. Lütfen sonra dene."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class AINotConfigured(AIError):
    """API anahtarı yok / istemci yapılandırılmadı."""

    status_code = 503
    code = "ai_not_configured"
    default_message = "AI servisi yapılandırılmamış (API anahtarı eksik)."


class AIUpstreamError(AIError):
    """Claude'dan geçersiz/çözümlenemeyen yanıt ya da bağlantı hatası."""

    status_code = 502
    code = "ai_upstream"
    default_message = "AI servisinden geçerli bir yanıt alınamadı. Lütfen tekrar dene."


class AIRateLimited(AIError):
    """Üst servis (Claude) hız sınırına takıldı."""

    status_code = 429
    code = "ai_rate_limited"
    default_message = "AI servisi şu an yoğun. Lütfen biraz sonra tekrar dene."


class LiveLimitReached(AIError):
    """Ücretsiz katman aylık canlı süre limiti doldu (premium gerekir)."""

    status_code = 402
    code = "live_limit_reached"
    default_message = "Aylık ücretsiz canlı süresi doldu. Premium ile sınırsız."
