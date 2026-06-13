"""Hesap & KVKK rotaları: açık rıza + veri silme hakkı.

- GET/PATCH /v1/me/consent: davranış analitiği ve anonim küme kullanımı rızası.
- DELETE /v1/me: kullanıcı ve TÜM verisini siler (silme/unutulma hakkı).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..database import get_db
from ..domain.models import (
    AISession,
    LiveUsage,
    MaintenanceLog,
    MechanicLead,
    PartLead,
    RefreshToken,
    User,
    Vehicle,
)
from ..domain.schemas import ConsentOut, ConsentUpdate, SubscriptionOut
from ..services import subscription_service

router = APIRouter(prefix="/v1/me", tags=["account"], dependencies=[Depends(enforce_rate_limit)])


def _consent_out(user: User) -> ConsentOut:
    # null = henüz seçim yok → varsayılan KAPALI.
    return ConsentOut(
        analytics=bool(user.consent_analytics),
        data=bool(user.consent_data),
    )


@router.get("/consent", response_model=ConsentOut)
async def get_consent(user: User = Depends(get_current_user)) -> ConsentOut:
    return _consent_out(user)


@router.get("/subscription", response_model=SubscriptionOut)
async def get_subscription(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubscriptionOut:
    """Abonelik durumu + premium özellik kapıları (mobil bunu okur)."""
    settings = get_settings()
    return SubscriptionOut(
        tier=user.subscription_tier,
        is_premium=subscription_service.is_premium(user),
        live_unlimited=subscription_service.is_premium(user),
        free_live_seconds_remaining=await subscription_service.remaining_free_live_seconds(
            db, user, settings
        ),
    )


@router.patch("/consent", response_model=ConsentOut)
async def update_consent(
    payload: ConsentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConsentOut:
    if payload.analytics is not None:
        user.consent_analytics = payload.analytics
    if payload.data is not None:
        user.consent_data = payload.data
    user.consent_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return _consent_out(user)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Silme/unutulma hakkı: kullanıcı + tüm araç/log/teşhis/oturum verisi silinir.

    FK cascade'e güvenmeden açıkça siler (SQLite/Postgres farkından bağımsız).
    """
    vehicle_ids = (
        await db.scalars(select(Vehicle.id).where(Vehicle.user_id == user.id))
    ).all()
    if vehicle_ids:
        await db.execute(
            delete(MaintenanceLog).where(MaintenanceLog.vehicle_id.in_(vehicle_ids))
        )
    # Lead'ler AISession'a (SET NULL) ve User'a (CASCADE) bağlı; SQLite cascade
    # uygulamadığından açıkça silinir, yoksa unutulma hakkı sonrası yetim kalır.
    await db.execute(delete(MechanicLead).where(MechanicLead.user_id == user.id))
    await db.execute(delete(PartLead).where(PartLead.user_id == user.id))
    await db.execute(delete(LiveUsage).where(LiveUsage.user_id == user.id))
    await db.execute(delete(AISession).where(AISession.user_id == user.id))
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.execute(delete(Vehicle).where(Vehicle.user_id == user.id))
    await db.execute(delete(User).where(User.id == user.id))
    await db.commit()
