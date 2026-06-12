"""Araç CRUD iş mantığı — kullanıcı yalnızca kendi araçlarına erişir."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..domain.catalog import find_spec
from ..domain.models import Vehicle, VehicleSpec
from ..domain.schemas import VehicleCreate, VehicleUpdate


async def list_vehicles(db: AsyncSession, user_id: int) -> list[Vehicle]:
    rows = await db.scalars(
        select(Vehicle).where(Vehicle.user_id == user_id).options(selectinload(Vehicle.spec))
    )
    return list(rows)


async def get_owned(db: AsyncSession, user_id: int, vehicle_id: int) -> Vehicle:
    """Aracı getir; sahibi farklıysa 403, yoksa 404."""
    vehicle = await db.scalar(
        select(Vehicle).where(Vehicle.id == vehicle_id).options(selectinload(Vehicle.spec))
    )
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Araç bulunamadı.")
    if vehicle.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Bu araca erişim yetkin yok."
        )
    return vehicle


async def create_vehicle(db: AsyncSession, user_id: int, payload: VehicleCreate) -> Vehicle:
    vehicle = Vehicle(
        user_id=user_id,
        make=payload.make,
        model=payload.model,
        year=payload.year,
        plate=payload.plate,
        fuel_type=payload.fuel_type,
        engine_code=payload.engine_code,
        current_km=payload.current_km,
    )
    # Spec verilmediyse TR araç parkı kataloğundan otomatik doldurmayı dene.
    spec_in = payload.spec or find_spec(
        payload.make,
        payload.model,
        payload.year,
        fuel_type=payload.fuel_type,
        engine_code=payload.engine_code,
    )
    if spec_in is not None:
        vehicle.spec = VehicleSpec(**spec_in.model_dump())
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle, attribute_names=["spec"])
    return vehicle


async def update_vehicle(
    db: AsyncSession, user_id: int, vehicle_id: int, payload: VehicleUpdate
) -> Vehicle:
    vehicle = await get_owned(db, user_id, vehicle_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)
    await db.commit()
    await db.refresh(vehicle, attribute_names=["spec"])
    return vehicle


async def delete_vehicle(db: AsyncSession, user_id: int, vehicle_id: int) -> None:
    vehicle = await get_owned(db, user_id, vehicle_id)
    await db.delete(vehicle)
    await db.commit()
