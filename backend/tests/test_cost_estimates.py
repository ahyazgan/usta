"""Maliyet tahmini: tohum bantları + topluluk harmanı + uçlar."""

import pytest

from app.domain.cost_estimates import seed_system_band, seed_task_band
from app.domain.enums import ArizaSistem, VehicleType

from .conftest import register_and_login


# --- Birim: tohum bantları --------------------------------------------------- #

def test_seed_task_band_car_vs_moto_scaling():
    car = seed_task_band("oil_change", VehicleType.araba)
    moto = seed_task_band("oil_change", VehicleType.motosiklet)
    assert car is not None and moto is not None
    assert (car.low, car.high) == (800, 1800)
    # Motosiklet paylaşılan görevde ucuz (çarpan uygulanmış).
    assert moto.low < car.low and moto.high < car.high


def test_seed_task_band_moto_native_not_scaled():
    # Zincir zaten moto fiyatı → çarpan uygulanmaz, araba sorgusuyla aynı.
    moto = seed_task_band("chain", VehicleType.motosiklet)
    car = seed_task_band("chain", VehicleType.araba)
    assert moto == car == seed_task_band("chain", None)


def test_seed_task_band_unknown_none():
    assert seed_task_band("bilinmeyen_gorev", VehicleType.araba) is None


def test_seed_system_band():
    fren = seed_system_band(ArizaSistem.fren, VehicleType.araba)
    fren_moto = seed_system_band("fren", VehicleType.motosiklet)
    assert fren is not None and fren_moto is not None
    assert fren_moto.high < fren.high  # moto ucuz
    assert seed_system_band("yok", VehicleType.araba) is None


# --- Uç: görev tahmini ------------------------------------------------------- #

async def _make_car(client, headers) -> int:
    r = await client.post(
        "/v1/vehicles",
        json={"make": "Fiat", "model": "Egea", "year": 2019, "fuel_type": "benzin"},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


@pytest.mark.asyncio
async def test_task_estimate_seed_then_community(client):
    headers = await register_and_login(client, "cost1@usta.app")
    vid = await _make_car(client, headers)

    # Önce gerçek veri yok → tohum bandı.
    r = await client.get(f"/v1/vehicles/{vid}/tasks/oil_change/estimate", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "seed"
    assert body["low_try"] == 800 and body["high_try"] == 1800
    assert body["currency"] == "TRY"

    # 5 gerçek ödeme gir → topluluk bandına kayar (k-anon eşiği).
    for cost in (900, 1000, 1100, 1200, 1300):
        lr = await client.post(
            f"/v1/vehicles/{vid}/logs",
            json={"task": "oil_change", "cost_try": cost},
            headers=headers,
        )
        assert lr.status_code == 201

    r2 = await client.get(f"/v1/vehicles/{vid}/tasks/oil_change/estimate", headers=headers)
    body2 = r2.json()
    assert body2["source"] == "community"
    assert body2["sample_size"] == 5
    assert body2["low_try"] == 1000 and body2["high_try"] == 1200  # p25..p75


@pytest.mark.asyncio
async def test_task_estimate_unknown_404(client):
    headers = await register_and_login(client, "cost2@usta.app")
    vid = await _make_car(client, headers)
    r = await client.get(f"/v1/vehicles/{vid}/tasks/uydurma/estimate", headers=headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_task_estimate_requires_auth_401(client):
    r = await client.get("/v1/vehicles/1/tasks/oil_change/estimate")
    assert r.status_code == 401


# --- Uç: teşhis (arıza sistemi) tahmini -------------------------------------- #

@pytest.mark.asyncio
async def test_diagnosis_estimate_seed(client):
    headers = await register_and_login(client, "cost3@usta.app")
    r = await client.get(
        "/v1/estimate/diagnosis?ariza_sistem=fren&vehicle_type=araba", headers=headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "seed"
    assert body["low_try"] == 1000 and body["high_try"] == 4500


@pytest.mark.asyncio
async def test_diagnosis_estimate_requires_auth_401(client):
    r = await client.get("/v1/estimate/diagnosis?ariza_sistem=fren")
    assert r.status_code == 401
