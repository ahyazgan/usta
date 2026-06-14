"""Admin istatistik paneli — lead/tıklama/canlı özeti (ortaklık görüşme kozu).

Token ile korunur (X-Admin-Token == config.admin_token). Token boşsa 503,
yanlışsa 403. Kullanıcıya açık DEĞİL — kurucu/iş-geliştirme içindir.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db
from ..domain.ai_errors import AINotConfigured
from ..domain.enums import SubscriptionTier
from ..domain.models import LiveUsage, Mechanic, MechanicLead, PartLead, User

router = APIRouter(prefix="/v1/admin", tags=["admin"])

_DASHBOARD = Path(__file__).resolve().parent.parent / "static" / "admin.html"


@router.get("/dashboard", include_in_schema=False)
async def dashboard() -> FileResponse:
    """Token'la açılan basit web paneli (veri /stats'tan client-side çekilir)."""
    return FileResponse(_DASHBOARD, media_type="text/html")


def _require_admin(x_admin_token: str | None) -> None:
    settings = get_settings()
    if not settings.admin_token:
        raise AINotConfigured("Admin paneli yapılandırılmamış.")
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Geçersiz admin token.")


@router.get("/stats")
async def stats(
    db: AsyncSession = Depends(get_db),
    x_admin_token: str | None = Header(default=None),
) -> dict:
    """Lead-gen + parça-niyet + canlı + kullanıcı özeti (talep kanıtı)."""
    _require_admin(x_admin_token)
    since30 = datetime.now(timezone.utc) - timedelta(days=30)

    async def _count(stmt) -> int:
        return int(await db.scalar(stmt) or 0)

    # Tamirci yönlendirmeleri (lead-gen)
    lead_total = await _count(select(func.count(MechanicLead.id)))
    lead_30 = await _count(
        select(func.count(MechanicLead.id)).where(MechanicLead.created_at >= since30)
    )
    by_channel = {
        ch: n
        for ch, n in (
            await db.execute(
                select(MechanicLead.channel, func.count(MechanicLead.id)).group_by(
                    MechanicLead.channel
                )
            )
        ).all()
    }
    top_mechanics = [
        {"name": name, "city": city, "leads": n}
        for name, city, n in (
            await db.execute(
                select(Mechanic.name, Mechanic.city, func.count(MechanicLead.id))
                .join(MechanicLead, MechanicLead.mechanic_id == Mechanic.id)
                .group_by(Mechanic.id)
                .order_by(func.count(MechanicLead.id).desc())
                .limit(10)
            )
        ).all()
    ]

    # Parça-alım niyeti (affiliate talep kanıtı)
    part_total = await _count(select(func.count(PartLead.id)))
    part_30 = await _count(
        select(func.count(PartLead.id)).where(PartLead.created_at >= since30)
    )
    top_parts = [
        {"part": label, "intents": n}
        for label, n in (
            await db.execute(
                select(PartLead.part_label, func.count(PartLead.id))
                .group_by(PartLead.part_label)
                .order_by(func.count(PartLead.id).desc())
                .limit(10)
            )
        ).all()
    ]

    # Canlı kullanım + kullanıcı tabanı
    live_sessions = await _count(select(func.count(LiveUsage.id)))
    live_seconds = await _count(select(func.coalesce(func.sum(LiveUsage.seconds), 0)))
    users_total = await _count(select(func.count(User.id)))
    users_premium = await _count(
        select(func.count(User.id)).where(User.subscription_tier == SubscriptionTier.premium)
    )

    return {
        "mechanic_leads": {
            "total": lead_total,
            "last_30_days": lead_30,
            "by_channel": by_channel,
            "top_mechanics": top_mechanics,
        },
        "part_intents": {"total": part_total, "last_30_days": part_30, "top_parts": top_parts},
        "live": {"sessions": live_sessions, "total_seconds": live_seconds},
        "users": {"total": users_total, "premium": users_premium},
    }
