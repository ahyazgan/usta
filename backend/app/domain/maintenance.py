"""Bakım hatırlatma mantığı (km bazlı, saf fonksiyonlar).

Son bakım kaydının km'si + servis aralığı + güncel km'den bir sonraki bakımın
ne zaman geldiğini hesaplar. Zaman bazlı (örn. akü yaşı) hatırlatmalar MVP'de yok.
"""

from __future__ import annotations

from dataclasses import dataclass

from .enums import ReminderStatus

# Görev -> servis aralığı (km). Sadece km bazlı görevler.
# (battery/wiper/headlight zaman/duruma bağlıdır; km hatırlatıcısı üretilmez.)
TASK_INTERVALS_KM: dict[str, int] = {
    "oil_change": 15_000,
    "cabin_filter": 15_000,
    "air_filter": 30_000,
    "spark_plug": 60_000,
    "coolant": 60_000,
    "brake_check": 20_000,  # kontrol aralığı (değişim değil)
    "tire": 10_000,  # rotasyon/kontrol aralığı
}

# Kalan km bu eşiğin altındaysa "yaklaşıyor".
SOON_THRESHOLD_KM = 2_000


@dataclass(slots=True, frozen=True)
class Reminder:
    task: str
    interval_km: int
    last_km: int | None
    due_km: int | None
    remaining_km: int | None
    status: ReminderStatus


def compute_reminders(current_km: int | None, last_km_by_task: dict[str, int]) -> list[Reminder]:
    """Her km bazlı görev için hatırlatma üretir.

    last_km_by_task: görev -> o görevin EN SON kaydındaki km.
    """
    reminders: list[Reminder] = []
    for task, interval in TASK_INTERVALS_KM.items():
        last_km = last_km_by_task.get(task)
        if last_km is None or current_km is None:
            reminders.append(
                Reminder(task, interval, last_km, None, None, ReminderStatus.unknown)
            )
            continue
        due_km = last_km + interval
        remaining = due_km - current_km
        if remaining <= 0:
            status = ReminderStatus.due
        elif remaining <= SOON_THRESHOLD_KM:
            status = ReminderStatus.soon
        else:
            status = ReminderStatus.ok
        reminders.append(Reminder(task, interval, last_km, due_km, remaining, status))
    return reminders
