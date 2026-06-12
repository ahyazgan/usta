"""TR araç parkı bakım kataloğu (seed/örnek veri).

Türkiye'de yaygın araçlar için yağ/filtre/akü gibi bakım verilerini tutar.
Araç oluştururken kullanıcı `spec` vermezse buradan otomatik doldurulur.

⚠️ Bu değerler ÖRNEK seed verisidir. Üretimde araç kullanım kılavuzuna ve
yetkili katalog parça numaralarına karşı doğrulanmalıdır. AI rehberliği bu
verileri "kesin" değil referans olarak kullanır.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .enums import FuelType, VehicleType
from .schemas import VehicleSpecIn


@dataclass(slots=True, frozen=True)
class CatalogEntry:
    make: str
    model: str
    year_min: int
    year_max: int
    spec: VehicleSpecIn
    fuels: tuple[FuelType, ...] = field(default=())
    engine_codes: tuple[str, ...] = field(default=())
    vehicle_type: VehicleType = VehicleType.araba


# Not: LPG'li benzinli araçlarda LPG sistemine müdahale TARİFİ verilmez;
# katalog yalnızca temel bakım verisini taşır.
CATALOG: tuple[CatalogEntry, ...] = (
    CatalogEntry(
        make="Fiat",
        model="Egea",
        year_min=2015,
        year_max=2024,
        fuels=(FuelType.benzin, FuelType.lpg),
        engine_codes=("843A1000",),
        spec=VehicleSpecIn(
            oil_spec="5W-40",
            oil_capacity_l=4.0,
            oil_drain_bolt_size="14mm",
            oil_drain_location="yağ karteri alt-arka köşe",
            oil_filter_part="örnek: 55256470",
            air_filter_part="örnek: 51897064",
            cabin_filter_part="örnek: 77367464",
            spark_plug_part="örnek: NGK ZKR7A-10",
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Fiat",
        model="Egea",
        year_min=2015,
        year_max=2024,
        fuels=(FuelType.dizel,),
        engine_codes=("198A2000", "199B1000"),
        spec=VehicleSpecIn(
            oil_spec="5W-30",
            oil_capacity_l=4.3,
            oil_drain_bolt_size="13mm",
            oil_drain_location="yağ karteri alt-arka",
            oil_filter_part="örnek: 71754237",
            air_filter_part="örnek: 51897064",
            cabin_filter_part="örnek: 77367464",
            spark_plug_part=None,  # dizel — buji yok
            battery_spec="70Ah / 630A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Renault",
        model="Clio",
        year_min=2012,
        year_max=2023,
        fuels=(FuelType.dizel,),
        engine_codes=("K9K",),
        spec=VehicleSpecIn(
            oil_spec="5W-30",
            oil_capacity_l=4.5,
            oil_drain_bolt_size="8mm iç altıgen (allen)",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 8200768927",
            air_filter_part="örnek: 165466455R",
            cabin_filter_part="örnek: 272773016R",
            spark_plug_part=None,
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sağ ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Renault",
        model="Megane",
        year_min=2016,
        year_max=2023,
        fuels=(FuelType.dizel,),
        engine_codes=("K9K",),
        spec=VehicleSpecIn(
            oil_spec="5W-30",
            oil_capacity_l=4.5,
            oil_drain_bolt_size="8mm iç altıgen (allen)",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 8200768927",
            air_filter_part="örnek: 165461376R",
            cabin_filter_part="örnek: 272773016R",
            spark_plug_part=None,
            battery_spec="70Ah / 630A",
            battery_location="motor bölmesi sağ ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Toyota",
        model="Corolla",
        year_min=2013,
        year_max=2019,
        fuels=(FuelType.benzin, FuelType.lpg),
        engine_codes=("1ZR-FAE",),
        spec=VehicleSpecIn(
            oil_spec="0W-20",
            oil_capacity_l=4.2,
            oil_drain_bolt_size="14mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 04152-YZZA1",
            air_filter_part="örnek: 17801-0T050",
            cabin_filter_part="örnek: 87139-0N010",
            spark_plug_part="örnek: Denso FK20HR11",
            battery_spec="55Ah / 470A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Dacia",
        model="Sandero",
        year_min=2013,
        year_max=2020,
        fuels=(FuelType.benzin, FuelType.lpg),
        engine_codes=("H4B", "B4D"),
        spec=VehicleSpecIn(
            oil_spec="5W-40",
            oil_capacity_l=4.0,
            oil_drain_bolt_size="10mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 152089599R",
            air_filter_part="örnek: 165465154R",
            cabin_filter_part="örnek: 272772835R",
            spark_plug_part="örnek: NGK LZKAR6AP-11",
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    # --- MOTOSİKLETLER (TR'de yaygın; değerler ÖRNEK, el kitabına karşı doğrula) ---
    CatalogEntry(
        make="Honda",
        model="CB125",
        year_min=2015,
        year_max=2024,
        fuels=(FuelType.benzin,),
        engine_codes=("JC64",),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-30",
            oil_capacity_l=1.1,
            oil_drain_bolt_size="12mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip / 15412-KGA-900",
            air_filter_part="örnek: 17211-K0G-900",
            cabin_filter_part=None,  # motosiklette kabin filtresi yok
            spark_plug_part="örnek: NGK CPR6EA-9",
            battery_spec="12V 3.5Ah (YTZ4V)",
            battery_location="sele altı",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Yamaha",
        model="YBR125",
        year_min=2008,
        year_max=2022,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-40",
            oil_capacity_l=1.0,
            oil_drain_bolt_size="17mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip (yıkanabilir)",
            air_filter_part="örnek: 3D9-E4450-00",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK CR6HSA",
            battery_spec="12V 5Ah (YB5L-B)",
            battery_location="sele altı / yan kapak",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Honda",
        model="PCX125",
        year_min=2014,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-30",
            oil_capacity_l=0.8,
            oil_drain_bolt_size="12mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip",
            air_filter_part="örnek: 17210-K35-V00",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK CPR7EA-9",
            battery_spec="12V (GTZ6V)",
            battery_location="ayak tabanı / sele altı",
            transmission_type="otomatik (CVT)",
        ),
    ),
    CatalogEntry(
        make="Yamaha",
        model="MT-25",
        year_min=2015,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-40",
            oil_capacity_l=2.4,
            oil_drain_bolt_size="14mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: 1WD-E3440-00",
            air_filter_part="örnek: 1WD-14451-00",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK CPR8EA-9",
            battery_spec="12V 7Ah (YTZ7S)",
            battery_location="sele altı",
            transmission_type="manuel",
        ),
    ),
)


def find_spec(
    make: str,
    model: str,
    year: int,
    *,
    fuel_type: FuelType | None = None,
    engine_code: str | None = None,
    vehicle_type: VehicleType | None = None,
) -> VehicleSpecIn | None:
    """Katalogda eşleşen aracın spec'ini döndürür; yoksa None.

    Eşleşme önceliği: motor kodu > yakıt türü > yıl aralığı.
    vehicle_type verilirse (None=eski çağrı) yalnızca o türdeki kayıtlar dikkate
    alınır (araba/motosiklet karışmasını önler).
    """
    make_n, model_n = make.strip().casefold(), model.strip().casefold()
    engine_n = engine_code.strip().casefold() if engine_code else None
    vtype = vehicle_type or VehicleType.araba

    candidates = [
        e
        for e in CATALOG
        if e.make.casefold() == make_n
        and e.model.casefold() == model_n
        and e.year_min <= year <= e.year_max
        and e.vehicle_type == vtype
    ]
    if not candidates:
        return None

    # Motor koduyla daralt.
    if engine_n:
        by_engine = [e for e in candidates if any(c.casefold() == engine_n for c in e.engine_codes)]
        if by_engine:
            candidates = by_engine

    # Yakıt türüyle daralt.
    if fuel_type is not None:
        by_fuel = [e for e in candidates if not e.fuels or fuel_type in e.fuels]
        if by_fuel:
            candidates = by_fuel

    return candidates[0].spec.model_copy(deep=True)
