"""Abonelik / premium kapıları (iskelet).

Şu an tier yalnızca free/premium. Gerçek faturalandırma (RevenueCat → Apple/Google
IAP) webhook'la tier'i çevirir; bu servis okuma + özellik kapılarını sağlar.
Canlı sesli rehber premium odaklı: free'de aylık kısa deneme, premium sınırsız.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..domain.enums import SubscriptionTier
from ..domain.models import LiveUsage, User


def is_premium(user: User) -> bool:
    return user.subscription_tier == SubscriptionTier.premium


async def month_live_seconds(db: AsyncSession, user_id: int) -> int:
    """Kullanıcının bu ayki toplam canlı saniyesi."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total = await db.scalar(
        select(func.coalesce(func.sum(LiveUsage.seconds), 0)).where(
            LiveUsage.user_id == user_id, LiveUsage.created_at >= month_start
        )
    )
    return int(total or 0)


async def remaining_free_live_seconds(
    db: AsyncSession, user: User, settings: Settings
) -> int | None:
    """Kalan ücretsiz canlı saniye; premium → None (sınırsız)."""
    if is_premium(user):
        return None
    used = await month_live_seconds(db, user.id)
    return max(0, settings.free_live_seconds_per_month - used)


async def features(db: AsyncSession, user: User, settings: Settings) -> dict[str, object]:
    """Mobil için özellik kapıları (premium nelerin kilidini açar)."""
    premium = is_premium(user)
    return {
        "live_voice": True,  # herkese açık (free'de kısa deneme, premium sınırsız)
        "live_unlimited": premium,
        "free_live_seconds_remaining": await remaining_free_live_seconds(db, user, settings),
        "unlimited_diagnosis": premium,
    }
