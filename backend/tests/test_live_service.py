"""Canlı oturum system instruction kurucusu — güvenlik + araç + görev birleşimi."""

from app.domain.enums import FuelType, VehicleType
from app.domain.models import Vehicle, VehicleSpec
from app.services.ai.live_service import build_live_system_instruction


def _vehicle() -> Vehicle:
    v = Vehicle(
        make="Fiat", model="Egea", year=2019,
        fuel_type=FuelType.benzin, vehicle_type=VehicleType.araba,
        engine_code="843A1000", current_km=84000,
    )
    v.spec = VehicleSpec(
        oil_spec="5W-40", oil_capacity_l=3.0, oil_drain_bolt_size="14mm",
        oil_drain_location="karter alt-arka", oil_filter_part="55256470",
        spark_plug_part="NGK DCPR7E-N-10", battery_spec="60Ah / 540A",
        battery_location="motor bölmesi sol ön",
    )
    return v


def test_live_instruction_has_safety_and_vehicle():
    instr = build_live_system_instruction(_vehicle())
    low = instr.casefold()
    # Güvenlik kuralları (canlı taban prompttan)
    assert "büyük ihtimalle" in low
    assert "lpg" in low
    assert "tamirci" in low  # "vazgeç, tamirciye git" çıkışı
    # Araç bağlamı
    assert "Fiat Egea" in instr
    assert "55256470" in instr  # araca özel yağ filtresi no'su


def test_live_instruction_with_task_includes_steps_parts_price():
    instr = build_live_system_instruction(_vehicle(), task_id="oil_change")
    assert "MEVCUT GÖREV" in instr
    assert "Yağ Değişimi" in instr
    # Görev adımları + araca özel parça + tohum fiyat aralığı
    assert "55256470" in instr  # parçalar bölümünde
    assert "800-1800 TL" in instr  # oil_change araba tohum bandı
    assert "Adımlar" in instr


def test_live_instruction_unknown_task_skips_section():
    instr = build_live_system_instruction(_vehicle(), task_id="uydurma_gorev")
    assert "MEVCUT GÖREV" not in instr  # bilinmeyen görev → bölüm yok, hata yok
