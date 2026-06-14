"""TR araç parkı kataloğu ve araç oluştururken otomatik spec doldurma testleri."""

import pytest

from app.domain.catalog import CATALOG, _parse_entry, find_spec
from app.domain.enums import FuelType, VehicleType

from .conftest import register_and_login


def test_catalog_loads_from_json():
    """Katalog JSON'dan yüklendi ve dolu (boş = veri dosyası okunamadı demek)."""
    assert len(CATALOG) > 50
    makes = {e.make for e in CATALOG}
    assert {"BMW", "Renault", "Tesla", "Toyota"} <= makes


def test_parse_entry_valid():
    entry = _parse_entry(
        {
            "make": "Test",
            "model": "X",
            "year_min": 2010,
            "year_max": 2020,
            "vehicle_type": "araba",
            "fuels": ["benzin", "lpg"],
            "engine_codes": ["ABC"],
            "spec": {"oil_spec": "5W-30"},
        }
    )
    assert entry.make == "Test"
    assert FuelType.lpg in entry.fuels
    assert entry.spec.oil_spec == "5W-30"
    assert entry.vehicle_type == VehicleType.araba


def test_parse_entry_invalid_raises():
    """Bozuk kayıt (eksik zorunlu alan / geçersiz enum) hata fırlatır → yükleyici
    bunu yakalayıp o kaydı atlar, katalog çökmez."""
    import pytest as _pytest

    with _pytest.raises((KeyError, ValueError, TypeError)):
        _parse_entry({"make": "Eksik"})  # year_min/model yok
    with _pytest.raises((KeyError, ValueError, TypeError)):
        _parse_entry(
            {
                "make": "Kötü",
                "model": "Y",
                "year_min": 2010,
                "year_max": 2020,
                "fuels": ["uçak"],  # geçersiz FuelType
            }
        )


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
async def test_catalog_brands_endpoint(client):
    headers = await register_and_login(client, "brands@usta.app")
    cars = (await client.get("/v1/catalog/brands?vehicle_type=araba", headers=headers)).json()
    motos = (await client.get("/v1/catalog/brands?vehicle_type=motosiklet", headers=headers)).json()
    assert "Fiat" in cars and "Volkswagen" in cars
    assert "Fiat" not in motos  # araba markası moto listesinde yok
    assert "Yamaha" in motos and "Bajaj" in motos
    assert cars == sorted(cars)  # alfabetik
    # vehicle_type yoksa araba varsayılır.
    assert (await client.get("/v1/catalog/brands", headers=headers)).json() == cars


@pytest.mark.asyncio
async def test_catalog_brands_requires_auth_401(client):
    assert (await client.get("/v1/catalog/brands")).status_code == 401


@pytest.mark.asyncio
async def test_catalog_models_endpoint(client):
    headers = await register_and_login(client, "models@usta.app")
    # Renault'un birden çok modeli var (Clio, Megane, Symbol).
    renault = (
        await client.get("/v1/catalog/models?make=Renault&vehicle_type=araba", headers=headers)
    ).json()
    assert "Clio" in renault and "Megane" in renault
    assert renault == sorted(renault)  # alfabetik
    assert len(renault) == len(set(renault))  # tekilleştirilmiş
    # Harf duyarsız.
    assert (
        await client.get("/v1/catalog/models?make=renault&vehicle_type=araba", headers=headers)
    ).json() == renault
    # Tür ayrımı: Honda araba (Civic) vs motosiklet (CB125, PCX125...).
    honda_moto = (
        await client.get("/v1/catalog/models?make=Honda&vehicle_type=motosiklet", headers=headers)
    ).json()
    assert "CB125" in honda_moto and "Civic" not in honda_moto
    # Bilinmeyen marka -> boş liste (hata değil).
    assert (
        await client.get("/v1/catalog/models?make=Bilinmeyen&vehicle_type=araba", headers=headers)
    ).json() == []


@pytest.mark.asyncio
async def test_catalog_models_requires_auth_401(client):
    assert (await client.get("/v1/catalog/models?make=Renault")).status_code == 401


@pytest.mark.asyncio
async def test_catalog_models_missing_make_422(client):
    headers = await register_and_login(client, "models422@usta.app")
    # make zorunlu query param -> eksikse 422.
    assert (await client.get("/v1/catalog/models", headers=headers)).status_code == 422


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
