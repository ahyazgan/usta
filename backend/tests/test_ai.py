"""AI teşhis testleri: happy + 401 + 429 + 422 + sahiplik + GÜVENLİK senaryoları.

Claude her zaman mock'lanır (fake_claude). Güvenlik kuralları assert edilir.
"""

import base64

import pytest

from app.core.rate_limit import enforce_rate_limit
from app.main import app

from .conftest import create_vehicle, register_and_login

FRAME_B64 = base64.b64encode(b"sahte-jpeg-baytlari" * 4).decode()


def _image_payload(vehicle_id: int) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "task": "oil_change",
        "step": 3,
        "frame_base64": FRAME_B64,
        "media_type": "image/jpeg",
        "user_note": "Doğru cıvata mı?",
    }


def _sound_payload(vehicle_id: int) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "user_description": "Rolantide hafif tıkırtı duyuyorum",
        "condition": "rolanti",
    }


# --------------------------------------------------------------------------- #
# Görüntü teşhisi
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_image_diagnose_happy(client, fake_claude):
    headers = await register_and_login(client, "ai1@usta.app")
    vehicle = await create_vehicle(client, headers)

    r = await client.post("/v1/ai/diagnose/image", json=_image_payload(vehicle["id"]), headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["guven"] in {"yuksek", "orta", "dusuk"}
    assert body["konum_tarifi"] == "merkez"
    assert "büyük ihtimalle" in body["tespit"].casefold()
    # Vision modeli sonnet olmalı (Opus yasak).
    assert "opus" not in fake_claude.calls[0]["model"].lower()
    assert "sonnet" in fake_claude.calls[0]["model"].lower()


@pytest.mark.asyncio
async def test_image_diagnose_requires_auth_401(client):
    r = await client.post("/v1/ai/diagnose/image", json=_image_payload(1))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_image_diagnose_validation_422(client):
    headers = await register_and_login(client, "ai2@usta.app")
    # frame_base64 eksik
    r = await client.post(
        "/v1/ai/diagnose/image",
        json={"vehicle_id": 1, "task": "oil_change"},
        headers=headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_image_diagnose_other_vehicle_403(client):
    owner = await register_and_login(client, "owner2@usta.app")
    vehicle = await create_vehicle(client, owner)
    intruder = await register_and_login(client, "intruder2@usta.app")

    r = await client.post(
        "/v1/ai/diagnose/image", json=_image_payload(vehicle["id"]), headers=intruder
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_image_diagnose_rate_limit_429(client):
    headers = await register_and_login(client, "ai3@usta.app")
    vehicle = await create_vehicle(client, headers)

    async def _always_limited():
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="limit")

    app.dependency_overrides[enforce_rate_limit] = _always_limited
    try:
        r = await client.post(
            "/v1/ai/diagnose/image", json=_image_payload(vehicle["id"]), headers=headers
        )
        assert r.status_code == 429
    finally:
        app.dependency_overrides.pop(enforce_rate_limit, None)


# --------------------------------------------------------------------------- #
# GÜVENLİK senaryoları (görüntü)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_image_safety_warning_injected(client, fake_claude):
    """Sıcak motor/kriko geçen yanıtta uyarı boşsa, sistem doldurmalı."""
    headers = await register_and_login(client, "safe1@usta.app")
    vehicle = await create_vehicle(client, headers)

    fake_claude.image_response = {
        "tespit": "Büyük ihtimalle tahliye cıvatası görünüyor.",
        "guven": "orta",
        "konum_tarifi": "merkez",
        "dogru_yer_mi": True,
        "sonraki_adim": "Araç kriko üzerindeyken cıvatayı gevşet.",
        "guvenlik_uyarisi": None,
        "tamirciye_git_onerisi": False,
    }
    r = await client.post("/v1/ai/diagnose/image", json=_image_payload(vehicle["id"]), headers=headers)
    assert r.status_code == 200
    assert r.json()["guvenlik_uyarisi"], "kriko geçen yanıtta güvenlik uyarısı zorunlu"


@pytest.mark.asyncio
async def test_image_hedge_phrase_enforced(client, fake_claude):
    """Kesin teşhis dili geldiğinde 'büyük ihtimalle' eklenmeli."""
    headers = await register_and_login(client, "safe2@usta.app")
    vehicle = await create_vehicle(client, headers)

    fake_claude.image_response = {
        "tespit": "Yağ tıpası tam burada.",
        "guven": "yuksek",
        "konum_tarifi": "merkez",
        "dogru_yer_mi": True,
        "sonraki_adim": "Cıvatayı gevşet.",
        "guvenlik_uyarisi": None,
        "tamirciye_git_onerisi": False,
    }
    r = await client.post("/v1/ai/diagnose/image", json=_image_payload(vehicle["id"]), headers=headers)
    assert "büyük ihtimalle" in r.json()["tespit"].casefold()


@pytest.mark.asyncio
async def test_image_lpg_intervention_blocked(client, fake_claude):
    """LPG müdahale tarifi engellenip tamirciye yönlendirilmeli."""
    headers = await register_and_login(client, "safe3@usta.app")
    vehicle = await create_vehicle(client, headers)

    fake_claude.image_response = {
        "tespit": "Büyük ihtimalle LPG regülatörü görünüyor.",
        "guven": "orta",
        "konum_tarifi": "sol-orta",
        "dogru_yer_mi": True,
        "sonraki_adim": "LPG regülatörünü sökerek ayar yap.",
        "guvenlik_uyarisi": None,
        "tamirciye_git_onerisi": False,
    }
    r = await client.post("/v1/ai/diagnose/image", json=_image_payload(vehicle["id"]), headers=headers)
    body = r.json()
    assert body["tamirciye_git_onerisi"] is True
    assert "lpg" in (body["guvenlik_uyarisi"] or "").casefold()
    assert "sök" not in body["sonraki_adim"].casefold()


# --------------------------------------------------------------------------- #
# Ses teşhisi
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_sound_diagnose_happy(client, fake_claude):
    headers = await register_and_login(client, "ses1@usta.app")
    vehicle = await create_vehicle(client, headers)

    r = await client.post("/v1/ai/diagnose/sound", json=_sound_payload(vehicle["id"]), headers=headers)
    assert r.status_code == 200
    assert r.json()["ses_kategorisi"] in {
        "tikirti", "kayis_sesi", "metalik_vuruntu", "islik", "egzoz_patlamasi", "normal", "belirsiz",
    }


@pytest.mark.asyncio
async def test_sound_diagnose_validation_422(client):
    headers = await register_and_login(client, "ses2@usta.app")
    # geçersiz condition
    r = await client.post(
        "/v1/ai/diagnose/sound",
        json={"vehicle_id": 1, "user_description": "ses", "condition": "uzayda"},
        headers=headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_sound_metalik_vuruntu_forces_mechanic(client, fake_claude):
    """metalik_vuruntu => her zaman acil + tamirci."""
    headers = await register_and_login(client, "ses3@usta.app")
    vehicle = await create_vehicle(client, headers)

    fake_claude.sound_response = {
        "tespit": "Büyük ihtimalle yükte metalik vuruntu var.",
        "guven": "orta",
        "ses_kategorisi": "metalik_vuruntu",
        "aciliyet": "dusuk",  # model yanlış verse bile sistem yükseltmeli
        "guvenlik_uyarisi": None,
        "sonraki_adim": "Devam et.",
        "tamirciye_git_onerisi": False,
    }
    r = await client.post("/v1/ai/diagnose/sound", json=_sound_payload(vehicle["id"]), headers=headers)
    body = r.json()
    assert body["aciliyet"] == "yuksek"
    assert body["tamirciye_git_onerisi"] is True
    assert body["guvenlik_uyarisi"]


@pytest.mark.asyncio
async def test_tokens_logged_to_ai_session(client, fake_claude):
    """Token sayıları AISession'a yazılmalı (maliyet denetimi)."""
    from sqlalchemy import select

    from app.domain.models import AISession
    from tests.conftest import TestSession

    headers = await register_and_login(client, "tok@usta.app")
    vehicle = await create_vehicle(client, headers)
    await client.post("/v1/ai/diagnose/image", json=_image_payload(vehicle["id"]), headers=headers)

    async with TestSession() as s:
        rows = list(await s.scalars(select(AISession)))
    assert len(rows) == 1
    assert rows[0].tokens_in == fake_claude.tokens_in
    assert rows[0].tokens_out == fake_claude.tokens_out
    assert "opus" not in rows[0].model.lower()
