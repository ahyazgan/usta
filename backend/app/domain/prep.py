"""Hazırlık listesi — DIY için "başlamadan önce ne lazım?".

Bir bakım görevi için, aracın spec'inden (katalog) ilgili **parça numaralarını**
çıkarır. Aletler rehber adımlarından (mobil tarafında) toplanır; burada yalnızca
araca özel parça/sarf bilgisi var. Boş (None) alanlar atlanır.

İleride parça-affiliate gelirinin de temeli: her parça → satın-al bağlantısı.
"""

from __future__ import annotations

from urllib.parse import quote

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


def build_buy_url(value: str, label: str, template: str) -> str | None:
    """Parça için "Satın Al" linki (affiliate iskeleti).

    template '{q}' içerir; sorgu = temizlenmiş değer + etiket. Şablon boşsa None.
    "örnek:" ön eki sorgudan çıkarılır (gerçek parça no'su/adı aranır).
    """
    if not template:
        return None
    clean = value.split("örnek:")[-1].strip() if "örnek:" in value else value.strip()
    query = f"{clean} {label}".strip()
    return template.replace("{q}", quote(query))


def prep_parts_for_task(
    task_id: str, spec_values: dict[str, object], buy_url_template: str = ""
) -> list[dict[str, str | None]]:
    """Göreve özel parça listesi (araç spec'inden doldurulmuş; boş alanlar atlanır).

    buy_url_template verilirse her parçaya bir "Satın Al" linki eklenir.
    """
    out: list[dict[str, str | None]] = []
    for key, label_tr, label_en in _PREP_FIELDS.get(task_id, []):
        val = spec_values.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            continue
        out.append(
            {
                "label_tr": label_tr,
                "label_en": label_en,
                "value": str(val),
                "buy_url": build_buy_url(str(val), label_tr, buy_url_template),
            }
        )
    return out
