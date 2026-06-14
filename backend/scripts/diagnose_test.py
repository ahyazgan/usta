"""Gerçek araç fotoğraflarıyla canlı backend'in AI teşhisini test eder.

Amaç: en riskli bilinmeyeni — "Claude vision gerçek motor/parça fotoğrafını
doğru okuyor mu?" — uygulama/cihaz/build OLMADAN, doğrudan canlı backend'e
fotoğraf göndererek doğrulamak.

Akış:
  1. Tek seferlik test kullanıcısı kaydeder (varsa giriş yapar) → JWT.
  2. Test aracı oluşturur (CLI'dan marka/model/yıl/yakıt geçilebilir).
  3. Bir klasördeki her fotoğrafı 1024px / JPEG 0.7'ye küçültür (maliyet kuralı),
     /v1/ai/diagnose/image'a gönderir.
  4. Yapısal Türkçe yanıtı (tespit/güven/konum/güvenlik_uyarısı/...) yazdırır.

Kullanım (backend/ içinden):
  .venv/Scripts/python.exe scripts/diagnose_test.py --images ./test-photos --task oil_change
  .venv/Scripts/python.exe scripts/diagnose_test.py --images foto.jpg --make Renault --model Clio --year 2018 --fuel dizel

Notlar:
  * Varsayılan API canlı Render backend'idir; --api ile değiştir.
  * Her teşhis gerçek Claude çağrısıdır (hedef < $0.05); birkaç fotoğraf birkaç sent.
  * İnternet ister; backend uyuyorsa ilk istek ~30sn uyanma bekleyebilir.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import httpx
from PIL import Image

DEFAULT_API = "https://usta-backend.onrender.com"
DEFAULT_EMAIL = "diagtest@ustadiag.com"
DEFAULT_PASSWORD = "DiagTest12345!"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".HEIC"}
MAX_PX = 1024
JPEG_QUALITY = 70


def log(msg: str) -> None:
    print(msg, flush=True)


def collect_images(arg: str) -> list[Path]:
    p = Path(arg)
    if p.is_file():
        return [p]
    if p.is_dir():
        return sorted(
            f for f in p.iterdir() if f.suffix.lower() in {s.lower() for s in IMAGE_SUFFIXES}
        )
    raise SystemExit(f"[hata] Bulunamadı: {arg} (klasör veya dosya ver)")


def to_jpeg_b64(path: Path) -> str:
    """Fotoğrafı max 1024px, JPEG 0.7'ye küçültür → base64 (maliyet kuralı)."""
    import base64

    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((MAX_PX, MAX_PX))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def auth(client: httpx.Client, email: str, password: str) -> str:
    """Kayıt dener; varsa giriş yapar. access_token döndürür."""
    r = client.post("/v1/auth/register", json={"email": email, "password": password})
    if r.status_code in (200, 201):
        log("  ✓ test kullanıcısı oluşturuldu")
        return r.json()["access_token"] if "access_token" in r.json() else _login(client, email, password)
    # Zaten var (409/400) → giriş
    return _login(client, email, password)


