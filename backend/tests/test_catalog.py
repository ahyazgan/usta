"""TR araç parkı kataloğu ve araç oluştururken otomatik spec doldurma testleri."""

import pytest

from app.domain.catalog import find_spec
from app.domain.enums import FuelType, VehicleType

from .conftest import register_and_login


def test_find_spec_known_diesel_clio():
    spec = find_spec("Renault", "Clio", 2018, fuel_type=FuelType.dizel, engine_code="K9K")
    assert spec is not None
    assert spec.oil_spec == "5W-30"
    assert spec.spark_plug_part is None  # dizel -> buji yok


def test_find_spec_fuel_disambiguation_egea():
    benzin = find_spec("Fiat", "Egea", 2019, fuel_type=FuelType.benzin)
    dizel = find_spec("Fiat", "Egea", 2019, fuel_type=FuelType.dizel)
    assert benzin is not None and dizel is not None
    assert benzin.oil_spec == "5W-40"
    assert dizel.oil_spec == "5W-30"
    assert benzin.spark_plug_part and dizel.spark_plug_part is None


def test_find_spec_case_insensitive():
    assert find_spec("fiat", "egea", 2019, fuel_type=FuelType.lpg) is not None


def test_find_spec_unknown_returns_none():
    assert find_spec("Tesla", "Model S", 2022, fuel_type=FuelType.elektrik) is None


def test_find_spec_motorcycle_catalog():
    """Motosiklet katalogdan spec dolar; arabaymış gibi sorgulanınca eşleşmez."""
    moto = find_spec(
        "Honda", "CB125", 2021, fuel_type=FuelType.benzin,
        engine_code="JC64", vehicle_type=VehicleType.motosiklet,
    )
    assert moto is not None
    assert moto.oil_spec == "10W-30"
    assert moto.cabin_filter_part is None  # motosiklette kabin filtresi yok
    assert moto.spark_plug_part  # buji var
    # Tür araba (varsayılan) ise CB125 araba değil -> None.
    assert find_spec("Honda", "CB125", 2021, fuel_type=FuelType.benzin) is None


@pytest.mark.asyncio
async def test_create_motorcycle_autofills_spec(client):
    headers = await register_and_login(client, "moto-cat@usta.app")
    payload = {
        "make": "Yamaha", "model": "YBR125", "year": 2018,
        "fuel_type": "benzin", "vehicle_type": "motosiklet",
    }
    r = await client.post("/v1/vehicles", json=payload, headers=headers)
    assert r.status_code == 201
    spec = r.json()["spec"]
    assert spec is not None and spec["oil_spec"] == "10W-40"


def test_find_spec_out_of_year_range_none():
    assert find_spec("Fiat", "Egea", 1999) is None


@pytest.mark.asyncio
async def test_create_vehicle_autofills_spec_from_catalog(client):
    headers = await register_and_login(client, "cat1@usta.app")
    # spec verilmeden bilinen araç
    payload = {"make": "Renault", "model": "Clio", "year": 2018, "fuel_type": "dizel", "engine_code": "K9K"}
    r = await client.post("/v1/vehicles", json=payload, headers=headers)
    assert r.status_code == 201
    spec = r.json()["spec"]
    assert spec is not None
    assert spec["oil_spec"] == "5W-30"


@pytest.mark.asyncio
async def test_create_unknown_vehicle_has_no_spec(client):
    headers = await register_and_login(client, "cat2@usta.app")
    payload = {"make": "Bilinmeyen", "model": "XYZ", "year": 2020, "fuel_type": "benzin"}
    r = await client.post("/v1/vehicles", json=payload, headers=headers)
    assert r.status_code == 201
    assert r.json()["spec"] is None


@pytest.mark.asyncio
async def test_user_provided_spec_overrides_catalog(client):
    headers = await register_and_login(client, "cat3@usta.app")
    payload = {
        "make": "Renault", "model": "Clio", "year": 2018, "fuel_type": "dizel",
        "engine_code": "K9K", "spec": {"oil_spec": "0W-30 (özel)"},
    }
    r = await client.post("/v1/vehicles", json=payload, headers=headers)
    assert r.json()["spec"]["oil_spec"] == "0W-30 (özel)"
