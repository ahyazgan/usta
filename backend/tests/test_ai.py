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


def _dashboard_payload(vehicle_id: int) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "frame_base64": FRAME_B64,
        "media_type": "image/jpeg",
        "user_note": "Panoda ne yanıyor?",
    }


def _dtc_payload(vehicle_id: int) -> dict:
    return {"vehicle_id": vehicle_id, "code": "p0300", "user_note": "Motor teklemesi var"}


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
    # Fiyat şeffaflığı: teşhis yanıtı tamirci maliyet tahmini içerir.
    ce = body["cost_estimate"]
    assert ce is not None
    assert ce["low_try"] > 0 and ce["high_try"] >= ce["low_try"]
    assert ce["source"] in {"seed", "community"} and ce["currency"] == "TRY"


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
# Gösterge paneli uyarı ışığı tanıma
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_dashboard_diagnose_happy(client, fake_claude):
    headers = await register_and_login(client, "pano1@usta.app")
    vehicle = await create_vehicle(client, headers)

    r = await client.post(
        "/v1/ai/diagnose/dashboard", json=_dashboard_payload(vehicle["id"]), headers=headers
    )
    assert r.status_code == 200
    body = r.json()
    assert "büyük ihtimalle" in body["tespit"].casefold()
    assert body["guven"] in {"yuksek", "orta", "dusuk"}
    assert isinstance(body["isiklar"], list) and len(body["isiklar"]) >= 1
    light = body["isiklar"][0]
    assert light["renk"] in {"kirmizi", "sari", "yesil", "mavi", "bilinmiyor"}
    assert light["aciliyet"] in {"dusuk", "orta", "yuksek"}
    assert body["en_yuksek_aciliyet"] in {"dusuk", "orta", "yuksek"}
    # Vision modeli sonnet olmalı (Opus yasak).
    assert "opus" not in fake_claude.calls[0]["model"].lower()
    assert "sonnet" in fake_claude.calls[0]["model"].lower()


