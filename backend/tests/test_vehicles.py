"""Araç CRUD testleri: happy + 401 + 422 + sahiplik (403/404)."""

import pytest

from .conftest import create_vehicle, register_and_login


@pytest.mark.asyncio
async def test_create_and_list_vehicle(client):
    headers = await register_and_login(client, "v1@usta.app")
    vehicle = await create_vehicle(client, headers)
    assert vehicle["make"] == "Fiat"
    assert vehicle["fuel_type"] == "lpg"
    assert vehicle["spec"]["oil_spec"] == "5W-30"

    r = await client.get("/v1/vehicles", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_vehicle_dates_roundtrip(client):
    """muayene/sigorta tarihleri create + update üzerinden korunur."""
    headers = await register_and_login(client, "vdate@usta.app")
    r = await client.post(
        "/v1/vehicles",
        json={
            "make": "Fiat", "model": "Egea", "year": 2019, "fuel_type": "lpg",
            "muayene_date": "2027-03-15", "sigorta_date": "2026-08-01",
        },
        headers=headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["muayene_date"] == "2027-03-15"
    assert body["sigorta_date"] == "2026-08-01"

    # Güncelleme yalnızca verilen tarihi değiştirir.
    r = await client.patch(
        f"/v1/vehicles/{body['id']}",
        json={"sigorta_date": "2027-08-01"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["sigorta_date"] == "2027-08-01"
    assert r.json()["muayene_date"] == "2027-03-15"  # dokunulmadı


@pytest.mark.asyncio
async def test_create_vehicle_requires_auth_401(client):
    r = await client.post("/v1/vehicles", json={"make": "Fiat", "model": "Egea", "year": 2019, "fuel_type": "lpg"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_vehicle_validation_422(client):
    headers = await register_and_login(client, "v2@usta.app")
    # geçersiz fuel_type + yıl aralık dışı
    r = await client.post(
        "/v1/vehicles",
        json={"make": "Fiat", "model": "Egea", "year": 1800, "fuel_type": "havagazi"},
        headers=headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_other_users_vehicle_403(client):
    owner = await register_and_login(client, "owner@usta.app")
    vehicle = await create_vehicle(client, owner)

    intruder = await register_and_login(client, "intruder@usta.app")
    r = await client.get(f"/v1/vehicles/{vehicle['id']}", headers=intruder)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_get_missing_vehicle_404(client):
    headers = await register_and_login(client, "v3@usta.app")
    r = await client.get("/v1/vehicles/99999", headers=headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_and_delete_vehicle(client):
    headers = await register_and_login(client, "v4@usta.app")
    vehicle = await create_vehicle(client, headers)

    r = await client.patch(f"/v1/vehicles/{vehicle['id']}", json={"current_km": 90000}, headers=headers)
    assert r.status_code == 200
    assert r.json()["current_km"] == 90000

    r = await client.delete(f"/v1/vehicles/{vehicle['id']}", headers=headers)
    assert r.status_code == 204

    r = await client.get(f"/v1/vehicles/{vehicle['id']}", headers=headers)
    assert r.status_code == 404
