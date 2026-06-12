"""Bakım görevi kayıt defteri.

Her görev bir vision prompt dosyasına bağlıdır ve hangi yakıt türlerine
uygulanabileceğini belirtir (örn. buji dizelde yok, yağ değişimi elektrikte yok).
Mobil uygulama araca özel görev listesini buradan türetir.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .enums import Aciliyet, FuelType, VehicleType


@dataclass(slots=True, frozen=True)
class MaintenanceTask:
    id: str
    title_tr: str
    title_en: str
    risk: Aciliyet
    prompt_file: str  # backend/prompts/ altına görelidir
    # Boş demet = tüm yakıtlara uygulanır.
    applies_to_fuels: tuple[FuelType, ...] = field(default=())
    # Boş demet = tüm araç türlerine uygulanır (araba + motosiklet).
    applies_to_types: tuple[VehicleType, ...] = field(default=())
    # Bu işi kendin yapınca tasarruf edilen yaklaşık işçilik (TL) — tahmini.
    diy_saving_try: int = 0


_ALL_COMBUSTION = (FuelType.benzin, FuelType.dizel, FuelType.lpg, FuelType.hibrit)
_SPARK = (FuelType.benzin, FuelType.lpg, FuelType.hibrit)  # bujili motorlar
_CAR_ONLY = (VehicleType.araba,)
_MOTO_ONLY = (VehicleType.motosiklet,)

TASKS: tuple[MaintenanceTask, ...] = (
    MaintenanceTask(
        "oil_change", "Yağ Değişimi", "Oil Change", Aciliyet.orta,
        "vision/oil_change.md", applies_to_fuels=_ALL_COMBUSTION,  # elektrikte yağ yok
        diy_saving_try=400,
    ),
    MaintenanceTask(
        "spark_plug", "Buji Değişimi", "Spark Plug", Aciliyet.orta,
        "vision/spark_plug.md", applies_to_fuels=_SPARK,  # dizel/elektrikte buji yok
        diy_saving_try=350,
    ),
    MaintenanceTask(
        "battery", "Akü Kontrolü", "Battery Check", Aciliyet.yuksek,
        "vision/battery.md",  # tüm yakıtlar (elektrikte de 12V akü var)
        diy_saving_try=250,
    ),
    MaintenanceTask(
        "brake_check", "Fren Kontrolü", "Brake Check", Aciliyet.yuksek,
        "vision/brake_check.md",  # tüm yakıtlar; güvenlik-kritik, kontrol odaklı
        diy_saving_try=500,
    ),
    MaintenanceTask(
        "air_filter", "Hava Filtresi", "Air Filter", Aciliyet.dusuk,
        "vision/air_filter.md", applies_to_fuels=_ALL_COMBUSTION,  # elektrikte motor hava filtresi yok
        diy_saving_try=200,
    ),
    MaintenanceTask(
        "cabin_filter", "Polen Filtresi", "Cabin Filter", Aciliyet.dusuk,
        "vision/cabin_filter.md", applies_to_types=_CAR_ONLY,  # motosiklette kabin yok
        diy_saving_try=200,
    ),
    MaintenanceTask(
        "coolant", "Soğutma Sıvısı", "Coolant", Aciliyet.yuksek,
        "vision/coolant.md", applies_to_fuels=_ALL_COMBUSTION,  # elektrikte motor soğutması farklı
        diy_saving_try=250,
    ),
    MaintenanceTask(
        "tire", "Lastik Kontrolü", "Tire Check", Aciliyet.orta,
        "vision/tire.md",  # tüm yakıtlar; güvenlik-ilgili
        diy_saving_try=150,
    ),
    MaintenanceTask(
        "wiper", "Silecek", "Wiper Blades", Aciliyet.dusuk,
        "vision/wiper.md", applies_to_types=_CAR_ONLY,  # motosiklette silecek yok
        diy_saving_try=100,
    ),
    MaintenanceTask(
        "headlight", "Far / Ampul", "Headlight", Aciliyet.orta,
        "vision/headlight.md",  # tüm araçlar
        diy_saving_try=200,
    ),
    MaintenanceTask(
        "chain", "Zincir Bakımı", "Chain Maintenance", Aciliyet.orta,
        "vision/chain.md", applies_to_types=_MOTO_ONLY,  # yalnızca motosiklet
        diy_saving_try=150,
    ),
    MaintenanceTask(
        "tire_pressure", "Lastik Basıncı", "Tire Pressure", Aciliyet.orta,
        "vision/tire_pressure.md", applies_to_types=_MOTO_ONLY,
        diy_saving_try=50,
    ),
    MaintenanceTask(
        "clutch_cable", "Debriyaj Teli", "Clutch Cable", Aciliyet.orta,
        "vision/clutch_cable.md", applies_to_types=_MOTO_ONLY,
        diy_saving_try=150,
    ),
)

_BY_ID = {t.id: t for t in TASKS}


def get_tasks() -> tuple[MaintenanceTask, ...]:
    return TASKS


def get_task(task_id: str) -> MaintenanceTask | None:
    return _BY_ID.get(task_id)


def tasks_for_fuel(fuel: FuelType) -> tuple[MaintenanceTask, ...]:
    """Bir yakıt türüne uygulanabilir görevleri döndürür (geriye dönük)."""
    return tuple(t for t in TASKS if not t.applies_to_fuels or fuel in t.applies_to_fuels)


def tasks_for_vehicle(
    fuel: FuelType, vehicle_type: VehicleType | None
) -> tuple[MaintenanceTask, ...]:
    """Bir aracın yakıtına VE türüne uygulanabilir görevler.

    vehicle_type None ise (eski kayıtlar) araba kabul edilir.
    """
    vtype = vehicle_type or VehicleType.araba
    return tuple(
        t
        for t in TASKS
        if (not t.applies_to_fuels or fuel in t.applies_to_fuels)
        and (not t.applies_to_types or vtype in t.applies_to_types)
    )
