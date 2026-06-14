"""Yakıt & masraf takibi testleri: happy + tüketim + 401 + 422 + sahiplik (403)."""

import pytest

from app.core.rate_limit import enforce_rate_limit
from app.main import app

from .conftest import create_vehicle, register_and_login


def _fuel(odometer_km: int, liters: float, total_try: int | None = None, full_tank: bool = True) -> dict:
    body: dict = {"odometer_km": odometer_km, "liters": liters, "full_tank": full_tank}
    if total_try is not None:
        body["total_try"] = total_try
    return body


@pytest.mark.asyncio
async def test_add_and_list_fuel(client):
    headers = await register_and_login(client, "fuel1@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]

    r = await client.post(f"/v1/vehicles/{vid}/fuel", json=_fuel(100000, 40.0, 1600), headers=headers)
    assert r.status_code == 201
    body = r.json()
    assert body["odometer_km"] == 100000 and body["liters"] == 40.0 and body["total_try"] == 1600

    r = await client.get(f"/v1/vehicles/{vid}/fuel", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_fuel_summary_consumption(client):
    """İki tam-depo dolumu → L/100km hesaplanır."""
    headers = await register_and_login(client, "fuel2@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]

    # 100000 km'de dolum, 100500 km'de 30 L tam dolum → 500 km'de 30 L = 6.0 L/100km
    await client.post(f"/v1/vehicles/{vid}/fuel", json=_fuel(100000, 45.0, 1800), headers=headers)
    await client.post(f"/v1/vehicles/{vid}/fuel", json=_fuel(100500, 30.0, 1200), headers=headers)

    r = await client.get(f"/v1/vehicles/{vid}/fuel/summary", headers=headers)
    assert r.status_code == 200
    s = r.json()
    assert s["entry_count"] == 2
    assert s["avg_consumption"] == 6.0
    assert s["total_liters"] == 75.0
    assert s["total_spent_try"] == 3000
    assert s["last_odometer_km"] == 100500


@pytest.mark.asyncio
async def test_fuel_summary_single_entry_no_consumption(client):
    """Tek dolumda tüketim hesaplanamaz → null."""
    headers = await register_and_login(client, "fuel3@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    await client.post(f"/v1/vehicles/{vid}/fuel", json=_fuel(100000, 40.0), headers=headers)
    r = await client.get(f"/v1/vehicles/{vid}/fuel/summary", headers=headers)
    assert r.json()["avg_consumption"] is None


@pytest.mark.asyncio
async def test_fuel_requires_auth_401(client):
    r = await client.post("/v1/vehicles/1/fuel", json=_fuel(1000, 30.0))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_fuel_validation_422(client):
    headers = await register_and_login(client, "fuel4@usta.app")
    vehicle = await create_vehicle(client, headers)
    # liters 0 (gt=0) → geçersiz
    r = await client.post(
        f"/v1/vehicles/{vehicle['id']}/fuel", json={"odometer_km": 1000, "liters": 0}, headers=headers
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_fuel_other_vehicle_403(client):
    owner = await register_and_login(client, "fuelowner@usta.app")
    vehicle = await create_vehicle(client, owner)
    intruder = await register_and_login(client, "fuelintruder@usta.app")
    r = await client.post(
        f"/v1/vehicles/{vehicle['id']}/fuel", json=_fuel(1000, 30.0), headers=intruder
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_fuel_rate_limit_429(client):
    headers = await register_and_login(client, "fuel5@usta.app")
    vehicle = await create_vehicle(client, headers)

    async def _always_limited():
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="limit")

    app.dependency_overrides[enforce_rate_limit] = _always_limited
    try:
        r = await client.post(
            f"/v1/vehicles/{vehicle['id']}/fuel", json=_fuel(1000, 30.0), headers=headers
        )
        assert r.status_code == 429
    finally:
        app.dependency_overrides.pop(enforce_rate_limit, None)
