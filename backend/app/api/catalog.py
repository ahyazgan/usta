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


@router.get("/models", response_model=list[str])
async def models(
    make: str,
    vehicle_type: VehicleType | None = None,
    _user: User = Depends(get_current_user),
) -> list[str]:
    """Bir markanın katalogdaki modelleri (araç türüne göre, alfabetik).
    'yazmak yerine seç' için marka seçilince doldurulur. Eşleşme büyük/küçük
    harf duyarsızdır; make boş/bilinmeyense boş liste döner."""
    vtype = vehicle_type or VehicleType.araba
    make_n = make.strip().casefold()
    if not make_n:
        return []
    return sorted(
        {
            e.model
            for e in CATALOG
            if e.vehicle_type == vtype and e.make.casefold() == make_n
        }
    )
