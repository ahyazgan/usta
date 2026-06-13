"""Canlı sesli rehber — oturum 'system instruction' kurucusu.

Gemini Live (ya da herhangi bir realtime sağlayıcı) için canlı asistanın
"beynini" hazırlar: güvenlik kuralları + araç bağlamı + (varsa) görev adımları +
parçalar + fiyat aralığı. İçerik SAĞLAYICI-BAĞIMSIZ; ileride ephemeral token /
oturum config bu metni server-side gömecek (istemciye sızdırılmaz).

Yeni AI üretimi YOK; mevcut katalog/rehber/güvenlik/fiyat verisini metne dizer.
"""

from __future__ import annotations

from ...domain.cost_estimates import seed_task_band
from ...domain.enums import VehicleType
from ...domain.guides import fill_template, get_guide
from ...domain.models import Vehicle
from ...domain.prep import prep_parts_for_task
from ...domain.tasks import get_task
from .prompts import _read, vehicle_context

# Görsel rehberde anlamlı olan spec alanları (vehicle_context ile aynı kaynak).
_SPEC_KEYS = (
    "oil_spec", "oil_capacity_l", "oil_drain_bolt_size", "oil_filter_part",
    "air_filter_part", "cabin_filter_part", "spark_plug_part",
    "battery_spec", "battery_location",
)


def _spec_values(vehicle: Vehicle) -> dict[str, object]:
    spec = vehicle.spec
    if spec is None:
        return {}
    return {key: getattr(spec, key, None) for key in _SPEC_KEYS}


def _task_section(vehicle: Vehicle, task_id: str) -> str | None:
    """Görev verildiyse: başlık + adımlar (spec dolu) + parçalar + fiyat."""
    task = get_task(task_id)
    guide = get_guide(task_id)
    if task is None or guide is None:
        return None

    spec_values = _spec_values(vehicle)
    lines = [
        "## MEVCUT GÖREV",
        f"- İş: {task.title_tr} (yaklaşık {guide.est_minutes} dk)",
        "- Adımlar (kullanıcıyı bunlarla sözlü yürüt, tek seferde bir adım):",
    ]
    for i, s in enumerate(guide.steps, start=1):
        lines.append(f"  {i}. {fill_template(s.instruction_tr, spec_values, 'tr')}")

    parts = prep_parts_for_task(task_id, spec_values)
    if parts:
        lines.append("- Gerekli parçalar (araca özel): " + ", ".join(
            f"{p['label_tr']}: {p['value']}" for p in parts
        ))

    band = seed_task_band(task_id, vehicle.vehicle_type or VehicleType.araba)
    if band is not None:
        lines.append(
            f"- Tamirciye tahmini maliyet: ~{band.low}-{band.high} TL "
            "(sorulursa söyle; kesin değil)."
        )
    lines.append(f"- Güvenlik notu: {guide.mechanic_note_tr}")
    return "\n".join(lines)


def build_live_system_instruction(vehicle: Vehicle, task_id: str | None = None) -> str:
    """Canlı oturumun system instruction'ı: güvenlik + araç + (varsa) görev.

    Sağlayıcı-bağımsız; realtime oturum config'ine gömülür (istemciye verilmez).
    """
    sections = [vehicle_context(vehicle), _read("live/_base.md")]
    if task_id:
        task_section = _task_section(vehicle, task_id)
        if task_section is not None:
            sections.append(task_section)
    return "\n\n".join(sections)
