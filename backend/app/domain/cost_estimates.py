"""Tamir/bakım maliyet tahmini — TR pazarı tohum bantları.

Unicorn wedge'inin temeli: kullanıcı "bu iş tamirciye ne tutar?" sorusunun
cevabını burada bulur. Başta tohum (kural-tabanlı) bantlar kullanılır; kullanıcılar
gerçek ödedikleri tutarı (`MaintenanceLog.cost_try`) girdikçe `cost_service`
bu tohumları **topluluk verisiyle** keskinleştirir → kopyalanamaz fiyat hendeği.

⚠️ Bantlar ÖRNEK seed (TL, tamirciye tam iş — işçilik + parça). Bölgeye/araca göre
değişir; "kesin fiyat" değil **referans aralık**tır. Topluluk verisi biriktikçe
gerçeğe yakınsar.
"""

from __future__ import annotations

from dataclasses import dataclass

from .enums import ArizaSistem, VehicleType


@dataclass(slots=True, frozen=True)
class CostBand:
    low: int
    high: int


# Bakım görevi → tamirciye tahmini tam iş (araba taban fiyatı, TL).
_TASK_BANDS: dict[str, CostBand] = {
    "oil_change": CostBand(800, 1800),
    "spark_plug": CostBand(700, 1900),
    "battery": CostBand(1500, 4500),
    "brake_check": CostBand(1000, 3500),
    "air_filter": CostBand(400, 1200),
    "cabin_filter": CostBand(400, 1200),
    "coolant": CostBand(600, 1800),
    "tire": CostBand(500, 2200),
    "wiper": CostBand(300, 900),
    "headlight": CostBand(400, 1500),
    # Motosiklete özel görevler — bantlar zaten moto fiyatı (çarpan UYGULANMAZ).
    "chain": CostBand(400, 1200),
    "tire_pressure": CostBand(100, 400),
    "clutch_cable": CostBand(300, 1000),
}

# Bandı zaten motosiklet fiyatı olan görevler (araç türü çarpanı uygulanmaz).
_MOTO_NATIVE_TASKS = frozenset({"chain", "tire_pressure", "clutch_cable"})

# Arıza sistemi → tamirciye tahmini tam iş (araba taban fiyatı, TL).
# Teşhis (kamera/ses) sonucundaki `ariza_sistem` ile eşleşir.
_SYSTEM_BANDS: dict[ArizaSistem, CostBand] = {
    ArizaSistem.motor: CostBand(2000, 15000),
    ArizaSistem.ates_leme: CostBand(800, 4000),
    ArizaSistem.fren: CostBand(1000, 4500),
    ArizaSistem.elektrik: CostBand(800, 6000),
    ArizaSistem.lastik: CostBand(500, 6000),
    ArizaSistem.filtre: CostBand(400, 1500),
    ArizaSistem.suspansiyon: CostBand(1500, 8000),
    ArizaSistem.sanziman: CostBand(3000, 25000),
    ArizaSistem.gorus: CostBand(300, 2500),
    ArizaSistem.diger: CostBand(500, 5000),
}

# Motosiklet, paylaşılan sistem/görevlerde arabadan ucuz — kaba çarpan.
_MOTO_MULT = 0.55


def _round50(value: float) -> int:
    """En yakın 50 TL'ye yuvarla (fiyat aralığı 'temiz' görünsün)."""
    return int(round(value / 50.0) * 50)


def _scale(band: CostBand, mult: float) -> CostBand:
    return CostBand(_round50(band.low * mult), _round50(band.high * mult))


def seed_task_band(task_id: str, vehicle_type: VehicleType | None) -> CostBand | None:
    """Bir bakım görevinin tohum maliyet bandı (araç türüne göre ölçekli)."""
    band = _TASK_BANDS.get(task_id)
    if band is None:
        return None
    if vehicle_type == VehicleType.motosiklet and task_id not in _MOTO_NATIVE_TASKS:
        return _scale(band, _MOTO_MULT)
    return band


def seed_system_band(
    ariza_sistem: ArizaSistem | str, vehicle_type: VehicleType | None
) -> CostBand | None:
    """Bir arıza sisteminin tohum maliyet bandı (teşhis için, araç türüne göre)."""
    if isinstance(ariza_sistem, str):
        try:
            ariza_sistem = ArizaSistem(ariza_sistem)
        except ValueError:
            return None
    band = _SYSTEM_BANDS.get(ariza_sistem)
    if band is None:
        return None
    if vehicle_type == VehicleType.motosiklet:
        return _scale(band, _MOTO_MULT)
    return band
