"""Katalog yardımcı rotaları — formda 'bilinen markadan seç' için."""

from fastapi import APIRouter, Depends

from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..domain.catalog import CATALOG
from ..domain.enums import VehicleType
from ..domain.models import User

router = APIRouter(prefix="/v1/catalog", tags=["catalog"], dependencies=[Depends(enforce_rate_limit)])


@router.get("/brands", response_model=list[str])
async def brands(
    vehicle_type: VehicleType | None = None,
    _user: User = Depends(get_current_user),
) -> list[str]:
    """Katalogdaki markalar (araç türüne göre, alfabetik). vehicle_type
    verilmezse araba kabul edilir."""
    vtype = vehicle_type or VehicleType.araba
    return sorted({e.make for e in CATALOG if e.vehicle_type == vtype})
