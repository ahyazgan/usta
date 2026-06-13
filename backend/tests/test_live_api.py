"""Canlı oturum uçları: 503 (yapılandırılmamış), 401, limit (402), happy, end."""

import pytest

from app.config import get_settings
from app.services.ai import live_session_service

from .conftest import create_vehicle, register_and_login


async def _fake_mint(config, settings):
    # Gerçek Google çağrısını test etme; config doğru kuruldu mu kontrol et.
    assert config["system_instruction"] and config["tools"]
    return "ephemeral-token-xyz"


@pytest.mark.asyncio
async def test_live_session_not_configured_503(client):
    """Gemini anahtarı yoksa (varsayılan) canlı mod 503."""
    headers = await register_and_login(client, "live1@usta.app")
    vehicle = await create_vehicle(client, headers)
    r = await client.post(
        "/v1/live/session", json={"vehicle_id": vehicle["id"]}, headers=headers
    )
    assert r.status_code == 503
    assert r.json()["code"] == "ai_not_configured"


@pytest.mark.asyncio
async def test_live_session_requires_auth_401(client):
    r = await client.post("/v1/live/session", json={"vehicle_id": 1})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_live_session_happy(client, monkeypatch):
    headers = await register_and_login(client, "live2@usta.app")
    vehicle = await create_vehicle(client, headers)
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")
    monkeypatch.setattr(live_session_service, "mint_ephemeral_token", _fake_mint)

    r = await client.post(
        "/v1/live/session",
        json={"vehicle_id": vehicle["id"], "task": "oil_change", "lang": "en"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token"] == "ephemeral-token-xyz"
    assert body["language"] == "en" and body["voice"]
    assert body["live_usage_id"] >= 1 and body["max_seconds"] > 0
    # GÜVENLİK: system_instruction istemciye sızmamalı.
    assert "system_instruction" not in body


@pytest.mark.asyncio
async def test_live_session_limit_reached_402(client, monkeypatch):
    headers = await register_and_login(client, "live3@usta.app")
    vehicle = await create_vehicle(client, headers)
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")
    monkeypatch.setattr(live_session_service, "mint_ephemeral_token", _fake_mint)
    # Ücretsiz limiti 0 yap → ilk oturumda dolmuş say (premium değil).
    monkeypatch.setattr(get_settings(), "free_live_seconds_per_month", 0)

    r = await client.post(
        "/v1/live/session", json={"vehicle_id": vehicle["id"]}, headers=headers
    )
    assert r.status_code == 402
    assert r.json()["code"] == "live_limit_reached"


@pytest.mark.asyncio
async def test_live_session_end_records_seconds(client, monkeypatch):
    headers = await register_and_login(client, "live4@usta.app")
    vehicle = await create_vehicle(client, headers)
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")
    monkeypatch.setattr(live_session_service, "mint_ephemeral_token", _fake_mint)

    start = await client.post(
        "/v1/live/session", json={"vehicle_id": vehicle["id"]}, headers=headers
    )
    uid = start.json()["live_usage_id"]
    end = await client.post(
        f"/v1/live/session/{uid}/end", json={"seconds": 120}, headers=headers
    )
    assert end.status_code == 204
