"""Canlı sesli rehber — oturum 'system instruction' + config kurucusu (TR + EN).

Gemini Live (ya da herhangi bir realtime sağlayıcı) için canlı asistanın
"beynini" hazırlar: güvenlik kuralları + araç bağlamı + (varsa) görev adımları +
parçalar + fiyat + sağlanan araçlar (tool). İçerik SAĞLAYICI-BAĞIMSIZ; oturum
config server-side gömülür (system instruction istemciye sızdırılmaz).

Yeni AI üretimi YOK; mevcut katalog/rehber/güvenlik/fiyat verisini metne dizer.
"""

from __future__ import annotations

from typing import Literal

from ...domain.cost_estimates import seed_task_band
from ...domain.enums import VehicleType
from ...domain.guides import fill_template, get_guide
from ...domain.models import Vehicle
from ...domain.prep import prep_parts_for_task
from ...domain.tasks import get_task
from .prompts import _read

Lang = Literal["tr", "en"]

_SPEC_KEYS = (
    "oil_spec", "oil_capacity_l", "oil_drain_bolt_size", "oil_filter_part",
    "air_filter_part", "cabin_filter_part", "spark_plug_part",
    "battery_spec", "battery_location",
)

# Bölüm etiketleri (tr/en).
_T = {
    "tr": {
        "ctx": "## ARAÇ BAĞLAMI",
        "vehicle": "Marka/Model/Yıl",
        "engine": "Motor kodu",
        "fuel": "Yakıt",
        "km": "Güncel KM",
        "unknown": "bilinmiyor",
        "oil": "Yağ",
        "drain": "Yağ tıpası",
        "oilfilter": "Yağ filtresi",
        "plug": "Buji",
        "battery": "Akü",
        "task": "## MEVCUT GÖREV",
        "job": "İş",
        "approx_min": "yaklaşık {m} dk",
        "steps": "Adımlar (kullanıcıyı bunlarla sözlü yürüt, tek seferde bir adım)",
        "parts": "Gerekli parçalar (araca özel)",
        "cost": "Tamirciye tahmini maliyet: ~{lo}-{hi} TL (sorulursa söyle; kesin değil).",
        "safety": "Güvenlik notu",
    },
    "en": {
        "ctx": "## VEHICLE CONTEXT",
        "vehicle": "Make/Model/Year",
        "engine": "Engine code",
        "fuel": "Fuel",
        "km": "Current km",
        "unknown": "unknown",
        "oil": "Oil",
        "drain": "Drain bolt",
        "oilfilter": "Oil filter",
        "plug": "Spark plug",
        "battery": "Battery",
        "task": "## CURRENT TASK",
        "job": "Job",
        "approx_min": "about {m} min",
        "steps": "Steps (walk the user through these out loud, one step at a time)",
        "parts": "Required parts (vehicle-specific)",
        "cost": "Estimated mechanic cost: ~{lo}-{hi} TL (mention if asked; not exact).",
        "safety": "Safety note",
    },
}


def _vehicle_context(vehicle: Vehicle, lang: Lang) -> str:
    t = _T[lang]
    spec = vehicle.spec
    lines = [
        t["ctx"],
        f"- {t['vehicle']}: {vehicle.make} {vehicle.model} {vehicle.year}",
        f"- {t['engine']}: {vehicle.engine_code or t['unknown']}",
        f"- {t['fuel']}: {vehicle.fuel_type.value}",
        f"- {t['km']}: {vehicle.current_km if vehicle.current_km is not None else t['unknown']}",
    ]
    if spec is not None:
        lines += [
            f"- {t['oil']}: {spec.oil_spec or t['unknown']} ({spec.oil_capacity_l or '?'} L)",
            f"- {t['drain']}: {spec.oil_drain_bolt_size or t['unknown']} "
            f"({spec.oil_drain_location or t['unknown']})",
            f"- {t['oilfilter']}: {spec.oil_filter_part or t['unknown']}",
            f"- {t['plug']}: {spec.spark_plug_part or t['unknown']}",
            f"- {t['battery']}: {spec.battery_spec or t['unknown']} "
            f"({spec.battery_location or t['unknown']})",
        ]
    return "\n".join(lines)


