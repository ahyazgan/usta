"""Auth endpoint testleri: happy + 401 + 422 + token yenileme."""

import pytest

from .conftest import register_and_login


@pytest.mark.asyncio
async def test_register_login_happy(client):
    r = await client.post("/v1/auth/register", json={"email": "u1@usta.app", "password": "parola1234"})
    assert r.status_code == 201
    assert r.json()["email"] == "u1@usta.app"
    assert r.json()["subscription_tier"] == "free"

    r = await client.post("/v1/auth/login", json={"email": "u1@usta.app", "password": "parola1234"})
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_conflict(client):
    await client.post("/v1/auth/register", json={"email": "dup@usta.app", "password": "parola1234"})
    r = await client.post("/v1/auth/register", json={"email": "dup@usta.app", "password": "parola1234"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password_401(client):
    await client.post("/v1/auth/register", json={"email": "u2@usta.app", "password": "parola1234"})
    r = await client.post("/v1/auth/login", json={"email": "u2@usta.app", "password": "yanlis9999"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_register_validation_422(client):
    # parola çok kısa (min 8)
    r = await client.post("/v1/auth/register", json={"email": "u3@usta.app", "password": "kisa"})
    assert r.status_code == 422
    # eksik alan
    r = await client.post("/v1/auth/register", json={"email": "u3@usta.app"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_refresh_rotation(client):
    await client.post("/v1/auth/register", json={"email": "u4@usta.app", "password": "parola1234"})
    login = await client.post("/v1/auth/login", json={"email": "u4@usta.app", "password": "parola1234"})
    refresh_token = login.json()["refresh_token"]

    r = await client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert r.json()["access_token"]

    # Eski token rotasyonla iptal edildi -> tekrar kullanılamaz.
    r2 = await client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_401(client):
    r = await client.post("/v1/auth/refresh", json={"refresh_token": "gecersiz-token-xxxxxx"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_requires_jwt_401(client):
    r = await client.get("/v1/vehicles")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_helper_returns_valid_header(client):
    headers = await register_and_login(client, "u5@usta.app")
    r = await client.get("/v1/vehicles", headers=headers)
    assert r.status_code == 200
