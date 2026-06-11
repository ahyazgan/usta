"""Bakım geçmişi & hatırlatma rotaları (JWT + rate limit, araç sahipliği)."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..database import get_db
from ..domain.models import User
from ..domain.schemas import MaintenanceLogCreate, MaintenanceLogOut, ReminderOut, TaskOut
from ..domain.tasks import tasks_for_fuel
from ..services import maintenance_service, vehicle_service

router = APIRouter(
    prefix="/v1/vehicles/{vehicle_id}",
    tags=["maintenance"],
    dependencies=[Depends(enforce_rate_limit)],
)


@router.post("/logs", response_model=MaintenanceLogOut, status_code=status.HTTP_201_CREATED)
async def add_log(
    vehicle_id: int,
    payload: MaintenanceLogCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MaintenanceLogOut:
    log = await maintenance_service.add_log(db, user.id, vehicle_id, payload)
    return MaintenanceLogOut.model_validate(log)


@router.get("/logs", response_model=list[MaintenanceLogOut])
async def list_logs(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[MaintenanceLogOut]:
    logs = await maintenance_service.list_logs(db, user.id, vehicle_id)
    return [MaintenanceLogOut.model_validate(log) for log in logs]


@router.get("/tasks", response_model=list[TaskOut])
async def vehicle_tasks(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskOut]:
    """Bu aracın yakıt türüne uygulanabilir bakım görevleri (örn. dizelde buji yok)."""
    vehicle = await vehicle_service.get_owned(db, user.id, vehicle_id)
    return [
        TaskOut(id=t.id, title_tr=t.title_tr, title_en=t.title_en, risk=t.risk)
        for t in tasks_for_fuel(vehicle.fuel_type)
    ]


@router.get("/reminders", response_model=list[ReminderOut])
async def get_reminders(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ReminderOut]:
    reminders = await maintenance_service.get_reminders(db, user.id, vehicle_id)
    return [ReminderOut(**asdict(r)) for r in reminders]
