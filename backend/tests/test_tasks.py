"""Görev kayıt defteri + GET /v1/tasks + fiyatlandırma + harness testleri."""

import pytest

from app.domain.enums import FuelType, VehicleType
from app.domain.pricing import TARGET_COST_PER_DIAGNOSIS_USD, cost_usd, within_budget
from app.domain.tasks import get_task, get_tasks, tasks_for_fuel, tasks_for_vehicle
from app.services.ai.prompts import PROMPTS_DIR
from app.tools.eval_vision import offline_selfcheck

from .conftest import register_and_login


# --------------------------------------------------------------------------- #
# Kayıt defteri + prompt senkronu
# --------------------------------------------------------------------------- #


def test_every_task_has_existing_prompt_file():
    for task in get_tasks():
        assert (PROMPTS_DIR / task.prompt_file).exists(), f"prompt yok: {task.prompt_file}"


def test_get_task_lookup():
    assert get_task("battery").risk.value == "yuksek"
    assert get_task("cabin_filter").risk.value == "dusuk"
    assert get_task("olmayan") is None


def test_new_tasks_registered_with_expected_risk():
    # Yeni eklenen görevler kayıt defterinde ve doğru risk seviyesinde.
    assert get_task("coolant").risk.value == "yuksek"  # basınçlı + sıcak: güvenlik-kritik
    assert get_task("tire").risk.value == "orta"
    assert get_task("headlight").risk.value == "orta"
    assert get_task("wiper").risk.value == "dusuk"
    # Başlıklar iki dilde de dolu.
    for tid in ("coolant", "tire", "wiper", "headlight"):
        task = get_task(tid)
        assert task.title_tr and task.title_en, f"başlık eksik: {tid}"


def test_tasks_by_vehicle_type():
    """Motosiklet: polen/silecek YOK, zincir VAR; araba: tersi."""
    moto = {t.id for t in tasks_for_vehicle(FuelType.benzin, VehicleType.motosiklet)}
    car = {t.id for t in tasks_for_vehicle(FuelType.benzin, VehicleType.araba)}

    assert {"chain", "tire_pressure", "clutch_cable"} <= moto  # moto-özel görevler
    assert "cabin_filter" not in moto
    assert "wiper" not in moto
    # Ortak görevler motosiklette de var.
    assert {"oil_change", "brake_check", "tire", "battery"} <= moto

    assert {"chain", "tire_pressure", "clutch_cable"} & car == set()  # arabada yok
    assert {"cabin_filter", "wiper"} <= car

    # None (eski kayıt) = araba kabul edilir.
    assert tasks_for_vehicle(FuelType.benzin, None) == tasks_for_vehicle(
        FuelType.benzin, VehicleType.araba
    )


def test_new_tasks_fuel_applicability():
    elektrik = {t.id for t in tasks_for_fuel(FuelType.elektrik)}
    benzin = {t.id for t in tasks_for_fuel(FuelType.benzin)}
    # Lastik/silecek/far her araçta var (elektrik dahil).
    assert {"tire", "wiper", "headlight"} <= elektrik
    assert {"tire", "wiper", "headlight"} <= benzin
    # Motor soğutma sıvısı yanmalı motorlarda var; elektrikte farklı sistem.
    assert "coolant" in benzin
    assert "coolant" not in elektrik


def test_tasks_for_fuel_filters_by_applicability():
    benzin = {t.id for t in tasks_for_fuel(FuelType.benzin)}
    dizel = {t.id for t in tasks_for_fuel(FuelType.dizel)}
    elektrik = {t.id for t in tasks_for_fuel(FuelType.elektrik)}

    assert "spark_plug" in benzin  # bujili motor
    assert "spark_plug" not in dizel  # dizelde buji yok
    assert "oil_change" in dizel
    assert "air_filter" in dizel  # motor hava filtresi yanmalı motorlarda var
    assert "oil_change" not in elektrik  # elektrikte yağ yok
    assert "spark_plug" not in elektrik
    assert "air_filter" not in elektrik  # elektrikte motor hava filtresi yok
    assert {"battery", "cabin_filter", "brake_check"} <= elektrik  # her araçta var
    assert get_task("brake_check").risk.value == "yuksek"  # güvenlik-kritik


