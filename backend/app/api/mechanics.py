"""Tamirci dizini + yönlendirme (lead) rotaları — Faz C MVP.

Küratörlü tamirci listesi (şehir/sistem filtreli) ve lead kaydı. Lead'ler
ileride tamircilerden ücretlendirme (lead-gen) modelinin temelidir.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..database import get_db
from ..domain.models import AISession, Mechanic, MechanicLead, User
from ..domain.schemas import MechanicLeadIn, MechanicOut

router = APIRouter(prefix="/v1/mechanics", tags=["mechanics"], dependencies=[Depends(enforce_rate_limit)])


@router.get("", response_model=list[MechanicOut])
async def list_mechanics(
    city: str | None = None,
    system: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[MechanicOut]:
    """Tamircileri listeler; şehre göre süzer, sisteme göre öncelikle eşleşeni öne alır.

    `system` verilirse: o sisteme bakan (veya genel) tamirciler döner, eşleşenler
    önce. Doğrulanmış (verified) tamirciler her zaman üstte.
    """
    stmt = select(Mechanic)
    if city:
        stmt = stmt.where(Mechanic.city == city)
    rows = list(await db.scalars(stmt))

    def matches_system(m: Mechanic) -> bool:
        if system is None:
            return True
        if not m.systems:
            return True  # genel tamirci
        return system in [s.strip() for s in m.systems.split(",")]

    filtered = [m for m in rows if matches_system(m)]

    def sort_key(m: Mechanic) -> tuple[int, int, str]:
        # matches_system ile aynı token-bazlı mantık (substring tuzağına düşmez).
        specific = bool(system and m.systems and system in [s.strip() for s in m.systems.split(",")])
        return (0 if m.verified else 1, 0 if specific else 1, m.name)

    filtered.sort(key=sort_key)
    return [MechanicOut.model_validate(m) for m in filtered]


@router.post("/{mechanic_id}/lead", status_code=status.HTTP_201_CREATED)
async def record_lead(
    mechanic_id: int,
    payload: MechanicLeadIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    """Kullanıcı bir tamirciye ulaştığında (ara/WhatsApp/yol tarifi) lead kaydeder."""
    mechanic = await db.get(Mechanic, mechanic_id)
    if mechanic is None:
        raise HTTPException(status_code=404, detail="Tamirci bulunamadı")

    # ai_session bağı yalnızca kullanıcının kendi oturumuysa kabul edilir.
    session_id = payload.ai_session_id
    if session_id is not None:
        owned = await db.scalar(
            select(AISession.id).where(
                AISession.id == session_id, AISession.user_id == user.id
            )
        )
        if owned is None:
            session_id = None

    lead = MechanicLead(
        user_id=user.id,
        mechanic_id=mechanic_id,
        ai_session_id=session_id,
        channel=payload.channel,
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return {"id": lead.id}