def _login(client: httpx.Client, email: str, password: str) -> str:
    r = client.post("/v1/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        raise SystemExit(f"[hata] Giriş başarısız: {r.status_code} {r.text[:200]}")
    log("  ✓ giriş yapıldı")
    return r.json()["access_token"]


def ensure_vehicle(client: httpx.Client, args: argparse.Namespace) -> int:
    """Test aracı oluşturur, id döndürür. Var olanı tekrar kullanmak yerine
    basitçe yeni bir tane açar (test ortamı; sahiplik aynı kullanıcıda)."""
    # Önce mevcut araçlara bak — aynısı varsa onu kullan.
    existing = client.get("/v1/vehicles").json()
    for v in existing if isinstance(existing, list) else []:
        if (
            v.get("make") == args.make
            and v.get("model") == args.model
            and v.get("year") == args.year
        ):
            log(f"  ✓ mevcut araç kullanılıyor (#{v['id']})")
            return int(v["id"])

    body = {
        "make": args.make,
        "model": args.model,
        "year": args.year,
        "fuel_type": args.fuel,
        "vehicle_type": args.vtype,
    }
    r = client.post("/v1/vehicles", json=body)
    if r.status_code not in (200, 201):
        raise SystemExit(f"[hata] Araç oluşturulamadı: {r.status_code} {r.text[:200]}")
    vid = int(r.json()["id"])
    log(f"  ✓ test aracı: {args.make} {args.model} {args.year} {args.fuel} (#{vid})")
    return vid


def diagnose(client: httpx.Client, vehicle_id: int, task: str, b64: str) -> dict:
    r = client.post(
        "/v1/ai/diagnose/image",
        json={
            "vehicle_id": vehicle_id,
            "task": task,
            "frame_base64": b64,
            "media_type": "image/jpeg",
        },
        timeout=90.0,
    )
    if r.status_code != 200:
        return {"_error": f"{r.status_code} {r.text[:300]}"}
    return r.json()


def render(name: str, res: dict) -> None:
    bar = "─" * 60
    log(f"\n{bar}\n📷 {name}\n{bar}")
    if "_error" in res:
        log(f"  ⚠️  HATA: {res['_error']}")
        return
    guven_ikon = {"yuksek": "🟢", "orta": "🟡", "dusuk": "🔴"}.get(res.get("guven", ""), "⚪")
    log(f"  TESPİT      : {res.get('tespit', '—')}")
    log(f"  GÜVEN       : {guven_ikon} {res.get('guven', '—')}")
    log(f"  KONUM       : {res.get('konum_tarifi') or '—'}")
    log(f"  DOĞRU YER?  : {res.get('dogru_yer_mi')}")
    log(f"  SONRAKİ ADIM: {res.get('sonraki_adim', '—')}")
    uyari = res.get("guvenlik_uyarisi")
    if uyari:
        log(f"  ⚠️  GÜVENLİK : {uyari}")
    if res.get("tamirciye_git_onerisi"):
        log("  🔧 TAMİRCİYE GİT önerisi: EVET")
    ce = res.get("cost_estimate")
    if ce:
        log(f"  💰 TAHMİNİ MALİYET: {ce}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Usta canlı AI teşhis testi")
    ap.add_argument("--api", default=DEFAULT_API, help="backend kök URL")
    ap.add_argument("--images", required=True, help="fotoğraf klasörü veya tek dosya")
    ap.add_argument("--task", default="oil_change", help="görev id (örn. oil_change, spark_plugs)")
    ap.add_argument("--make", default="Renault")
    ap.add_argument("--model", default="Clio")
    ap.add_argument("--year", type=int, default=2018)
    ap.add_argument("--fuel", default="dizel", help="benzin|dizel|lpg|hibrit|elektrik")
    ap.add_argument("--vtype", default="araba", help="araba|motosiklet")
    ap.add_argument("--email", default=DEFAULT_EMAIL)
    ap.add_argument("--password", default=DEFAULT_PASSWORD)
    args = ap.parse_args()

    images = collect_images(args.images)
    if not images:
        raise SystemExit(f"[hata] {args.images} içinde fotoğraf yok ({', '.join(sorted(IMAGE_SUFFIXES))})")

    log(f"🔗 API: {args.api}")
    log(f"🖼️  {len(images)} fotoğraf · görev: {args.task}")
    log("⏳ backend uyuyorsa ilk istek ~30sn sürebilir...\n")

    with httpx.Client(base_url=args.api, timeout=90.0) as client:
        token = auth(client, args.email, args.password)
        client.headers["Authorization"] = f"Bearer {token}"
        vehicle_id = ensure_vehicle(client, args)

        for img in images:
            try:
                b64 = to_jpeg_b64(img)
            except Exception as e:  # noqa: BLE001
                log(f"\n📷 {img.name}\n  ⚠️  okunamadı/küçültülemedi: {e}")
                continue
            res = diagnose(client, vehicle_id, args.task, b64)
            render(img.name, res)

    log("\n✅ Bitti. Yanlış okuyan fotoğrafları not al → prompt'ları birlikte iyileştiririz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
