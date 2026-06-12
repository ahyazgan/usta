"""Hazırlık listesi — DIY için "başlamadan önce ne lazım?".

Bir bakım görevi için, aracın spec'inden (katalog) ilgili **parça numaralarını**
çıkarır. Aletler rehber adımlarından (mobil tarafında) toplanır; burada yalnızca
araca özel parça/sarf bilgisi var. Boş (None) alanlar atlanır.

İleride parça-affiliate gelirinin de temeli: her parça → satın-al bağlantısı.
"""

from __future__ import annotations

# task_id -> [(spec_key, label_tr, label_en)]; sıra mobilde gösterim sırasıdır.
_PREP_FIELDS: dict[str, list[tuple[str, str, str]]] = {
    "oil_change": [
        ("oil_spec", "Motor yağı", "Engine oil"),
        ("oil_capacity_l", "Yağ kapasitesi (L)", "Oil capacity (L)"),
        ("oil_filter_part", "Yağ filtresi", "Oil filter"),
        ("oil_drain_bolt_size", "Karter tıpası ölçüsü", "Drain bolt size"),
    ],
    "spark_plug": [("spark_plug_part", "Buji", "Spark plug")],
    "air_filter": [("air_filter_part", "Hava filtresi", "Air filter")],
    "cabin_filter": [("cabin_filter_part", "Polen filtresi", "Cabin filter")],
    "battery": [("battery_spec", "Akü", "Battery")],
}


def prep_parts_for_task(task_id: str, spec_values: dict[str, object]) -> list[dict[str, str]]:
    """Göreve özel parça listesi (araç spec'inden doldurulmuş; boş alanlar atlanır)."""
    out: list[dict[str, str]] = []
    for key, label_tr, label_en in _PREP_FIELDS.get(task_id, []):
        val = spec_values.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            continue
        out.append({"label_tr": label_tr, "label_en": label_en, "value": str(val)})
    return out
