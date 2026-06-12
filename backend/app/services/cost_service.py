"""Maliyet tahmin servisi — tohum bantları + topluluk (gerçek ödenen) verisi.

Akış: tohum bandıyla başla; aynı görev/araç-türü için yeterli (>= MIN_SAMPLES)
gerçek `cost_try` kaydı birikmişse, p25–p75 aralığını topluluktan hesapla ve
onu döndür (k-anonimlik: az örnekte bireysel fiyat sızmaz). Çark döndükçe tahmin
tohumdan gerçeğe kayar — kopyalanamaz fiyat hendeği.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.cost_estimates import CostBand, seed_system_band, seed_task_band
from ..domain.enums import VehicleType
from ..domain.models import AISession, MaintenanceLog, Vehicle

# Topluluk bandını göstermek için gereken en az gerçek-fiyat örneği (k-anon).
MIN_SAMPLES = 5


@dataclass(slots=True, frozen=True)
class CostEstimate:
    low_try: int
    high_try: int
    source: str  # "seed" | "community"
    sample_size: int


def _round50(value: float) -> int:
    return int(round(value / 50.0) * 50)


def _percentile(sorted_vals: list[int], q: float) -> int:
    """Basit yüzdelik (q ∈ [0,1]); küçük örnek için yeterli."""
    if not sorted_vals:
        return 0
    idx = min(len(sorted_vals) - 1, max(0, int(round(q * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


def _blend(seed: CostBand | None, costs: list[int]) -> CostEstimate | None:
    """Yeterli gerçek veri varsa topluluk bandı; yoksa tohum bandı."""
    n = len(costs)
    if n >= MIN_SAMPLES:
        costs.sort()
        low = _round50(_percentile(costs, 0.25))
        high = _round50(_percentile(costs, 0.75))
        if high < low:  # tek değere yığılma kenar durumu
            high = low
        return CostEstimate(low_try=low, high_try=high, source="community", sample_size=n)
    if seed is None:
        return None
    return CostEstimate(low_try=seed.low, high_try=seed.high, source="seed", sample_size=n)


def _vehicle_type_clause(vehicle_type: VehicleType | None):
    """Araç türü filtresi; araba sorgusunda eski null kayıtları da kapsar."""
    vtype = vehicle_type or VehicleType.araba
    if vtype == VehicleType.araba:
        return or_(Vehicle.vehicle_type == VehicleType.araba, Vehicle.vehicle_type.is_(None))
    return Vehicle.vehicle_type == vtype


async def _task_costs(db: AsyncSession, task_id: str, vehicle_type: VehicleType | None) -> list[int]:
    rows = await db.scalars(
        select(MaintenanceLog.cost_try)
        .join(Vehicle, MaintenanceLog.vehicle_id == Vehicle.id)
        .where(
            MaintenanceLog.task == task_id,
            MaintenanceLog.cost_try.is_not(None),
            MaintenanceLog.cost_try > 0,
            _vehicle_type_clause(vehicle_type),
        )
    )
    return [int(c) for c in rows]


async def _system_costs(
    db: AsyncSession, ariza_sistem: str, vehicle_type: VehicleType | None
) -> list[int]:
    # Kaynak: teşhis kapanışında "tamirci çözdü" + beyan edilen ödeme
    # (AISession.cost_try). Sadece tamirci ödemeleri → band temiz kalır.
    rows = await db.scalars(
        select(AISession.cost_try)
        .join(Vehicle, AISession.vehicle_id == Vehicle.id)
        .where(
            AISession.ariza_sistem == ariza_sistem,
            AISession.cost_try.is_not(None),
            AISession.cost_try > 0,
            _vehicle_type_clause(vehicle_type),
        )
    )
    return [int(c) for c in rows]


async def estimate_task(
    db: AsyncSession, task_id: str, vehicle_type: VehicleType | None
) -> CostEstimate | None:
    """Bir bakım görevinin tamirciye tahmini maliyeti (tohum + topluluk)."""
    seed = seed_task_band(task_id, vehicle_type)
    costs = await _task_costs(db, task_id, vehicle_type)
    return _blend(seed, costs)


async def estimate_system(
    db: AsyncSession, ariza_sistem: str, vehicle_type: VehicleType | None
) -> CostEstimate | None:
    """Bir arıza sisteminin (teşhis) tamirciye tahmini maliyeti."""
    seed = seed_system_band(ariza_sistem, vehicle_type)
    costs = await _system_costs(db, ariza_sistem, vehicle_type)
    return _blend(seed, costs)
