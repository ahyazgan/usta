"""Bakım geçmişi & hatırlatma rotaları (JWT + rate limit, araç sahipliği)."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..core.rate_limit import enforce_rate_limit
from ..database import get_db
from ..domain.models import User
from sqlalchemy import select

from ..domain.guides import fill_template, get_guide
from ..domain.models import AISession
from ..domain.schemas import (
    DiagnosisHistoryOut,
    GuideStepOut,
    MaintenanceLogCreate,
    MaintenanceLogOut,
    ReminderOut,
    TaskGuideOut,
    TaskOut,
    VehicleSummaryOut,
)
from ..domain.tasks import get_task, tasks_for_fuel
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


@router.get("/tasks/{task_id}/guide", response_model=TaskGuideOut)
async def task_guide(
    vehicle_id: int,
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskGuideOut:
    """Araca özel doldurulmuş adım adım bakım rehberi.

    Talimatlardaki {yer_tutucular} aracın spec'inden doldurulur (örn. tıpa
    ölçüsü "14mm"); görev bu aracın yakıtına uygulanamıyorsa 404 döner.
    """
    vehicle = await vehicle_service.get_owned(db, user.id, vehicle_id)
    task = get_task(task_id)
    guide = get_guide(task_id)
    if task is None or guide is None:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    if task.applies_to_fuels and vehicle.fuel_type not in task.applies_to_fuels:
        raise HTTPException(status_code=404, detail="Görev bu araca uygulanamaz")

    spec_values: dict[str, object] = {}
    if vehicle.spec is not None:
        for key in (
            "oil_spec", "oil_capacity_l", "oil_drain_bolt_size", "oil_filter_part",
            "air_filter_part", "cabin_filter_part", "spark_plug_part",
            "battery_spec", "battery_location",
        ):
            spec_values[key] = getattr(vehicle.spec, key, None)

    steps = [
        GuideStepOut(
            step=i,
            instruction_tr=fill_template(s.instruction_tr, spec_values, "tr"),
            instruction_en=fill_template(s.instruction_en, spec_values, "en"),
            tool_tr=fill_template(s.tool_tr, spec_values, "tr") if s.tool_tr else None,
            tool_en=fill_template(s.tool_en, spec_values, "en") if s.tool_en else None,
            torque_nm=s.torque_nm,
            warning_tr=s.warning_tr,
            warning_en=s.warning_en,
        )
        for i, s in enumerate(guide.steps, start=1)
    ]
    return TaskGuideOut(
        task_id=task.id,
        title_tr=task.title_tr,
        title_en=task.title_en,
        risk=task.risk,
        est_minutes=guide.est_minutes,
        diy_saving_try=task.diy_saving_try,
        steps=steps,
        mechanic_note_tr=guide.mechanic_note_tr,
        mechanic_note_en=guide.mechanic_note_en,
    )


@router.get("/diagnoses", response_model=list[DiagnosisHistoryOut])
async def diagnosis_history(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[DiagnosisHistoryOut]:
    """Bu aracın son AI teşhisleri (görüntü + ses), yeniden eskiye, en çok 20.

    Eski kayıtlarda özet alanlar boş olabilir; içeriksiz satırlar listelenmez.
    """
    await vehicle_service.get_owned(db, user.id, vehicle_id)
    rows = await db.scalars(
        select(AISession)
        .where(
            AISession.vehicle_id == vehicle_id,
            AISession.user_id == user.id,
            AISession.tespit.is_not(None),
        )
        .order_by(AISession.created_at.desc(), AISession.id.desc())
        .limit(20)
    )
    return [DiagnosisHistoryOut.model_validate(r) for r in rows]


@router.get("/summary", response_model=VehicleSummaryOut)
async def vehicle_summary(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VehicleSummaryOut:
    """Kayıtlı bakım sayısı + tahmini DIY tasarrufu (loglardan toplanır)."""
    # Sahiplik doğrulaması (kendi aracı değilse 404/403).
    await vehicle_service.get_owned(db, user.id, vehicle_id)
    logs = await maintenance_service.list_logs(db, user.id, vehicle_id)
    savings = 0
    for log in logs:
        task = get_task(log.task)
        if task is not None:
            savings += task.diy_saving_try
    return VehicleSummaryOut(maintenance_count=len(logs), savings_try=savings)
