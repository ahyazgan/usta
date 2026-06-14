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


# --------------------------------------------------------------------------- #
# Veri çarkı: session_id + 👍/👎 geri bildirimi + teşhis↔log bağı + maliyet
# --------------------------------------------------------------------------- #


async def _diagnose_and_get_session_id(client, headers, vid: int) -> int:
    r = await client.post(
        "/v1/ai/diagnose/image",
        json={
            "vehicle_id": vid,
            "task": "battery",
            "frame_base64": _FRAME,
            "media_type": "image/jpeg",
        },
        headers=headers,
    )
    assert r.status_code == 200
    session_id = r.json()["session_id"]
    assert isinstance(session_id, int) and session_id >= 1
    return session_id


@pytest.mark.asyncio
async def test_diagnose_returns_session_id_and_kategori_logged(client):
    headers = await register_and_login(client, "fb0@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    await _diagnose_and_get_session_id(client, headers, vid)
    await _run_sound_diagnose(client, headers, vid)

    r = await client.get(f"/v1/vehicles/{vid}/diagnoses", headers=headers)
    body = r.json()
    image = next(x for x in body if x["kind"] == "image")
    sound = next(x for x in body if x["kind"] == "sound")
    assert image["kategori"] == "battery"  # görüntüde kategori = görev
    assert sound["kategori"] == "kayis_sesi"  # seste kategori = ses türü (mock)
    assert image["feedback_dogru"] is None  # henüz oylanmadı


@pytest.mark.asyncio
async def test_feedback_roundtrip_and_revote(client):
    headers = await register_and_login(client, "fb1@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    sid = await _diagnose_and_get_session_id(client, headers, vid)

    r = await client.post(
        f"/v1/vehicles/{vid}/diagnoses/{sid}/feedback",
        json={"dogru": True},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["feedback_dogru"] is True

    # Fikir değiştirme: son oy yazılır.
    r = await client.post(
        f"/v1/vehicles/{vid}/diagnoses/{sid}/feedback",
        json={"dogru": False},
        headers=headers,
    )
    assert r.json()["feedback_dogru"] is False

    # Liste de güncel değeri yansıtır.
    r = await client.get(f"/v1/vehicles/{vid}/diagnoses", headers=headers)
    assert r.json()[0]["feedback_dogru"] is False


@pytest.mark.asyncio
async def test_feedback_requires_auth_401(client):
    r = await client.post("/v1/vehicles/1/diagnoses/1/feedback", json={"dogru": True})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_feedback_foreign_session_404(client):
    owner = await register_and_login(client, "fb-own@usta.app")
    vehicle = await create_vehicle(client, owner)
    vid = vehicle["id"]
    sid = await _diagnose_and_get_session_id(client, owner, vid)

    intruder = await register_and_login(client, "fb-intruder@usta.app")
    their_vehicle = await create_vehicle(client, intruder)
    # Başkasının teşhisini kendi aracın üzerinden oylayamazsın.
    r = await client.post(
        f"/v1/vehicles/{their_vehicle['id']}/diagnoses/{sid}/feedback",
        json={"dogru": True},
        headers=intruder,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_diagnose_tags_ariza_sistem(client):
    """Görüntü ve ses teşhisleri sorgulanabilir araç sistemine eşlenir."""
    headers = await register_and_login(client, "tax1@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    await _diagnose_and_get_session_id(client, headers, vid)  # task=battery
    await _run_sound_diagnose(client, headers, vid)  # mock -> kayis_sesi

    body = (await client.get(f"/v1/vehicles/{vid}/diagnoses", headers=headers)).json()
    image = next(x for x in body if x["kind"] == "image")
    sound = next(x for x in body if x["kind"] == "sound")
    assert image["ariza_sistem"] == "elektrik"  # battery -> elektrik
    assert sound["ariza_sistem"] == "sanziman"  # kayis_sesi -> sanziman


@pytest.mark.asyncio
async def test_resolution_roundtrip_and_revote(client):
    headers = await register_and_login(client, "res1@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    sid = await _diagnose_and_get_session_id(client, headers, vid)

    r = await client.post(
        f"/v1/vehicles/{vid}/diagnoses/{sid}/resolution",
        json={"resolution": "kendim_cozdum"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["resolution"] == "kendim_cozdum"

    # Fikir değiştirme: son değer yazılır.
    r = await client.post(
        f"/v1/vehicles/{vid}/diagnoses/{sid}/resolution",
        json={"resolution": "tamirci_cozdu"},
        headers=headers,
    )
    assert r.json()["resolution"] == "tamirci_cozdu"

    body = (await client.get(f"/v1/vehicles/{vid}/diagnoses", headers=headers)).json()
    assert body[0]["resolution"] == "tamirci_cozdu"


@pytest.mark.asyncio
async def test_resolution_requires_auth_401(client):
    r = await client.post(
        "/v1/vehicles/1/diagnoses/1/resolution", json={"resolution": "kendim_cozdum"}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_resolution_invalid_value_422(client):
    headers = await register_and_login(client, "res2@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    sid = await _diagnose_and_get_session_id(client, headers, vid)
    r = await client.post(
        f"/v1/vehicles/{vid}/diagnoses/{sid}/resolution",
        json={"resolution": "uydurma_deger"},
        headers=headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_log_links_session_and_stores_cost(client):
    headers = await register_and_login(client, "fb-link@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    sid = await _diagnose_and_get_session_id(client, headers, vid)

    r = await client.post(
        f"/v1/vehicles/{vid}/logs",
        json={"task": "battery", "km": 85000, "ai_session_id": sid, "cost_try": 750},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["cost_try"] == 750

    # Sahte/yabancı session id bağı sessizce düşülür ama log yine 201'dir.
    r = await client.post(
        f"/v1/vehicles/{vid}/logs",
        json={"task": "oil_change", "km": 85100, "ai_session_id": 999_999},
        headers=headers,
    )
    assert r.status_code == 201
