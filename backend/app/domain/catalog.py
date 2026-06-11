"""TR araç parkı bakım kataloğu (seed/örnek veri).

Türkiye'de yaygın araçlar için yağ/filtre/akü gibi bakım verilerini tutar.
Araç oluştururken kullanıcı `spec` vermezse buradan otomatik doldurulur.

⚠️ Bu değerler ÖRNEK seed verisidir. Üretimde araç kullanım kılavuzuna ve
yetkili katalog parça numaralarına karşı doğrulanmalıdır. AI rehberliği bu
verileri "kesin" değil referans olarak kullanır.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .enums import FuelType
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
)


def find_spec(
    make: str,
    model: str,
    year: int,
    *,
    fuel_type: FuelType | None = None,
    engine_code: str | None = None,
) -> VehicleSpecIn | None:
    """Katalogda eşleşen aracın spec'ini döndürür; yoksa None.

    Eşleşme önceliği: motor kodu > yakıt türü > yıl aralığı.
    """
    make_n, model_n = make.strip().casefold(), model.strip().casefold()
    engine_n = engine_code.strip().casefold() if engine_code else None

    candidates = [
        e
        for e in CATALOG
        if e.make.casefold() == make_n
        and e.model.casefold() == model_n
        and e.year_min <= year <= e.year_max
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