@pytest.mark.asyncio
async def test_vehicle_tasks_endpoint_respects_fuel(client):
    from .conftest import create_vehicle

    headers = await register_and_login(client, "vtask@usta.app")
    # conftest demo aracı LPG -> buji dahil tüm görevler
    lpg = await create_vehicle(client, headers)
    r = await client.get(f"/v1/vehicles/{lpg['id']}/tasks", headers=headers)
    assert r.status_code == 200
    assert "spark_plug" in {t["id"] for t in r.json()}

    # Dizel araç -> buji hariç
    dz = await client.post(
        "/v1/vehicles",
        json={"make": "Renault", "model": "Clio", "year": 2018, "fuel_type": "dizel", "engine_code": "K9K"},
        headers=headers,
    )
    rid = dz.json()["id"]
    r = await client.get(f"/v1/vehicles/{rid}/tasks", headers=headers)
    ids = {t["id"] for t in r.json()}
    assert "spark_plug" not in ids
    assert "oil_change" in ids


@pytest.mark.asyncio
async def test_vehicle_tasks_endpoint_respects_type(client):
    headers = await register_and_login(client, "vtype@usta.app")
    moto = await client.post(
        "/v1/vehicles",
        json={"make": "Honda", "model": "CB125", "year": 2021,
              "fuel_type": "benzin", "vehicle_type": "motosiklet"},
        headers=headers,
    )
    assert moto.status_code == 201
    assert moto.json()["vehicle_type"] == "motosiklet"
    mid = moto.json()["id"]

    ids = {t["id"] for t in (await client.get(f"/v1/vehicles/{mid}/tasks", headers=headers)).json()}
    assert "chain" in ids
    assert "cabin_filter" not in ids and "wiper" not in ids

    # Zincir rehberi motosiklette 200; araba-only silecek motosiklette 404.
    assert (await client.get(f"/v1/vehicles/{mid}/tasks/chain/guide", headers=headers)).status_code == 200
    assert (await client.get(f"/v1/vehicles/{mid}/tasks/wiper/guide", headers=headers)).status_code == 404


@pytest.mark.asyncio
async def test_vehicle_tasks_requires_auth_401(client):
    r = await client.get("/v1/vehicles/1/tasks")
    assert r.status_code == 401


# --------------------------------------------------------------------------- #
# Endpoint
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_list_tasks_happy(client):
    headers = await register_and_login(client, "task1@usta.app")
    r = await client.get("/v1/tasks", headers=headers)
    assert r.status_code == 200
    body = r.json()
    ids = {t["id"] for t in body}
    assert {"oil_change", "battery", "cabin_filter"} <= ids
    battery = next(t for t in body if t["id"] == "battery")
    assert battery["risk"] == "yuksek"
    assert battery["title_tr"] and battery["title_en"]


@pytest.mark.asyncio
async def test_list_tasks_requires_auth_401(client):
    r = await client.get("/v1/tasks")
    assert r.status_code == 401


# --------------------------------------------------------------------------- #
# Fiyatlandırma / maliyet
# --------------------------------------------------------------------------- #


def test_cost_usd_math():
    # 1M girdi @ $3, 1M çıktı @ $15
    assert cost_usd("claude-sonnet-4-5", 1_000_000, 0) == pytest.approx(3.0)
    assert cost_usd("claude-sonnet-4-5", 0, 1_000_000) == pytest.approx(15.0)


def test_typical_diagnosis_within_budget():
    # Tipik bir teşhis (1024px kare ~ 1300 girdi + 100 çıktı) bütçe içinde olmalı.
    assert within_budget("claude-sonnet-4-5", 1300, 100)
    assert cost_usd("claude-sonnet-4-5", 1300, 100) < TARGET_COST_PER_DIAGNOSIS_USD


def test_over_budget_detected():
    assert not within_budget("claude-sonnet-4-5", 20_000, 5_000)


# --------------------------------------------------------------------------- #
# Çevrimdışı harness öz-denetimi (gerçek çağrı yok)
# --------------------------------------------------------------------------- #


def test_offline_selfcheck_passes(capsys):
    rc = offline_selfcheck()
    assert rc == 0, "vision harness öz-denetimi geçmeli"
    out = capsys.readouterr().out
    assert "TÜM ÖZ-DENETİMLER GEÇTİ" in out