@pytest.mark.asyncio
async def test_dashboard_requires_auth_401(client):
    r = await client.post("/v1/ai/diagnose/dashboard", json=_dashboard_payload(1))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_validation_422(client):
    headers = await register_and_login(client, "pano2@usta.app")
    # frame_base64 eksik
    r = await client.post(
        "/v1/ai/diagnose/dashboard", json={"vehicle_id": 1}, headers=headers
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_dashboard_other_vehicle_403(client):
    owner = await register_and_login(client, "panoowner@usta.app")
    vehicle = await create_vehicle(client, owner)
    intruder = await register_and_login(client, "panointruder@usta.app")
    r = await client.post(
        "/v1/ai/diagnose/dashboard", json=_dashboard_payload(vehicle["id"]), headers=intruder
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_red_light_forces_mechanic(client, fake_claude):
    """KIRMIZI ışık => her zaman tamirci + güvenlik uyarısı, aciliyet yükselir."""
    headers = await register_and_login(client, "pano3@usta.app")
    vehicle = await create_vehicle(client, headers)

    fake_claude.dashboard_response = {
        "tespit": "Büyük ihtimalle kırmızı yağ basıncı ışığı yanıyor.",
        "guven": "orta",
        "isiklar": [
            {
                "isim": "Yağ basıncı uyarısı",
                "renk": "kirmizi",
                "anlam": "Büyük ihtimalle yağ basıncı düşük.",
                "aciliyet": "dusuk",  # model yanlış verse de sistem yükseltmeli
                "ne_yapmali": "Devam et.",
            }
        ],
        "en_yuksek_aciliyet": "dusuk",  # sistem yeniden hesaplamalı
        "guvenlik_uyarisi": None,
        "sonraki_adim": "Sürmeye devam et.",
        "tamirciye_git_onerisi": False,
    }
    r = await client.post(
        "/v1/ai/diagnose/dashboard", json=_dashboard_payload(vehicle["id"]), headers=headers
    )
    body = r.json()
    assert body["tamirciye_git_onerisi"] is True
    assert body["guvenlik_uyarisi"], "kırmızı ışıkta güvenlik uyarısı zorunlu"


@pytest.mark.asyncio
async def test_dashboard_hedge_phrase_enforced(client, fake_claude):
    """Kesin teşhis dili geldiğinde 'büyük ihtimalle' eklenmeli."""
    headers = await register_and_login(client, "pano4@usta.app")
    vehicle = await create_vehicle(client, headers)

    fake_claude.dashboard_response = {
        "tespit": "Motor arıza ışığı kesinlikle ateşleme arızası.",
        "guven": "yuksek",
        "isiklar": [],
        "en_yuksek_aciliyet": "dusuk",
        "guvenlik_uyarisi": None,
        "sonraki_adim": "Tekrar dene.",
        "tamirciye_git_onerisi": False,
    }
    r = await client.post(
        "/v1/ai/diagnose/dashboard", json=_dashboard_payload(vehicle["id"]), headers=headers
    )
    assert "büyük ihtimalle" in r.json()["tespit"].casefold()


@pytest.mark.asyncio
async def test_dashboard_per_light_anlam_hedged(client, fake_claude):
    """Her ışığın `anlam`'ı da hedge'lenmeli; kesin dil ('kesinlikle') yumuşatılmalı."""
    headers = await register_and_login(client, "pano5@usta.app")
    vehicle = await create_vehicle(client, headers)

    fake_claude.dashboard_response = {
        "tespit": "Büyük ihtimalle bir uyarı ışığı yanıyor.",
        "guven": "orta",
        "isiklar": [
            {
                "isim": "ABS uyarısı",
                "renk": "sari",
                "anlam": "Kesinlikle ABS arızası var.",  # kesin dil — yumuşatılmalı
                "aciliyet": "orta",
                "ne_yapmali": "Kontrol ettir.",
            }
        ],
        "en_yuksek_aciliyet": "orta",
        "guvenlik_uyarisi": None,
        "sonraki_adim": "Tamirciye uğra.",
        "tamirciye_git_onerisi": True,
    }
    r = await client.post(
        "/v1/ai/diagnose/dashboard", json=_dashboard_payload(vehicle["id"]), headers=headers
    )
    anlam = r.json()["isiklar"][0]["anlam"].casefold()
    assert "büyük ihtimalle" in anlam
    assert "kesinlikle" not in anlam


# --------------------------------------------------------------------------- #
# Arıza kodu (OBD-II / DTC) açıklama
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_dtc_diagnose_happy(client, fake_claude):
    headers = await register_and_login(client, "dtc1@usta.app")
    vehicle = await create_vehicle(client, headers)

    r = await client.post("/v1/ai/diagnose/code", json=_dtc_payload(vehicle["id"]), headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "büyük ihtimalle" in body["tespit"].casefold()
    assert body["guven"] in {"yuksek", "orta", "dusuk"}
    assert body["aciliyet"] in {"dusuk", "orta", "yuksek"}
    assert isinstance(body["olasi_nedenler"], list) and len(body["olasi_nedenler"]) >= 1
    assert "baslik" in body and body["kod"]
    # Metin analizi → sonnet (Opus yasak).
    assert "opus" not in fake_claude.calls[0]["model"].lower()
    assert "sonnet" in fake_claude.calls[0]["model"].lower()


@pytest.mark.asyncio
async def test_dtc_requires_auth_401(client):
    r = await client.post("/v1/ai/diagnose/code", json=_dtc_payload(1))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_dtc_validation_422(client):
    headers = await register_and_login(client, "dtc2@usta.app")
    # code eksik
    r = await client.post("/v1/ai/diagnose/code", json={"vehicle_id": 1}, headers=headers)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_dtc_other_vehicle_403(client):
    owner = await register_and_login(client, "dtcowner@usta.app")
    vehicle = await create_vehicle(client, owner)
    intruder = await register_and_login(client, "dtcintruder@usta.app")
    r = await client.post("/v1/ai/diagnose/code", json=_dtc_payload(vehicle["id"]), headers=intruder)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_dtc_rate_limit_429(client):
    headers = await register_and_login(client, "dtc3@usta.app")
    vehicle = await create_vehicle(client, headers)

    async def _always_limited():
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="limit")

    app.dependency_overrides[enforce_rate_limit] = _always_limited
    try:
        r = await client.post("/v1/ai/diagnose/code", json=_dtc_payload(vehicle["id"]), headers=headers)
        assert r.status_code == 429
    finally:
        app.dependency_overrides.pop(enforce_rate_limit, None)


@pytest.mark.asyncio
async def test_dtc_not_drivable_forces_mechanic(client, fake_claude):
    """surulebilir_mi=False => tamirci + güvenlik uyarısı zorunlu."""
    headers = await register_and_login(client, "dtc4@usta.app")
    vehicle = await create_vehicle(client, headers)

    fake_claude.dtc_response = {
        "tespit": "Büyük ihtimalle ciddi bir ateşleme sorunu.",
        "guven": "orta",
        "kod": "P0301",
        "baslik": "1. silindir ateşleme teklemesi",
        "olasi_nedenler": ["Buji", "Bobin"],
        "aciliyet": "dusuk",  # tutarsız; sistem yükseltmeli değil ama surulebilir False
        "surulebilir_mi": False,
        "sonraki_adim": "Devam et.",
        "guvenlik_uyarisi": None,
        "tamirciye_git_onerisi": False,
    }
    r = await client.post("/v1/ai/diagnose/code", json=_dtc_payload(vehicle["id"]), headers=headers)
    body = r.json()
    assert body["tamirciye_git_onerisi"] is True
    assert body["guvenlik_uyarisi"], "sürülemez kodda güvenlik uyarısı zorunlu"


@pytest.mark.asyncio
async def test_dtc_hararet_triggers_warning(client, fake_claude):
    """'hararet' geçen yanıtta uyarı boşsa sistem doldurmalı (tetikleyici kelime)."""
    headers = await register_and_login(client, "dtc5@usta.app")
    vehicle = await create_vehicle(client, headers)

    fake_claude.dtc_response = {
        "tespit": "Büyük ihtimalle soğutma sıcaklığı sensörüyle ilgili bir kod.",
        "guven": "orta",
        "kod": "P0118",
        "baslik": "Motor hararet sensörü yüksek sinyal",
        "olasi_nedenler": ["Hararet sensörü arızası", "Kablo/konnektör"],
        "aciliyet": "orta",
        "surulebilir_mi": True,
        "sonraki_adim": "Hararet göstergesini izle; yükselirse dur.",
        "guvenlik_uyarisi": None,
        "tamirciye_git_onerisi": True,
    }
    r = await client.post("/v1/ai/diagnose/code", json=_dtc_payload(vehicle["id"]), headers=headers)
    assert r.json()["guvenlik_uyarisi"], "hararet geçen yanıtta güvenlik uyarısı zorunlu"


# --------------------------------------------------------------------------- #
# Ses teşhisi
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_sound_diagnose_happy(client, fake_claude):
    headers = await register_and_login(client, "ses1@usta.app")
    vehicle = await create_vehicle(client, headers)

    r = await client.post("/v1/ai/diagnose/sound", json=_sound_payload(vehicle["id"]), headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["ses_kategorisi"] in {
        "tikirti", "kayis_sesi", "metalik_vuruntu", "islik", "egzoz_patlamasi", "normal", "belirsiz",
    }
    # Fiyat şeffaflığı: ses teşhisi de tamirci maliyet tahmini içerir.
    assert body["cost_estimate"] is not None
    assert body["cost_estimate"]["high_try"] >= body["cost_estimate"]["low_try"] > 0


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


# --------------------------------------------------------------------------- #
# AI dayanıklılığı — temiz hata eşlemesi (çıplak 500 yerine)
# --------------------------------------------------------------------------- #


class _RaisingClaude:
    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    async def complete_json(self, **kwargs):
        raise self.exc


class _BadDataClaude:
    """Şemaya uymayan veri döndürür (eksik alanlar)."""

    async def complete_json(self, **kwargs):
        from app.services.ai.claude_client import ClaudeResult

        return ClaudeResult(data={"tespit": "eksik"}, tokens_in=10, tokens_out=5)


async def _setup_vehicle(client):
    headers = await register_and_login(client, f"resil{id(client)}@usta.app")
    vehicle = await create_vehicle(client, headers)
    return headers, vehicle["id"]


@pytest.mark.asyncio
async def test_ai_not_configured_returns_503(client):
    from app.domain.ai_errors import AINotConfigured
    from app.services.ai.claude_client import get_claude_client

    headers, vid = await _setup_vehicle(client)
    app.dependency_overrides[get_claude_client] = lambda: _RaisingClaude(AINotConfigured())
    r = await client.post("/v1/ai/diagnose/image", json=_image_payload(vid), headers=headers)
    assert r.status_code == 503
    assert r.json()["code"] == "ai_not_configured"


@pytest.mark.asyncio
async def test_ai_upstream_error_returns_502(client):
    from app.domain.ai_errors import AIUpstreamError
    from app.services.ai.claude_client import get_claude_client

    headers, vid = await _setup_vehicle(client)
    app.dependency_overrides[get_claude_client] = lambda: _RaisingClaude(AIUpstreamError())
    r = await client.post("/v1/ai/diagnose/image", json=_image_payload(vid), headers=headers)
    assert r.status_code == 502
    assert r.json()["code"] == "ai_upstream"


@pytest.mark.asyncio
async def test_ai_rate_limited_returns_429(client):
    from app.domain.ai_errors import AIRateLimited
    from app.services.ai.claude_client import get_claude_client

    headers, vid = await _setup_vehicle(client)
    app.dependency_overrides[get_claude_client] = lambda: _RaisingClaude(AIRateLimited())
    r = await client.post("/v1/ai/diagnose/sound", json=_sound_payload(vid), headers=headers)
    assert r.status_code == 429
    assert r.json()["code"] == "ai_rate_limited"


@pytest.mark.asyncio
async def test_ai_bad_schema_returns_502(client):
    from app.services.ai.claude_client import get_claude_client

    headers, vid = await _setup_vehicle(client)
    app.dependency_overrides[get_claude_client] = lambda: _BadDataClaude()
    r = await client.post("/v1/ai/diagnose/image", json=_image_payload(vid), headers=headers)
    assert r.status_code == 502
    assert r.json()["code"] == "ai_upstream"


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
