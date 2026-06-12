"""Tamirci dizini + lead testleri (Faz C)."""

import base64

import pytest

from app.domain.models import Mechanic

from .conftest import TestSession, create_vehicle, register_and_login

_FRAME = base64.b64encode(b"sahte-jpeg-1234").decode()


async def _seed_mechanics() -> None:
    async with TestSession() as db:
        db.add_all(
            [
                Mechanic(name="A Genel", city="İstanbul", phone="+9001", systems=None, verified=False),
                Mechanic(name="B Elektrik", city="İstanbul", phone="+9002", systems="elektrik,atesleme", verified=True),
                Mechanic(name="C Fren", city="Ankara", phone="+9003", systems="fren", verified=True),
            ]
        )
        await db.commit()


@pytest.mark.asyncio
async def test_list_mechanics_requires_auth_401(client):
    r = await client.get("/v1/mechanics")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_mechanics_city_filter(client):
    await _seed_mechanics()
    headers = await register_and_login(client, "mech1@usta.app")
    r = await client.get("/v1/mechanics?city=İstanbul", headers=headers)
    assert r.status_code == 200
    names = {m["name"] for m in r.json()}
    assert names == {"A Genel", "B Elektrik"}  # Ankara'daki C yok


@pytest.mark.asyncio
async def test_list_mechanics_system_filter_and_order(client):
    await _seed_mechanics()
    headers = await register_and_login(client, "mech2@usta.app")
    # elektrik: eşleşen B + genel A döner; doğrulanmış+eşleşen B önce.
    r = await client.get("/v1/mechanics?city=İstanbul&system=elektrik", headers=headers)
    body = r.json()
    assert [m["name"] for m in body] == ["B Elektrik", "A Genel"]
    # fren: İstanbul'da özel fren yok ama genel A uygundur.
    r = await client.get("/v1/mechanics?city=İstanbul&system=fren", headers=headers)
    assert {m["name"] for m in r.json()} == {"A Genel"}


@pytest.mark.asyncio
async def test_record_lead_happy_and_links_session(client):
    await _seed_mechanics()
    headers = await register_and_login(client, "mech3@usta.app")
    vehicle = await create_vehicle(client, headers)
    # Bir teşhis yap (session id için).
    d = await client.post(
        "/v1/ai/diagnose/image",
        json={"vehicle_id": vehicle["id"], "task": "battery", "frame_base64": _FRAME, "media_type": "image/jpeg"},
        headers=headers,
    )
    sid = d.json()["session_id"]

    mechs = (await client.get("/v1/mechanics?city=İstanbul", headers=headers)).json()
    mid = mechs[0]["id"]
    r = await client.post(
        f"/v1/mechanics/{mid}/lead",
        json={"channel": "whatsapp", "ai_session_id": sid},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["id"] >= 1


@pytest.mark.asyncio
async def test_record_lead_unknown_mechanic_404(client):
    headers = await register_and_login(client, "mech4@usta.app")
    r = await client.post("/v1/mechanics/99999/lead", json={"channel": "call"}, headers=headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_record_lead_invalid_channel_422(client):
    await _seed_mechanics()
    headers = await register_and_login(client, "mech5@usta.app")
    mid = (await client.get("/v1/mechanics", headers=headers)).json()[0]["id"]
    r = await client.post(f"/v1/mechanics/{mid}/lead", json={"channel": "uydurma"}, headers=headers)
    assert r.status_code == 422
