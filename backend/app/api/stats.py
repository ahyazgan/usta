"""Anonim küme istatistikleri (KVKK uyumlu).

Veri hendeğinin ilk ürünü ve anonimleştirme prensibinin kanıtı:
- YALNIZCA veri rızası (consent_data) veren kullanıcıların teşhisleri sayılır.
- Sonuç kişi-bağımsız küme; hiçbir satır bireysel kullanıcı/araç döndürmez.
- k-anonimlik: MIN_BUCKET altındaki sistemler gizlenir (yeniden tanımlanamasın).
"""

from fastapi import APIRouter, Depends
from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..database import get_db
from ..domain.models import AISession, User
from ..domain.schemas import SystemStatOut

# Bir sistem en az bu kadar teşhise sahip değilse istatistikte gösterilmez.
MIN_BUCKET = 5

router = APIRouter(prefix="/v1/stats", tags=["stats"], dependencies=[Depends(enforce_rate_limit)])


@router.get("/systems", response_model=list[SystemStatOut])
async def system_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[SystemStatOut]:
    """Araç sistemi başına anonim teşhis dağılımı + doğruluk oranı."""
    dogru = func.sum(
        # feedback_dogru True olanları say (DB-agnostik).
        func.coalesce(AISession.feedback_dogru, False).cast(Integer)
    )
    oylanan = func.count(AISession.feedback_dogru)
    rows = (
        await db.execute(
            select(
                AISession.ariza_sistem,
                func.count(AISession.id),
                oylanan,
                dogru,
            )
            .join(User, User.id == AISession.user_id)
            .where(
                User.consent_data.is_(True),
                AISession.ariza_sistem.is_not(None),
            )
            .group_by(AISession.ariza_sistem)
            .having(func.count(AISession.id) >= MIN_BUCKET)
        )
    ).all()

    out: list[SystemStatOut] = []
    for sistem, count, voted, correct in rows:
        voted = int(voted or 0)
        correct = int(correct or 0)
        out.append(
            SystemStatOut(
                sistem=sistem,
                count=int(count),
                dogrulanan=voted,
                dogruluk_orani=(round(correct / voted, 3) if voted > 0 else None),
            )
        )
    out.sort(key=lambda s: s.count, reverse=True)
    return out
