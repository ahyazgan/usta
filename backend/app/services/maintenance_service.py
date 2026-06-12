"""Bakım geçmişi ve hatırlatma iş mantığı (kullanıcı yalnızca kendi aracı)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.maintenance import Reminder, compute_reminders
from ..domain.models import MaintenanceLog
from ..domain.schemas import MaintenanceLogCreate
from ..domain.tasks import tasks_for_fuel
from . import vehicle_service


async def add_log(
    db: AsyncSession, user_id: int, vehicle_id: int, payload: MaintenanceLogCreate
) -> MaintenanceLog:
    await vehicle_service.get_owned(db, user_id, vehicle_id)  # 403/404 garanti
    log = MaintenanceLog(vehicle_id=vehicle_id, task=payload.task, km=payload.km, note=payload.note)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def list_logs(db: AsyncSession, user_id: int, vehicle_id: int) -> list[MaintenanceLog]:
    await vehicle_service.get_owned(db, user_id, vehicle_id)
    rows = await db.scalars(
        select(MaintenanceLog)
        .where(MaintenanceLog.vehicle_id == vehicle_id)
        .order_by(MaintenanceLog.created_at.desc(), MaintenanceLog.id.desc())
    )
    return list(rows)


async def get_reminders(db: AsyncSession, user_id: int, vehicle_id: int) -> list[Reminder]:
    vehicle = await vehicle_service.get_owned(db, user_id, vehicle_id)
    logs = await list_logs(db, user_id, vehicle_id)

    # Görev başına EN SON km'li kayıt (kayıtlar zaten created_at desc sıralı).
    last_km_by_task: dict[str, int] = {}
    for log in logs:
        if log.km is not None and log.task not in last_km_by_task:
            last_km_by_task[log.task] = log.km

    reminders = compute_reminders(vehicle.current_km, last_km_by_task)
    # Bu aracın yakıtına uygulanamayan görevleri ele (örn. dizelde buji).
    applicable = {t.id for t in tasks_for_fuel(vehicle.fuel_type)}
    return [r for r in reminders if r.task in applicable]