def _spec_values(vehicle: Vehicle) -> dict[str, object]:
    spec = vehicle.spec
    if spec is None:
        return {}
    return {key: getattr(spec, key, None) for key in _SPEC_KEYS}


def _task_section(vehicle: Vehicle, task_id: str, lang: Lang) -> str | None:
    task = get_task(task_id)
    guide = get_guide(task_id)
    if task is None or guide is None:
        return None
    t = _T[lang]
    spec_values = _spec_values(vehicle)
    title = task.title_tr if lang == "tr" else task.title_en
    note = guide.mechanic_note_tr if lang == "tr" else guide.mechanic_note_en

    lines = [
        t["task"],
        f"- {t['job']}: {title} ({t['approx_min'].format(m=guide.est_minutes)})",
        f"- {t['steps']}:",
    ]
    for i, s in enumerate(guide.steps, start=1):
        instr = s.instruction_tr if lang == "tr" else s.instruction_en
        lines.append(f"  {i}. {fill_template(instr, spec_values, lang)}")

    parts = prep_parts_for_task(task_id, spec_values)
    if parts:
        label_key = "label_tr" if lang == "tr" else "label_en"
        lines.append(
            f"- {t['parts']}: " + ", ".join(f"{p[label_key]}: {p['value']}" for p in parts)
        )

    band = seed_task_band(task_id, vehicle.vehicle_type or VehicleType.araba)
    if band is not None:
        lines.append("- " + t["cost"].format(lo=band.low, hi=band.high))
    lines.append(f"- {t['safety']}: {note}")
    return "\n".join(lines)


def build_live_system_instruction(
    vehicle: Vehicle, task_id: str | None = None, lang: Lang = "tr"
) -> str:
    """Canlı oturumun system instruction'ı: güvenlik + araç + (varsa) görev."""
    base = _read("live/_base.en.md" if lang == "en" else "live/_base.md")
    sections = [_vehicle_context(vehicle, lang), base]
    if task_id:
        section = _task_section(vehicle, task_id, lang)
        if section is not None:
            sections.append(section)
    return "\n\n".join(sections)


def tool_declarations(lang: Lang = "tr") -> list[dict]:
    """Canlı asistanın çağırabileceği araçlar (Gemini function declarations).

    Yürütme istemcide olur (mevcut REST uçlarımıza çevrilir): bunlar yalnızca
    şema bildirimi. Sistem değerleri ArizaSistem enum'una eşlenir.
    """
    sistem_desc = (
        "Araç sistemi: motor, atesleme, fren, elektrik, lastik, filtre, "
        "suspansiyon, sanziman, gorus, diger"
        if lang == "tr"
        else "Vehicle system: motor, atesleme, fren, elektrik, lastik, filtre, "
        "suspansiyon, sanziman, gorus, diger"
    )
    return [
        {
            "name": "fiyat_tahmini",
            "description": (
                "Bir arıza sistemi için tamirciye tahmini maliyet aralığını getirir."
                if lang == "tr"
                else "Get the estimated mechanic cost range for a fault system."
            ),
            "parameters": {
                "type": "object",
                "properties": {"ariza_sistem": {"type": "string", "description": sistem_desc}},
                "required": ["ariza_sistem"],
            },
        },
        {
            "name": "tamirci_bul",
            "description": (
                "Kullanıcının şehrinde, ilgili sisteme bakan doğrulanmış tamircileri getirir."
                if lang == "tr"
                else "Find verified mechanics in the user's city for the relevant system."
            ),
            "parameters": {
                "type": "object",
                "properties": {"ariza_sistem": {"type": "string", "description": sistem_desc}},
                "required": ["ariza_sistem"],
            },
        },
    ]


def build_session_config(
    vehicle: Vehicle,
    *,
    task_id: str | None,
    lang: Lang,
    model: str,
    voice: str,
) -> dict:
    """Realtime oturum config'i (system instruction dahil; server-side kullanılır).

    Ephemeral token üretirken bu config Google'a bağlanır; istemciye yalnızca
    token + güvenli alanlar döner (system_instruction değil).
    """
    return {
        "model": model,
        "voice": voice,
        "language": lang,
        "system_instruction": build_live_system_instruction(vehicle, task_id, lang),
        "tools": tool_declarations(lang),
    }
