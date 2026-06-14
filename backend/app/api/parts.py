"""Parça niyeti — "Satın Al" tıklaması (affiliate ölçüm + ortaklık kozu)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..database import get_db
from ..domain.models import PartLead, User
from ..domain.schemas import BuyIntentIn
from ..services import vehicle_service

router = APIRouter(prefix="/v1/parts", tags=["parts"], dependencies=[Depends(enforce_rate_limit)])


@router.post("/buy-intent", status_code=status.HTTP_201_CREATED)
async def log_buy_intent(
    payload: BuyIntentIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    """Kullanıcı bir parçanın 'Satın Al' linkine dokundu — niyeti logla.

    Admin paneli bunu toplar (perakendeci ortaklığı için talep kanıtı).
    """
    await vehicle_service.get_owned(db, user.id, payload.vehicle_id)
    lead = PartLead(
        user_id=user.id,
        vehicle_id=payload.vehicle_id,
        task=payload.task,
        part_label=payload.part_label[:80],
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return {"id": lead.id}
