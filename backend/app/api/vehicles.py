"""Araç CRUD rotaları — kullanıcı yalnızca kendi araçlarına erişir (JWT)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..database import get_db
from ..domain.models import User
from ..domain.schemas import VehicleCreate, VehicleOut, VehicleUpdate
from ..services import vehicle_service

router = APIRouter(prefix="/v1/vehicles", tags=["vehicles"], dependencies=[Depends(enforce_rate_limit)])


@router.get("", response_model=list[VehicleOut])
async def list_vehicles(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[VehicleOut]:
    vehicles = await vehicle_service.list_vehicles(db, user.id)
    return [VehicleOut.model_validate(v) for v in vehicles]


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    payload: VehicleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VehicleOut:
    vehicle = await vehicle_service.create_vehicle(db, user.id, payload)
    return VehicleOut.model_validate(vehicle)


@router.get("/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VehicleOut:
    vehicle = await vehicle_service.get_owned(db, user.id, vehicle_id)
    return VehicleOut.model_validate(vehicle)


@router.patch("/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VehicleOut:
    vehicle = await vehicle_service.update_vehicle(db, user.id, vehicle_id, payload)
    return VehicleOut.model_validate(vehicle)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    await vehicle_service.delete_vehicle(db, user.id, vehicle_id)
