"""Bakım görevi kayıt defteri.

Her görev bir vision prompt dosyasına bağlıdır. Mobil uygulama görev listesini
buradan (GET /v1/tasks) alır; prompt dosyalarıyla senkron kalır.
"""

from __future__ import annotations

from dataclasses import dataclass

from .enums import Aciliyet


@dataclass(slots=True, frozen=True)
class MaintenanceTask:
    id: str
    title_tr: str
    title_en: str
    risk: Aciliyet
    prompt_file: str  # backend/prompts/ altına görelidir


TASKS: tuple[MaintenanceTask, ...] = (
    MaintenanceTask("oil_change", "Yağ Değişimi", "Oil Change", Aciliyet.orta, "vision/oil_change.md"),
    MaintenanceTask("battery", "Akü Kontrolü", "Battery Check", Aciliyet.yuksek, "vision/battery.md"),
    MaintenanceTask("cabin_filter", "Polen Filtresi", "Cabin Filter", Aciliyet.dusuk, "vision/cabin_filter.md"),
)

_BY_ID = {t.id: t for t in TASKS}


def get_tasks() -> tuple[MaintenanceTask, ...]:
    return TASKS


def get_task(task_id: str) -> MaintenanceTask | None:
    return _BY_ID.get(task_id)
