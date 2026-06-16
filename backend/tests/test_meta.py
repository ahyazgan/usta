"""Meta/public endpoint testleri: /health ve mağaza-zorunlu /privacy sayfası."""

from httpx import AsyncClient


async def test_health_ok(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "database" in body


async def test_privacy_page_public(client: AsyncClient) -> None:
    """Gizlilik politikası kimlik doğrulama olmadan, HTML olarak erişilebilir olmalı."""
    r = await client.get("/privacy")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    body = r.text
    # Mağaza/KVKK için kritik bölümler sayfada bulunmalı.
    assert "KVKK" in body
    assert "saklanmaz" in body  # teşhis görüntüsü/sesi saklanmıyor güvencesi
    assert "privacy@usta.app" in body


async def test_terms_page_public(client: AsyncClient) -> None:
    """Kullanım Şartları kimlik doğrulama olmadan, HTML olarak erişilebilir olmalı."""
    r = await client.get("/terms")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    body = r.text
    # Apple/güvenlik için kritik ifadeler bulunmalı.
    assert "Kullanım Şartları" in body
    assert "kesin teknik tavsiye" in body  # sorumluluk reddi
    assert "LPG" in body  # LPG müdahale yasağı
