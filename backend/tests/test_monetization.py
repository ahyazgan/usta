"""Premium/abonelik + faturalandırma webhook + parça-niyet + admin paneli."""

import pytest

from app.config import get_settings

from .conftest import create_vehicle, register_and_login


# --- Abonelik okuma + premium kapısı --------------------------------------- #

@pytest.mark.asyncio
async def test_subscription_default_free(client):
    headers = await register_and_login(client, "sub1@usta.app")
    r = await client.get("/v1/me/subscription", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["tier"] == "free" and body["is_premium"] is False
    assert body["live_unlimited"] is False
    assert body["free_live_seconds_remaining"] == get_settings().free_live_seconds_per_month


@pytest.mark.asyncio
async def test_subscription_requires_auth_401(client):
    assert (await client.get("/v1/me/subscription")).status_code == 401


# --- Faturalandırma webhook → premium -------------------------------------- #

@pytest.mark.asyncio
async def test_billing_webhook_not_configured_503(client):
    r = await client.post("/v1/billing/webhook", json={"app_user_id": "x@y.z", "premium": True})
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_billing_webhook_wrong_secret_403(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "billing_webhook_secret", "topsecret")
    r = await client.post(
        "/v1/billing/webhook",
        json={"app_user_id": "x@y.z", "premium": True},
        headers={"X-Webhook-Secret": "wrong"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_billing_webhook_grants_premium(client, monkeypatch):
    email = "premium@usta.app"
    headers = await register_and_login(client, email)
    monkeypatch.setattr(get_settings(), "billing_webhook_secret", "topsecret")

    wh = await client.post(
        "/v1/billing/webhook",
        json={"app_user_id": email, "premium": True},
        headers={"X-Webhook-Secret": "topsecret"},
    )
    assert wh.status_code == 204

    sub = (await client.get("/v1/me/subscription", headers=headers)).json()
    assert sub["tier"] == "premium" and sub["is_premium"] is True
    assert sub["free_live_seconds_remaining"] is None  # premium → sınırsız


# --- Parça-niyet (tıklama) + admin paneli ---------------------------------- #

@pytest.mark.asyncio
async def test_buy_intent_logged(client):
    headers = await register_and_login(client, "buy1@usta.app")
    vehicle = await create_vehicle(client, headers)
    r = await client.post(
        "/v1/parts/buy-intent",
        json={"vehicle_id": vehicle["id"], "task": "oil_change", "part_label": "Yağ filtresi"},
        headers=headers,
    )
    assert r.status_code == 201 and r.json()["id"] >= 1


@pytest.mark.asyncio
async def test_buy_intent_requires_auth_401(client):
    r = await client.post("/v1/parts/buy-intent", json={"vehicle_id": 1, "part_label": "x"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_admin_dashboard_served(client):
    """Panel HTML token gerektirmez (veriyi client-side token'la çeker)."""
    r = await client.get("/v1/admin/dashboard")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Yönetim Paneli" in r.text


@pytest.mark.asyncio
async def test_admin_stats_not_configured_503(client):
    assert (await client.get("/v1/admin/stats")).status_code == 503


@pytest.mark.asyncio
async def test_admin_stats_wrong_token_403(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "admin_token", "adm")
    r = await client.get("/v1/admin/stats", headers={"X-Admin-Token": "nope"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_stats_aggregates(client, monkeypatch):
    headers = await register_and_login(client, "buy2@usta.app")
    vehicle = await create_vehicle(client, headers)
    for _ in range(3):
        await client.post(
            "/v1/parts/buy-intent",
            json={"vehicle_id": vehicle["id"], "part_label": "Buji"},
            headers=headers,
        )
    monkeypatch.setattr(get_settings(), "admin_token", "adm")
    r = await client.get("/v1/admin/stats", headers={"X-Admin-Token": "adm"})
    assert r.status_code == 200
    body = r.json()
    assert body["part_intents"]["total"] >= 3
    assert any(p["part"] == "Buji" and p["intents"] >= 3 for p in body["part_intents"]["top_parts"])
    assert body["users"]["total"] >= 1
    assert "mechanic_leads" in body and "live" in body
