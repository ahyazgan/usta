"""Maliyet tahmini: tohum bantları + topluluk harmanı + uçlar."""

import pytest
from sqlalchemy import select

from app.domain.cost_estimates import seed_system_band, seed_task_band
from app.domain.enums import AIKind, ArizaSistem, VehicleType
from app.domain.models import AISession, User

from .conftest import TestSession, register_and_login


async def _seed_diagnoses(email: str, vehicle_id: int, sistem: str, costs: list[int]) -> None:
    """Belirtilen kullanıcı/araç için 'tamirci çözdü' ödemeli teşhisler ekler."""
    async with TestSession() as s:
        uid = (await s.scalar(select(User).where(User.email == email))).id
        for c in costs:
            s.add(
                AISession(
                    user_id=uid,
                    vehicle_id=vehicle_id,
                    kind=AIKind.sound,
                    model="test",
                    ariza_sistem=sistem,
                    resolution="tamirci_cozdu",
                    cost_try=c,
                    tespit="büyük ihtimalle test",
                )
            )
        await s.commit()


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


@pytest.mark.asyncio
async def test_vehicle_estimates_list(client):
    """Fiyat vitrini: araca uygulanabilir tüm işler + tahmin tek çağrıda."""
    headers = await register_and_login(client, "vest@usta.app")
    vid = await _make_car(client, headers)
    rows = (await client.get(f"/v1/vehicles/{vid}/estimates", headers=headers)).json()
    assert len(rows) >= 8
    ids = {r["id"] for r in rows}
    assert "oil_change" in ids and "chain" not in ids  # araba; zincir yok
    for r in rows:
        assert r["high_try"] >= r["low_try"] > 0
        assert r["source"] in {"seed", "community"}
        assert {"title_tr", "title_en", "risk"} <= r.keys()


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


@pytest.mark.asyncio
async def test_system_estimate_community_from_resolutions(client):
    """Teşhis kapanışındaki tamirci ödemeleri sistem bandını topluluğa taşır."""
    email = "cost4@usta.app"
    headers = await register_and_login(client, email)
    vid = await _make_car(client, headers)
    await _seed_diagnoses(email, vid, "fren", [1000, 1500, 2000, 2500, 3000])

    r = await client.get(
        "/v1/estimate/diagnosis?ariza_sistem=fren&vehicle_type=araba", headers=headers
    )
    body = r.json()
    assert body["source"] == "community"
    assert body["sample_size"] == 5
    assert body["low_try"] == 1500 and body["high_try"] == 2500  # p25..p75


# --- Çark yakıtı: kapanışta tamirci ödemesini yakala ------------------------- #

async def _one_diagnosis(email: str, vehicle_id: int) -> int:
    async with TestSession() as s:
        uid = (await s.scalar(select(User).where(User.email == email))).id
        sess = AISession(
            user_id=uid, vehicle_id=vehicle_id, kind=AIKind.sound, model="test",
            ariza_sistem="fren", tespit="büyük ihtimalle test",
        )
        s.add(sess)
        await s.commit()
        return sess.id


@pytest.mark.asyncio
async def test_resolution_captures_mechanic_cost(client):
    email = "cost5@usta.app"
    headers = await register_and_login(client, email)
    vid = await _make_car(client, headers)
    sid = await _one_diagnosis(email, vid)

    r = await client.post(
        f"/v1/vehicles/{vid}/diagnoses/{sid}/resolution",
        json={"resolution": "tamirci_cozdu", "cost_try": 2000},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["resolution"] == "tamirci_cozdu"
    assert r.json()["cost_try"] == 2000


@pytest.mark.asyncio
async def test_resolution_non_mechanic_ignores_cost(client):
    """Tamirci dışı kapanışta ödeme yazılmaz (band kirlenmesin)."""
    email = "cost6@usta.app"
    headers = await register_and_login(client, email)
    vid = await _make_car(client, headers)
    sid = await _one_diagnosis(email, vid)

    r = await client.post(
        f"/v1/vehicles/{vid}/diagnoses/{sid}/resolution",
        json={"resolution": "kendim_cozdum", "cost_try": 9999},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["cost_try"] is None
