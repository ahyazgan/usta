"""Yakıt & masraf takibi rotaları (JWT + rate limit, araç sahipliği)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..database import get_db
from ..domain.models import User
from ..domain.schemas import FuelLogCreate, FuelLogOut, FuelSummaryOut
from ..services import fuel_service

router = APIRouter(
    prefix="/v1/vehicles/{vehicle_id}/fuel",
    tags=["fuel"],
    dependencies=[Depends(enforce_rate_limit)],
)


@router.post("", response_model=FuelLogOut, status_code=status.HTTP_201_CREATED)
async def add_fuel_log(
    vehicle_id: int,
    payload: FuelLogCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FuelLogOut:
    log = await fuel_service.add_fuel_log(db, user.id, vehicle_id, payload)
    return FuelLogOut.model_validate(log)


@router.get("", response_model=list[FuelLogOut])
async def list_fuel_logs(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[FuelLogOut]:
    logs = await fuel_service.list_fuel_logs(db, user.id, vehicle_id)
    return [FuelLogOut.model_validate(log) for log in logs]


@router.get("/summary", response_model=FuelSummaryOut)
async def fuel_summary(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FuelSummaryOut:
    return await fuel_service.fuel_summary(db, user.id, vehicle_id)
