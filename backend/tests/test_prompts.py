"""Prompt yükleyici ve görev rehberi testleri."""

from app.domain.enums import FuelType
from app.domain.models import Vehicle, VehicleSpec
from app.services.ai.prompts import build_vision_prompt, vehicle_context


def _demo_vehicle() -> Vehicle:
    v = Vehicle(make="Fiat", model="Egea", year=2019, fuel_type=FuelType.lpg, current_km=84210)
    v.engine_code = "843A1000"
    v.spec = VehicleSpec(oil_spec="5W-40", oil_capacity_l=4.0, oil_drain_bolt_size="14mm")
    return v


def test_vehicle_context_includes_core_fields():
    ctx = vehicle_context(_demo_vehicle())
    assert "Fiat Egea 2019" in ctx
    assert "843A1000" in ctx
    assert "lpg" in ctx


def test_build_vision_prompt_embeds_context_base_and_task():
    prompt = build_vision_prompt(_demo_vehicle(), task="oil_change", step=3)
    # Araç bağlamı başta
    assert prompt.index("ARAÇ BAĞLAMI") < prompt.index("JSON")
    # Taban kuralları
    assert "büyük ihtimalle" in prompt.casefold()
    assert "tamirciye" in prompt.casefold()
    # Göreve özel içerik + adım
    assert "YAĞ DEĞİŞİMİ" in prompt
    assert "3. adımda" in prompt


def test_unknown_task_falls_back_gracefully():
    prompt = build_vision_prompt(_demo_vehicle(), task="olmayan_gorev", step=None)
    assert "Genel kamera doğrulaması" in prompt


def test_battery_task_prompt_enforces_safety_language():
    prompt = build_vision_prompt(_demo_vehicle(), task="battery", step=1)
    low = prompt.casefold()
    assert "akü" in low
    assert "guvenlik_uyarisi" in low.replace("ı", "i") or "güvenlik" in low
    # Akü görevinde LPG müdahale yasağı hatırlatması var
    assert "lpg" in low


def test_cabin_filter_task_is_low_risk():
    prompt = build_vision_prompt(_demo_vehicle(), task="cabin_filter", step=2)
    assert "POLEN" in prompt
