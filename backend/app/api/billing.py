"""Faturalandırma webhook'u (RevenueCat tarzı) — premium'u açar/kapatır.

Üretimde RevenueCat → Apple/Google IAP olayları buraya düşer; basitleştirilmiş
iskelet: paylaşılan secret ile doğrula, app_user_id (e-posta) → kullanıcı tier'i.
Secret boşsa 503; yanlış secret 403. system_instruction tarzı sızıntı yok.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db
from ..domain.ai_errors import AINotConfigured
from ..domain.enums import SubscriptionTier
from ..domain.models import User
from ..domain.schemas import BillingEventIn

router = APIRouter(prefix="/v1/billing", tags=["billing"])


@router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def billing_webhook(
    payload: BillingEventIn,
    db: AsyncSession = Depends(get_db),
    x_webhook_secret: str | None = Header(default=None),
) -> None:
    """Premium'u aç/kapat. Sağlayıcı paylaşılan secret'ı X-Webhook-Secret ile gelir."""
    settings = get_settings()
    if not settings.billing_webhook_secret:
        raise AINotConfigured("Faturalandırma webhook'u yapılandırılmamış.")
    if x_webhook_secret != settings.billing_webhook_secret:
        raise HTTPException(status_code=403, detail="Geçersiz webhook secret.")

    user = await db.scalar(select(User).where(User.email == payload.app_user_id))
    if user is None:
        return  # bilinmeyen kullanıcı — sessiz (yeniden deneme kuyruğunu tetikleme)
    user.subscription_tier = (
        SubscriptionTier.premium if payload.premium else SubscriptionTier.free
    )
    await db.commit()
