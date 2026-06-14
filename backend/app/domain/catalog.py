"""TR + global araç parkı bakım kataloğu.

Araç verisi koddan AYRILMIŞTIR: tüm kayıtlar `catalog_data.json` içinde saf veri
olarak tutulur; bu modül yalnızca onu okuyup `CatalogEntry` nesnelerine çevirir.
Yeni araç eklemek için JSON'a bir satır eklemek yeterlidir — Python sözdizimi
gerekmez. Geçersiz/bozuk bir kayıt sessizce ATLANIR (tüm katalog çökmesin diye).

⚠️ Veriler KARIŞIK güvendedir:
- Bazı specler (yağ vizkozitesi/kapasite, buji tipi, akü) en çok satan modeller
  için web kaynaklarından doğrulandı — "örnek:" ön eki YOK.
- "örnek:" ön ekli değerler (özellikle filtre OE parça no'ları) hâlâ YER TUTUCU;
  üretimde araç el kitabına / yetkili parça kataloğuna karşı doğrulanmalı.
NOT: Tek-girdi-per-model yapısı motor varyantını (yıl/facelift) tam yakalayamaz;
gerçek OE parça uyumluluğu için harici parça verisi (perakendeci/TecDoc) gerekir.
AI rehberliği bu verileri "kesin" değil referans olarak kullanır.

LPG'li benzinli araçlarda LPG sistemine müdahale TARİFİ verilmez; katalog yalnızca
temel bakım verisini taşır.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from .enums import FuelType, VehicleType
from .schemas import VehicleSpecIn

logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).with_name("catalog_data.json")


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


def _parse_entry(raw: dict) -> CatalogEntry:
    """Bir JSON kaydını CatalogEntry'ye çevirir. Eksik/yanlış alan ValueError/
    KeyError fırlatır; çağıran tarafta yakalanıp o kayıt atlanır."""
    return CatalogEntry(
        make=raw["make"],
        model=raw["model"],
        year_min=int(raw["year_min"]),
        year_max=int(raw["year_max"]),
        spec=VehicleSpecIn.model_validate(raw.get("spec") or {}),
        fuels=tuple(FuelType(f) for f in raw.get("fuels", ())),
        engine_codes=tuple(raw.get("engine_codes", ())),
        vehicle_type=VehicleType(raw.get("vehicle_type", VehicleType.araba.value)),
    )


def _load_catalog() -> tuple[CatalogEntry, ...]:
    """catalog_data.json'u okuyup CatalogEntry tuple'ı döndürür. Bozuk tek bir
    kayıt tüm kataloğu düşürmesin: geçersiz kayıt loglanıp atlanır."""
    try:
        raw_rows = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.exception("Katalog veri dosyası okunamadı: %s", _DATA_FILE)
        return ()

    entries: list[CatalogEntry] = []
    for i, raw in enumerate(raw_rows):
        try:
            entries.append(_parse_entry(raw))
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Katalog kaydı atlandı (index %d): %s", i, exc)
    return tuple(entries)


CATALOG: tuple[CatalogEntry, ...] = _load_catalog()


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
