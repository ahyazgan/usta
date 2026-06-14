"""KVKK testleri: açık rıza + veri silme hakkı + anonim istatistik (k-anon)."""

import base64

import pytest
from sqlalchemy import func, select

from app.domain.models import Mechanic, MechanicLead

from .conftest import TestSession, create_vehicle, register_and_login

_FRAME = base64.b64encode(b"sahte-jpeg-1234").decode()


async def _diagnose(client, headers, vid: int, *, feedback: bool | None = None) -> None:
    r = await client.post(
        "/v1/ai/diagnose/image",
        json={"vehicle_id": vid, "task": "battery", "frame_base64": _FRAME, "media_type": "image/jpeg"},
        headers=headers,
    )
    assert r.status_code == 200
    if feedback is not None:
        sid = r.json()["session_id"]
        await client.post(
            f"/v1/vehicles/{vid}/diagnoses/{sid}/feedback",
            json={"dogru": feedback},
            headers=headers,
        )


# --------------------------------------------------------------------------- #
# Açık rıza
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_consent_defaults_false(client):
    headers = await register_and_login(client, "c1@usta.app")
    r = await client.get("/v1/me/consent", headers=headers)
    assert r.status_code == 200
    assert r.json() == {"analytics": False, "data": False}


@pytest.mark.asyncio
async def test_consent_partial_update(client):
    headers = await register_and_login(client, "c2@usta.app")
    r = await client.patch("/v1/me/consent", json={"analytics": True}, headers=headers)
    assert r.json() == {"analytics": True, "data": False}
    # data'yı aç, analytics dokunulmaz.
    r = await client.patch("/v1/me/consent", json={"data": True}, headers=headers)
    assert r.json() == {"analytics": True, "data": True}


@pytest.mark.asyncio
async def test_consent_requires_auth_401(client):
    r = await client.get("/v1/me/consent")
    assert r.status_code == 401


# --------------------------------------------------------------------------- #
# Silme/unutulma hakkı
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_account_deletion_erases_all_data(client):
    headers = await register_and_login(client, "del@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    await _diagnose(client, headers, vid)
    await client.post(f"/v1/vehicles/{vid}/logs", json={"task": "battery", "km": 85000}, headers=headers)

    r = await client.delete("/v1/me", headers=headers)
    assert r.status_code == 204

    # Token artık geçersiz (kullanıcı yok) — korumalı uç 401.
    r = await client.get("/v1/vehicles", headers=headers)
    assert r.status_code == 401

    # Aynı e-posta yeniden kaydedilebilir (gerçekten silinmiş).
    r = await client.post(
        "/v1/auth/register", json={"email": "del@usta.app", "password": "parola1234"}
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_account_deletion_removes_mechanic_leads(client):
    """Unutulma hakkı: tamirci lead'leri de silinir (SQLite cascade uygulamaz)."""
    headers = await register_and_login(client, "del-lead@usta.app")
    await create_vehicle(client, headers)
    async with TestSession() as db:
        db.add(Mechanic(name="L Tamirci", city="İstanbul", phone="+9000"))
        await db.commit()
    mid = (await client.get("/v1/mechanics", headers=headers)).json()[0]["id"]
    r = await client.post(f"/v1/mechanics/{mid}/lead", json={"channel": "call"}, headers=headers)
    assert r.status_code == 201

    assert (await client.delete("/v1/me", headers=headers)).status_code == 204

    async with TestSession() as db:
        remaining = await db.scalar(select(func.count()).select_from(MechanicLead))
        assert remaining == 0  # kullanıcının tek lead'i de silinmiş


@pytest.mark.asyncio
async def test_account_deletion_requires_auth_401(client):
    r = await client.delete("/v1/me")
    assert r.status_code == 401


# --------------------------------------------------------------------------- #
# Anonim istatistik (k-anonimlik + consent filtresi)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_stats_hides_small_buckets(client):
    """Eşiğin (5) altındaki sistem kümesi gizlenir; consent gerekir."""
    headers = await register_and_login(client, "stat1@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    # Veri rızası ver.
    await client.patch("/v1/me/consent", json={"data": True}, headers=headers)
    # 4 teşhis (eşik 5) -> küme gizli kalır.
    for _ in range(4):
        await _diagnose(client, headers, vid)
    r = await client.get("/v1/stats/systems", headers=headers)
    assert r.status_code == 200
    assert all(s["sistem"] != "elektrik" or s["count"] >= 5 for s in r.json())
    assert not any(s["sistem"] == "elektrik" for s in r.json())  # 4 < 5 gizli


@pytest.mark.asyncio
async def test_stats_aggregates_with_consent_and_accuracy(client):
    headers = await register_and_login(client, "stat2@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    await client.patch("/v1/me/consent", json={"data": True}, headers=headers)
    # 6 teşhis (>=5), 3'üne 👍, 1'ine 👎 -> doğruluk 3/4 = 0.75.
    for i in range(6):
        fb = True if i < 3 else (False if i == 3 else None)
        await _diagnose(client, headers, vid, feedback=fb)

    r = await client.get("/v1/stats/systems", headers=headers)
    elektrik = next(s for s in r.json() if s["sistem"] == "elektrik")
    assert elektrik["count"] == 6
    assert elektrik["dogrulanan"] == 4
    assert elektrik["dogruluk_orani"] == 0.75


@pytest.mark.asyncio
async def test_stats_excludes_non_consenting_users(client):
    """Rıza vermeyen kullanıcının teşhisleri kümeye girmez."""
    headers = await register_and_login(client, "stat3@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    # Rıza YOK — 6 teşhis.
    for _ in range(6):
        await _diagnose(client, headers, vid)
    r = await client.get("/v1/stats/systems", headers=headers)
    assert r.json() == []  # consent_data False -> küme boş
