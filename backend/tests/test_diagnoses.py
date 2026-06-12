"""GET /v1/vehicles/{id}/diagnoses — teşhis geçmişi testleri (Claude mock'lu)."""

import base64

import pytest

from .conftest import create_vehicle, register_and_login

_FRAME = base64.b64encode(b"sahte-jpeg-baytlari-1234").decode()


async def _run_image_diagnose(client, headers, vid: int) -> None:
    r = await client.post(
        "/v1/ai/diagnose/image",
        json={
            "vehicle_id": vid,
            "task": "oil_change",
            "frame_base64": _FRAME,
            "media_type": "image/jpeg",
        },
        headers=headers,
    )
    assert r.status_code == 200


async def _run_sound_diagnose(client, headers, vid: int) -> None:
    r = await client.post(
        "/v1/ai/diagnose/sound",
        json={
            "vehicle_id": vid,
            "user_description": "Rölantide önden tıkırtı geliyor.",
            "condition": "rolanti",
        },
        headers=headers,
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_diagnoses_empty_initially(client):
    headers = await register_and_login(client, "diag0@usta.app")
    vehicle = await create_vehicle(client, headers)
    r = await client.get(f"/v1/vehicles/{vehicle['id']}/diagnoses", headers=headers)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_diagnoses_lists_image_and_sound(client):
    headers = await register_and_login(client, "diag1@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]

    await _run_image_diagnose(client, headers, vid)
    await _run_sound_diagnose(client, headers, vid)

    r = await client.get(f"/v1/vehicles/{vid}/diagnoses", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    kinds = {x["kind"] for x in body}
    assert kinds == {"image", "sound"}

    image = next(x for x in body if x["kind"] == "image")
    assert image["task"] == "oil_change"
    # Özet, güvenlik kuralları zorlandıktan sonraki metinden yazılır -> hedge var.
    assert "büyük ihtimalle" in image["tespit"].casefold()
    assert image["guven"] in {"yuksek", "orta", "dusuk"}
    assert image["tamirciye_git"] in {True, False}

    sound = next(x for x in body if x["kind"] == "sound")
    assert sound["task"] is None  # ses teşhisi görev bağlamsızdır
    assert sound["tespit"]


@pytest.mark.asyncio
async def test_diagnoses_requires_auth_401(client):
    r = await client.get("/v1/vehicles/1/diagnoses")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_diagnoses_other_users_vehicle_403(client):
    owner = await register_and_login(client, "diag-own@usta.app")
    vehicle = await create_vehicle(client, owner)
    intruder = await register_and_login(client, "diag-intruder@usta.app")
    r = await client.get(f"/v1/vehicles/{vehicle['id']}/diagnoses", headers=intruder)
    assert r.status_code in {403, 404}


@pytest.mark.asyncio
async def test_guide_includes_diy_saving(client):
    """Rehber yanıtı bitiş ekranı için tasarruf tahminini içerir."""
    headers = await register_and_login(client, "diag-guide@usta.app")
    vehicle = await create_vehicle(client, headers)
    r = await client.get(
        f"/v1/vehicles/{vehicle['id']}/tasks/oil_change/guide", headers=headers
    )
    assert r.status_code == 200
    assert r.json()["diy_saving_try"] == 400
