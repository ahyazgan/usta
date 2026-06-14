"""Arıza taksonomisi eşlemesi.

Teşhisleri (görev id'si veya ses kategorisi) sorgulanabilir bir araç sistemine
(`ArizaSistem`) eşler. Veri hendeğinin istatistik katmanı bunun üzerine kurulur
(örn. "motor şikâyetleri 90.000 km'de artıyor").
"""

from __future__ import annotations

from .enums import ArizaSistem

# Görsel teşhis: görev id -> sistem.
_TASK_TO_SISTEM: dict[str, ArizaSistem] = {
    "oil_change": ArizaSistem.motor,
    "coolant": ArizaSistem.motor,
    "spark_plug": ArizaSistem.ates_leme,
    "battery": ArizaSistem.elektrik,
    "headlight": ArizaSistem.elektrik,
    "brake_check": ArizaSistem.fren,
    "air_filter": ArizaSistem.filtre,
    "cabin_filter": ArizaSistem.filtre,
    "tire": ArizaSistem.lastik,
    "wiper": ArizaSistem.gorus,
}

# Ses teşhisi: ses kategorisi -> sistem.
_SES_TO_SISTEM: dict[str, ArizaSistem] = {
    "tikirti": ArizaSistem.motor,
    "kayis_sesi": ArizaSistem.sanziman,
    "metalik_vuruntu": ArizaSistem.motor,
    "islik": ArizaSistem.motor,
    "egzoz_patlamasi": ArizaSistem.ates_leme,
    "normal": ArizaSistem.diger,
    "belirsiz": ArizaSistem.diger,
}


def sistem_for_task(task_id: str) -> ArizaSistem:
    return _TASK_TO_SISTEM.get(task_id, ArizaSistem.diger)


def sistem_for_ses(ses_kategorisi: str) -> ArizaSistem:
    return _SES_TO_SISTEM.get(ses_kategorisi, ArizaSistem.diger)
