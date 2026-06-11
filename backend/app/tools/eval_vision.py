"""Vision teşhis değerlendirme + maliyet harness'i (cost-guard).

İki mod:
- ANTHROPIC_API_KEY varsa: bir klasördeki örnek kareleri gerçek modele gönderir,
  JSON şema uyumunu + güvenlik kurallarını + token/maliyet metriklerini raporlar.
- Anahtar yoksa (veya --offline): gerçek çağrı yapmadan şema + güvenlik zorlamasını
  ve maliyet formülünü canlı örneklerle doğrular.

Kullanım:
  # Gerçek (anahtar gerekli):
  ANTHROPIC_API_KEY=sk-ant-... python -m app.tools.eval_vision \
      --images ./ornek_kareler --task oil_change \
      --make Fiat --model Egea --year 2019 --fuel lpg --engine 843A1000

  # Çevrimdışı öz-denetim:
  python -m app.tools.eval_vision --offline

Doğru maliyet için kareler 1024px JPEG 0.7 olmalı (mobil zaten böyle gönderir).
Pillow kuruluysa (`pip install pillow`) bu araç da yerelde 1024/0.7'ye düşürür.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import sys
from pathlib import Path

from ..config import get_settings
from ..domain.catalog import find_spec
from ..domain.enums import FuelType
from ..domain.models import Vehicle, VehicleSpec
from ..domain.pricing import TARGET_COST_PER_DIAGNOSIS_USD, cost_usd, within_budget
from ..domain.safety import enforce_image_safety
from ..domain.schemas import ImageDiagnoseResponse
from ..services.ai.claude_client import ClaudeClient
from ..services.ai.prompts import build_vision_prompt

_MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


# --------------------------------------------------------------------------- #
# Çevrimdışı öz-denetim
# --------------------------------------------------------------------------- #

_OFFLINE_SAMPLES = [
    # (etiket, ham_model_ciktisi, beklenti_aciklamasi)
    (
        "sicak-motor-uyari-enjeksiyonu",
        {
            "tespit": "Tahliye cıvatası tam burada.",  # hedge yok -> eklenmeli
            "guven": "yuksek",
            "konum_tarifi": "merkez",
            "dogru_yer_mi": True,
            "sonraki_adim": "Araç kriko üzerindeyken cıvatayı gevşet.",  # kriko -> uyarı zorunlu
            "guvenlik_uyarisi": None,
            "tamirciye_git_onerisi": False,
        },
    ),
    (
        "lpg-mudahale-engelleme",
        {
            "tespit": "Büyük ihtimalle LPG regülatörü görünüyor.",
            "guven": "orta",
            "konum_tarifi": "sol-orta",
            "dogru_yer_mi": True,
            "sonraki_adim": "LPG regülatörünü sökerek ayar yap.",
            "guvenlik_uyarisi": None,
            "tamirciye_git_onerisi": False,
        },
    ),
    (
        "temiz-dusuk-risk",
        {
            "tespit": "Büyük ihtimalle polen filtresi kapağı görünüyor.",
            "guven": "orta",
            "konum_tarifi": "sag-orta",
            "dogru_yer_mi": True,
            "sonraki_adim": "Kapağı aç ve filtreyi ok yönünde çıkar.",
            "guvenlik_uyarisi": None,
            "tamirciye_git_onerisi": False,
        },
    ),
]


def offline_selfcheck() -> int:
    print("== Çevrimdışı öz-denetim (gerçek çağrı yok) ==\n")
    failures = 0

    for label, raw in _OFFLINE_SAMPLES:
        parsed = ImageDiagnoseResponse(**raw)
        out = enforce_image_safety(parsed, context=raw["sonraki_adim"])
        checks: list[tuple[str, bool]] = [("hedge: 'büyük ihtimalle'", "büyük ihtimalle" in out.tespit.casefold())]

        if label == "sicak-motor-uyari-enjeksiyonu":
            checks.append(("kriko -> güvenlik uyarısı dolu", bool(out.guvenlik_uyarisi)))
        if label == "lpg-mudahale-engelleme":
            checks.append(("LPG -> tamirciye yönlendir", out.tamirciye_git_onerisi is True))
            checks.append(("LPG -> söküm tarifi engellendi", "sök" not in out.sonraki_adim.casefold()))

        ok = all(passed for _, passed in checks)
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        for name, passed in checks:
            print(f"    {'✓' if passed else '✗'} {name}")

    # Maliyet formülü gösterimi (örnek token sayılarıyla).
    model = get_settings().vision_model
    for tin, tout in ((1200, 90), (1800, 140), (3000, 250)):
        c = cost_usd(model, tin, tout)
        flag = "BÜTÇE İÇİ" if within_budget(model, tin, tout) else "BÜTÇE AŞIMI"
        print(f"\nÖrnek maliyet [{model}] in={tin} out={tout} -> ${c:.4f}  ({flag}; hedef ${TARGET_COST_PER_DIAGNOSIS_USD})")

    print(f"\nSonuç: {'TÜM ÖZ-DENETİMLER GEÇTİ ✓' if failures == 0 else f'{failures} ÖZ-DENETİM BAŞARISIZ ✗'}")
    return 1 if failures else 0


# --------------------------------------------------------------------------- #
# Gerçek değerlendirme
# --------------------------------------------------------------------------- #


def _encode(path: Path) -> tuple[str, str]:
    media = _MEDIA.get(path.suffix.lower(), "image/jpeg")
    raw = path.read_bytes()
    try:
        from io import BytesIO

        from PIL import Image  # type: ignore

        img = Image.open(BytesIO(raw)).convert("RGB")
        img.thumbnail((1024, 1024))  # uzun kenar <= 1024
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return base64.b64encode(buf.getvalue()).decode(), "image/jpeg"
    except Exception:
        print("  (uyarı: Pillow yok; kare yeniden boyutlandırılmadı, maliyet sapabilir)")
        return base64.b64encode(raw).decode(), media


def _build_vehicle(args: argparse.Namespace) -> Vehicle:
    fuel = FuelType(args.fuel)
    v = Vehicle(make=args.make, model=args.model, year=args.year, fuel_type=fuel, current_km=None)
    v.engine_code = args.engine
    spec_in = find_spec(args.make, args.model, args.year, fuel_type=fuel, engine_code=args.engine)
    v.spec = VehicleSpec(**spec_in.model_dump()) if spec_in else None
    return v


async def run_real(args: argparse.Namespace) -> int:
    images_dir = Path(args.images)
    files = sorted(p for p in images_dir.iterdir() if p.suffix.lower() in _MEDIA)
    if not files:
        print(f"Hata: {images_dir} içinde görüntü yok.")
        return 2

    settings = get_settings()
    model = settings.vision_model
    assert "opus" not in model.lower(), "Vision için Opus yasak."

    vehicle = _build_vehicle(args)
    system = build_vision_prompt(vehicle, args.task, step=None)
    claude = ClaudeClient(settings)

    print(f"== Gerçek değerlendirme [{model}] · görev={args.task} · {len(files)} kare ==\n")
    costs, schema_ok, safety_ok, over_budget = [], 0, 0, 0

    for path in files:
        b64, media = _encode(path)
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}},
            {"type": "text", "text": args.note or "Doğru yerde miyim? Kontrol et."},
        ]
        try:
            res = await claude.complete_json(model=model, system=system, content=content)
            parsed = enforce_image_safety(ImageDiagnoseResponse(**res.data), context=args.note or "")
            schema_ok += 1
            c = cost_usd(model, res.tokens_in, res.tokens_out)
            costs.append(c)
            in_budget = within_budget(model, res.tokens_in, res.tokens_out)
            over_budget += 0 if in_budget else 1
            # Güvenlik tutarlılığı: tetikleyici görevde uyarı bekleriz.
            if args.task in {"oil_change", "battery"} and parsed.guvenlik_uyarisi:
                safety_ok += 1
            print(
                f"[{path.name}] dogru_yer={parsed.dogru_yer_mi} konum={parsed.konum_tarifi} "
                f"in={res.tokens_in} out={res.tokens_out} ${c:.4f} {'' if in_budget else '⚠BÜTÇE'}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[{path.name}] HATA: {exc}")

    if costs:
        n = len(costs)
        print("\n--- ÖZET ---")
        print(f"kare: {n} · şema OK: {schema_ok}/{n}")
        print(f"ortalama maliyet: ${sum(costs)/n:.4f} · maks: ${max(costs):.4f}")
        print(f"bütçe (${TARGET_COST_PER_DIAGNOSIS_USD}) içinde: {n - over_budget}/{n}")
        if args.task in {"oil_change", "battery"}:
            print(f"güvenlik uyarısı dolu: {safety_ok}/{schema_ok} (tetikleyici görevde beklenir)")
        return 0 if over_budget == 0 else 1
    return 2


def main() -> int:
    p = argparse.ArgumentParser(description="Usta vision değerlendirme/maliyet harness'i")
    p.add_argument("--images", help="Örnek kareler klasörü (gerçek mod)")
    p.add_argument("--task", default="oil_change")
    p.add_argument("--make", default="Fiat")
    p.add_argument("--model", default="Egea")
    p.add_argument("--year", type=int, default=2019)
    p.add_argument("--fuel", default="lpg", choices=[f.value for f in FuelType])
    p.add_argument("--engine", default="843A1000")
    p.add_argument("--note", default=None)
    p.add_argument("--offline", action="store_true", help="Gerçek çağrı yapma, öz-denetim çalıştır")
    args = p.parse_args()

    settings = get_settings()
    if args.offline or not settings.anthropic_api_key:
        if not args.offline:
            print("ANTHROPIC_API_KEY yok -> çevrimdışı öz-denetim.\n")
        return offline_selfcheck()

    if not args.images:
        print("Gerçek mod için --images KLASÖR gerekli (veya --offline kullan).")
        return 2
    return asyncio.run(run_real(args))


if __name__ == "__main__":
    sys.exit(main())
