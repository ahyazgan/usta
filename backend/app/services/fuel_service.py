"""Yakıt & masraf takibi iş mantığı (kullanıcı yalnızca kendi aracı).

Tüketim, "tam depodan tam depoya" (full-to-full) yöntemiyle hesaplanır:
ardışık iki tam-depo dolumu arasında alınan litre / katedilen km * 100.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import FuelLog
from ..domain.schemas import FuelLogCreate, FuelSummaryOut
from . import vehicle_service


async def add_fuel_log(
    db: AsyncSession, user_id: int, vehicle_id: int, payload: FuelLogCreate
) -> FuelLog:
    await vehicle_service.get_owned(db, user_id, vehicle_id)  # 403/404 garanti
    log = FuelLog(
        vehicle_id=vehicle_id,
        odometer_km=payload.odometer_km,
        liters=payload.liters,
        total_try=payload.total_try,
        full_tank=payload.full_tank,
        note=payload.note,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def list_fuel_logs(db: AsyncSession, user_id: int, vehicle_id: int) -> list[FuelLog]:
    await vehicle_service.get_owned(db, user_id, vehicle_id)
    rows = await db.scalars(
        select(FuelLog)
        .where(FuelLog.vehicle_id == vehicle_id)
        .order_by(FuelLog.odometer_km.desc(), FuelLog.id.desc())
    )
    return list(rows)


def _avg_consumption(logs: list[FuelLog]) -> float | None:
    """Tam-depo dolumlarından ortalama L/100km. <2 tam dolum varsa None."""
    full = sorted(
        (lg for lg in logs if lg.full_tank), key=lambda lg: lg.odometer_km
    )
    if len(full) < 2:
        return None
    total_km = 0
    total_liters = 0.0
    for prev, cur in zip(full, full[1:]):
        km = cur.odometer_km - prev.odometer_km
        if km <= 0:
            continue  # tutarsız/aynı km — atla
        # Full-to-full: bir sonraki tam dolumun litresi, o aralıkta yakılan yakıttır.
        total_km += km
        total_liters += cur.liters
    if total_km <= 0:
        return None
    return round(total_liters / total_km * 100, 1)


async def fuel_summary(db: AsyncSession, user_id: int, vehicle_id: int) -> FuelSummaryOut:
    logs = await list_fuel_logs(db, user_id, vehicle_id)
    total_liters = round(sum(lg.liters for lg in logs), 1)
    total_spent = sum(lg.total_try for lg in logs if lg.total_try is not None)
    last_odo = max((lg.odometer_km for lg in logs), default=None)
    return FuelSummaryOut(
        entry_count=len(logs),
        total_liters=total_liters,
        total_spent_try=total_spent,
        avg_consumption=_avg_consumption(logs),
        last_odometer_km=last_odo,
    )
