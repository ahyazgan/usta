"""Teşhis-bazlı maliyet tahmini — arıza sistemine göre (kamera/ses sonucu)."""

from fastapi import APIRouter, Depends, HTTPException

from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..database import get_db
from ..domain.enums import ArizaSistem, VehicleType
from ..domain.models import User
from ..domain.schemas import CostEstimateOut
from ..services import cost_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/v1/estimate",
    tags=["estimate"],
    dependencies=[Depends(enforce_rate_limit)],
)


@router.get("/diagnosis", response_model=CostEstimateOut)
async def diagnosis_cost_estimate(
    ariza_sistem: ArizaSistem,
    vehicle_type: VehicleType | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> CostEstimateOut:
    """Bir arıza sisteminin tamirciye tahmini maliyeti (teşhis sonrası).

    Tohumla başlar; aynı sistem+araç-türü için yeterli gerçek ödeme birikince
    topluluğa kayar. Bilinmeyen sistemde 404.
    """
    est = await cost_service.estimate_system(db, ariza_sistem.value, vehicle_type)
    if est is None:
        raise HTTPException(status_code=404, detail="Bu sistem için maliyet tahmini yok")
    return CostEstimateOut(
        low_try=est.low_try,
        high_try=est.high_try,
        source=est.source,
        sample_size=est.sample_size,
    )
