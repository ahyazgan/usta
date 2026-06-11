"""Prompt yükleyici — AI prompt'ları backend/prompts/ altında ayrı dosyalarda."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ...domain.models import Vehicle

# backend/prompts dizini (bu dosya: backend/app/services/ai/prompts.py)
PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"


@lru_cache(maxsize=64)
def _read(relative: str) -> str:
    path = PROMPTS_DIR / relative
    return path.read_text(encoding="utf-8")


def vehicle_context(vehicle: Vehicle) -> str:
    """Araç bağlamını prompt'un başına yerleştirilecek metne çevirir."""
    spec = vehicle.spec
    lines = [
        "## ARAÇ BAĞLAMI",
        f"- Marka/Model/Yıl: {vehicle.make} {vehicle.model} {vehicle.year}",
        f"- Motor kodu: {vehicle.engine_code or 'bilinmiyor'}",
        f"- Yakıt: {vehicle.fuel_type.value}",
        f"- Güncel KM: {vehicle.current_km if vehicle.current_km is not None else 'bilinmiyor'}",
    ]
    if spec is not None:
        lines += [
            f"- Yağ spesifikasyonu: {spec.oil_spec or 'bilinmiyor'} ({spec.oil_capacity_l or '?'} L)",
            f"- Yağ tıpası ölçüsü: {spec.oil_drain_bolt_size or 'bilinmiyor'}",
            f"- Yağ tıpası konumu: {spec.oil_drain_location or 'bilinmiyor'}",
            f"- Yağ filtresi: {spec.oil_filter_part or 'bilinmiyor'}",
            f"- Buji: {spec.spark_plug_part or 'bilinmiyor'}",
            f"- Akü: {spec.battery_spec or 'bilinmiyor'} ({spec.battery_location or 'konum bilinmiyor'})",
        ]
    return "\n".join(lines)


def build_vision_prompt(vehicle: Vehicle, task: str, step: int | None) -> str:
    """_base + göreve özel prompt'u araç bağlamıyla birleştirir."""
    base = _read("vision/_base.md")
    task_file = f"vision/{task}.md"
    try:
        task_prompt = _read(task_file)
    except FileNotFoundError:
        task_prompt = "## GÖREV\nGenel kamera doğrulaması."
    step_line = f"\n## MEVCUT ADIM\nKullanıcı {step}. adımda." if step else ""
    return f"{vehicle_context(vehicle)}\n\n{base}\n\n{task_prompt}{step_line}"


def build_audio_prompt(vehicle: Vehicle) -> str:
    base = _read("audio/_base.md")
    return f"{vehicle_context(vehicle)}\n\n{base}"
