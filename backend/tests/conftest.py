"""Test altyapısı: in-memory SQLite, sahte Claude istemcisi, kimlik yardımcıları.

Claude API HER ZAMAN mock'lanır — testlerde gerçek ağ çağrısı yapılmaz.
"""

from __future__ import annotations

import os

# App import edilmeden ÖNCE ayarları test moduna al.
os.environ.setdefault("USTA_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("USTA_ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("USTA_DEBUG", "true")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.rate_limit import enforce_rate_limit, get_rate_limiter
from app.database import Base, get_db
from app.main import app
from app.services.ai.claude_client import ClaudeResult, get_claude_client

# Tek bağlantılı paylaşımlı in-memory veritabanı.
test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


# --------------------------------------------------------------------------- #
# Sahte Claude istemcisi
# --------------------------------------------------------------------------- #

DEFAULT_IMAGE = {
    "tespit": "Büyük ihtimalle yağ filtresi görünüyor.",
    "guven": "orta",
    "konum_tarifi": "merkez",
    "dogru_yer_mi": True,
    "sonraki_adim": "Filtreyi saat yönünün tersine çevir.",
    "guvenlik_uyarisi": None,
    "tamirciye_git_onerisi": False,
}

DEFAULT_SOUND = {
    "tespit": "Büyük ihtimalle kayış sesi var.",
    "guven": "orta",
    "ses_kategorisi": "kayis_sesi",
    "aciliyet": "dusuk",
    "guvenlik_uyarisi": None,
    "sonraki_adim": "Kayış gerginliğini bir ustaya kontrol ettir.",
    "tamirciye_git_onerisi": False,
}

DEFAULT_DASHBOARD = {
    "tespit": "Büyük ihtimalle sarı motor arıza ışığı yanıyor.",
    "guven": "orta",
    "isiklar": [
        {
            "isim": "Motor arıza lambası (check engine)",
            "renk": "sari",
            "anlam": "Büyük ihtimalle motor yönetiminde bir arıza kodu var.",
            "aciliyet": "orta",
            "ne_yapmali": "Yakın zamanda arıza kodunu okut.",
        }
    ],
    "en_yuksek_aciliyet": "orta",
    "guvenlik_uyarisi": None,
    "sonraki_adim": "Yakın zamanda tamirciye uğra.",
    "tamirciye_git_onerisi": True,
}


DEFAULT_DTC = {
    "tespit": "Büyük ihtimalle P0300, çoklu silindir ateşleme teklemesi demek.",
    "guven": "orta",
    "kod": "P0300",
    "baslik": "Rastgele/çoklu silindir ateşleme teklemesi",
    "olasi_nedenler": ["Eskimiş buji veya bobin", "Yakıt karışımı sorunu"],
    "aciliyet": "orta",
    "surulebilir_mi": False,
    "sonraki_adim": "Bujileri ve bobinleri kontrol ettir.",
    "guvenlik_uyarisi": None,
    "tamirciye_git_onerisi": True,
}


DEFAULT_SYMPTOM = {
    "tespit": "Büyük ihtimalle rölantide düzensiz çalışma var.",
    "guven": "orta",
    "olasi_nedenler": ["Eskimiş buji", "Hava kaçağı"],
    "ariza_sistem": "atesleme",
    "aciliyet": "orta",
    "sonraki_adim": "Bujileri kontrol ettir.",
    "guvenlik_uyarisi": None,
    "tamirciye_git_onerisi": True,
}


class FakeClaudeClient:
    def __init__(self) -> None:
        self.image_response = dict(DEFAULT_IMAGE)
        self.sound_response = dict(DEFAULT_SOUND)
        self.dashboard_response = dict(DEFAULT_DASHBOARD)
        self.dtc_response = dict(DEFAULT_DTC)
        self.symptom_response = dict(DEFAULT_SYMPTOM)
        self.tokens_in = 120
        self.tokens_out = 40
        self.calls: list[dict] = []

    async def complete_json(self, *, model, system, content, max_tokens=None) -> ClaudeResult:
        self.calls.append({"model": model, "system": system, "content": content})
        if isinstance(content, list):
            # Görüntü tabanlı çağrılar; pano prompt'u ile görüntü teşhisini ayır.
            data = self.dashboard_response if "PANO" in (system or "") else self.image_response
        elif "ARIZA KODU" in (system or ""):
            data = self.dtc_response
        elif "BELİRTİ" in (system or ""):
            data = self.symptom_response
        else:
            data = self.sound_response
        return ClaudeResult(data=dict(data), tokens_in=self.tokens_in, tokens_out=self.tokens_out)


@pytest_asyncio.fixture
async def fake_claude() -> FakeClaudeClient:
    return FakeClaudeClient()


# --------------------------------------------------------------------------- #
# DB + istemci fixture'ları
# --------------------------------------------------------------------------- #


@pytest_asyncio.fixture
async def client(fake_claude: FakeClaudeClient):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_claude_client] = lambda: fake_claude
    get_rate_limiter().reset()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# --------------------------------------------------------------------------- #
# Kimlik yardımcıları
# --------------------------------------------------------------------------- #


async def register_and_login(client: AsyncClient, email: str = "a@usta.app", password: str = "parola1234") -> dict:
    """Kullanıcı oluştur, giriş yap, Authorization header'ı döndür."""
    await client.post("/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def create_vehicle(client: AsyncClient, headers: dict) -> dict:
    payload = {
        "make": "Fiat",
        "model": "Egea",
        "year": 2019,
        "fuel_type": "lpg",
        "engine_code": "198A4000",
        "current_km": 84210,
        "spec": {
            "oil_spec": "5W-30",
            "oil_capacity_l": 4.3,
            "oil_drain_bolt_size": "13mm",
            "oil_drain_location": "karter alt-arka",
            "oil_filter_part": "55256470",
            "spark_plug_part": "NGK ...",
            "battery_spec": "60Ah",
            "battery_location": "motor bölmesi sol",
        },
    }
    resp = await client.post("/v1/vehicles", json=payload, headers=headers)
    return resp.json()
