"""Canlı oturum orkestrasyonu: limit kontrolü + ephemeral token + kullanım kaydı.

Akış (start_session):
  1. Canlı mod açık mı? (gemini_api_key) — yoksa AINotConfigured (503)
  2. Aylık kullanım limiti (premium hariç) — aşıldıysa LiveLimitReached (402)
  3. Oturum config'i kur (system instruction + tools, server-side)
  4. Ephemeral token üret (Google) — sadece token istemciye döner
  5. LiveUsage kaydı aç (0 sn); bitişte istemci süreyi yazar

Güvenlik: system_instruction istemciye DÖNMEZ; token'a server-side bağlanır.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import Settings
from ...domain.ai_errors import AINotConfigured, AIUpstreamError, LiveLimitReached
from ...domain.enums import SubscriptionTier
from ...domain.models import LiveUsage, User, Vehicle
from ...domain.schemas import LiveSessionOut
from . import live_service


async def _month_seconds(db: AsyncSession, user_id: int) -> int:
    """Kullanıcının bu ayki toplam canlı saniyesi."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total = await db.scalar(
        select(func.coalesce(func.sum(LiveUsage.seconds), 0)).where(
            LiveUsage.user_id == user_id, LiveUsage.created_at >= month_start
        )
    )
    return int(total or 0)


async def mint_ephemeral_token(config: dict, settings: Settings) -> str:
    """Google'dan kısa-ömürlü (ephemeral) Live token üretir.

    ⚠️ Google Live API hızlı evriliyor — uç (v1alpha/auth_tokens) ve istek/yanıt
    şeklini güncel dokümana karşı DOĞRULA. Bu fonksiyon yalıtık tutuldu: şema
    değişirse yalnızca burası güncellenir. İstemci system_instruction'ı görmez;
    config token'a server-side bağlanır.
    """
    url = (
        "https://generativelanguage.googleapis.com/v1alpha/auth_tokens"
        f"?key={settings.gemini_api_key}"
    )
    payload = {
        "uses": 1,
        "liveConnectConstraints": {
            "model": config["model"],
            "config": {
                "responseModalities": ["AUDIO"],
                "systemInstruction": {"parts": [{"text": config["system_instruction"]}]},
                "speechConfig": {
                    "languageCode": "tr-TR" if config["language"] == "tr" else "en-US",
                    "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": config["voice"]}},
                },
                "tools": [{"functionDeclarations": config["tools"]}],
            },
        },
    }
    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # ağ/şema hatası → temiz 502
        raise AIUpstreamError("Canlı oturum başlatılamadı.") from exc
    token = data.get("name") or data.get("token")
    if not token:
        raise AIUpstreamError("Canlı oturum jetonu alınamadı.")
    return str(token)


async def start_session(
    db: AsyncSession,
    *,
    user: User,
    vehicle: Vehicle,
    task: str | None,
    lang: str,
    settings: Settings,
) -> LiveSessionOut:
    if not settings.gemini_api_key:
        raise AINotConfigured("Canlı sesli rehber yapılandırılmamış.")

    # Maliyet freni: ücretsiz katmanda aylık limit (premium = sınırsız).
    if user.subscription_tier != SubscriptionTier.premium:
        used = await _month_seconds(db, user.id)
        if used >= settings.free_live_seconds_per_month:
            raise LiveLimitReached()

    config = live_service.build_session_config(
        vehicle,
        task_id=task,
        lang="en" if lang == "en" else "tr",
        model=settings.gemini_live_model,
        voice=settings.gemini_default_voice,
    )
    token = await mint_ephemeral_token(config, settings)

    usage = LiveUsage(user_id=user.id, vehicle_id=vehicle.id, task=task, lang=lang, seconds=0)
    db.add(usage)
    await db.commit()
    await db.refresh(usage)

    return LiveSessionOut(
        token=token,
        model=config["model"],
        voice=config["voice"],
        language=config["language"],
        live_usage_id=usage.id,
        max_seconds=settings.live_session_max_seconds,
    )


async def end_session(
    db: AsyncSession, *, user: User, live_usage_id: int, seconds: int, settings: Settings
) -> None:
    """İstemci oturum süresini bildirir; sert üst sınırla kırpılır."""
    usage = await db.scalar(
        select(LiveUsage).where(LiveUsage.id == live_usage_id, LiveUsage.user_id == user.id)
    )
    if usage is None:
        return  # sahiplik yok / bulunamadı — sessiz (kötüye kullanım yüzeyini küçült)
    usage.seconds = max(0, min(seconds, settings.live_session_max_seconds))
    await db.commit()
