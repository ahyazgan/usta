"""Teşhis yanıtına fiyat tahmini iliştirme yardımcısı.

Hem görüntü hem ses teşhisi, `ariza_sistem` türetildikten sonra bunu çağırır:
sistem + araç türüne göre tamirci maliyet aralığını (tohum/topluluk) üretir.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.enums import VehicleType
from ...domain.schemas import CostEstimateOut
from .. import cost_service


async def build_cost_estimate(
    db: AsyncSession, ariza_sistem: str | None, vehicle_type: VehicleType | None
) -> CostEstimateOut | None:
    """Arıza sistemine göre fiyat tahmini (yoksa None)."""
    if not ariza_sistem:
        return None
    est = await cost_service.estimate_system(db, ariza_sistem, vehicle_type)
    if est is None:
        return None
    return CostEstimateOut(
        low_try=est.low_try,
        high_try=est.high_try,
        source=est.source,
        sample_size=est.sample_size,
    )
