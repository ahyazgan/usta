"""Bakım geçmişi & hatırlatma testleri: happy + 401 + 422 + sahiplik + hatırlatma mantığı."""

import pytest

from app.domain.enums import ReminderStatus
from app.domain.maintenance import compute_reminders

from .conftest import create_vehicle, register_and_login


# --------------------------------------------------------------------------- #
# Saf hatırlatma mantığı
# --------------------------------------------------------------------------- #


def test_reminder_due_when_overdue():
    r = {x.task: x for x in compute_reminders(current_km=100_000, last_km_by_task={"oil_change": 80_000})}
    oil = r["oil_change"]
    assert oil.due_km == 95_000
    assert oil.remaining_km == -5_000
    assert oil.status == ReminderStatus.due


def test_reminder_soon_within_threshold():
    r = {x.task: x for x in compute_reminders(100_000, {"oil_change": 86_000})}
    assert r["oil_change"].status == ReminderStatus.soon  # kalan 1000 <= 2000


def test_reminder_ok_far_away():
    r = {x.task: x for x in compute_reminders(100_000, {"oil_change": 95_000})}
    assert r["oil_change"].status == ReminderStatus.ok  # kalan 10000


def test_reminder_unknown_without_data():
    r = {x.task: x for x in compute_reminders(None, {})}
    assert r["oil_change"].status == ReminderStatus.unknown
    assert r["oil_change"].remaining_km is None


# --------------------------------------------------------------------------- #
# Endpoint
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_add_and_list_logs(client):
    headers = await register_and_login(client, "log1@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]

    r = await client.post(
        f"/v1/vehicles/{vid}/logs",
        json={"task": "oil_change", "km": 80000, "note": "5W-30 + filtre"},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["task"] == "oil_change"

    r = await client.get(f"/v1/vehicles/{vid}/logs", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_logs_require_auth_401(client):
    r = await client.get("/v1/vehicles/1/logs")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_add_log_validation_422(client):
    headers = await register_and_login(client, "log2@usta.app")
    vehicle = await create_vehicle(client, headers)
    # negatif km
    r = await client.post(
        f"/v1/vehicles/{vehicle['id']}/logs",
        json={"task": "oil_change", "km": -5},
        headers=headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_logs_ownership_403(client):
    owner = await register_and_login(client, "logowner@usta.app")
    vehicle = await create_vehicle(client, owner)
    intruder = await register_and_login(client, "logintruder@usta.app")
    r = await client.get(f"/v1/vehicles/{vehicle['id']}/logs", headers=intruder)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_reminders_endpoint_reflects_logs(client):
    headers = await register_and_login(client, "rem1@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    # current_km from create_vehicle helper = 84210; son yağ 70000 -> due 85000, kalan 790 -> soon
    await client.post(
        f"/v1/vehicles/{vid}/logs", json={"task": "oil_change", "km": 70000}, headers=headers
    )
    r = await client.get(f"/v1/vehicles/{vid}/reminders", headers=headers)
    assert r.status_code == 200
    oil = next(x for x in r.json() if x["task"] == "oil_change")
    assert oil["due_km"] == 85000
    assert oil["status"] in {"soon", "due"}
