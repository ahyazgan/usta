"""Güvenlik kuralları — EN YÜKSEK ÖNCELİK.

Bu modül, AI yanıtlarına son güvenlik katmanını uygular. Prompt'lar kuralları
zaten içerir; burada model çıktısı her ihtimale karşı bir kez daha zorlanır.

Kurallar:
- Kesin teşhis dili yasak; "büyük ihtimalle" zorunlu.
- Sıcak motor / kriko / akü / yakıt / soğutma basıncı / fren / LPG geçen her
  yanıtta güvenlik uyarısı zorunlu.
- LPG sistemine müdahale tarifi YASAK.
- Her görevde "vazgeç, tamirciye git" çıkışı bulunur.
"""

import re

from .enums import Aciliyet, SesKategori
from .schemas import (
    DashboardDiagnoseResponse,
    ImageDiagnoseResponse,
    SoundDiagnoseResponse,
)

# Aciliyet sıralaması (düşük < orta < yüksek) — en yüksek aciliyeti yeniden hesaplamak için.
_ACILIYET_RANK = {Aciliyet.dusuk.value: 0, Aciliyet.orta.value: 1, Aciliyet.yuksek.value: 2}

# Güvenlik uyarısı tetikleyen anahtar kelimeler (Türkçe varyantlarıyla).
SAFETY_TRIGGER_KEYWORDS: tuple[str, ...] = (
    "sıcak motor",
    "sicak motor",
    "kriko",
    "akü",
    "aku",
    "yakıt",
    "yakit",
    "soğutma",
    "sogutma",
    "basınç",
    "basinc",
    "fren",
    "lpg",
)

# LPG müdahale tarifi yasağı için kırmızı bayrak kalıpları.
LPG_INTERVENTION_PATTERNS: tuple[str, ...] = (
    "lpg",
    "tüpün",
    "tupun",
    "regülatör",
    "regulator",
    "gaz hattı",
    "gaz hatti",
)

# "Büyük ihtimalle" hedge ifadesi; kesin teşhis dilini yumuşatır.
HEDGE_PHRASE = "büyük ihtimalle"

# Kesin teşhis dili — _ensure_hedge bunları hedge ifadesiyle değiştirir.
DEFINITIVE_PHRASES: tuple[str, ...] = (
    "kesinlikle",
    "kesin olarak",
    "%100",
    "yüzde yüz",
    "yuzde yuz",
    "100%",
)

DEFAULT_SAFETY_WARNING = (
    "Güvenlik: Motor sıcakken, araç kriko üzerindeyken veya akü/yakıt/fren/soğutma "
    "sistemi söz konusuyken dikkatli ol. Emin değilsen işlemi bırak ve tamirciye git."
)

LPG_SAFETY_WARNING = (
    "LPG sistemine kesinlikle müdahale etme. LPG dönüşümü ve bakımı yalnızca "
    "yetkili LPG servisi tarafından yapılmalıdır. Tamirciye git."
)

DASHBOARD_RED_WARNING = (
    "Kırmızı uyarı ışığı ciddi bir sorunun işareti olabilir. Aracı güvenli bir "
    "yerde durdur, zorlamadan sürmeyi bırak ve en kısa sürede tamirciye danış."
)


def _mentions_safety_topic(text: str) -> bool:
    low = text.casefold()
    return any(k in low for k in SAFETY_TRIGGER_KEYWORDS)


def _mentions_lpg_intervention(text: str) -> bool:
    low = text.casefold()
    return any(k in low for k in LPG_INTERVENTION_PATTERNS)


def _ensure_hedge(text: str) -> str:
    """Kesin teşhis dilini yumuşat: kesin ifadeleri hedge ile değiştir, yoksa
    hedge'i başa ekle. Salt substring değil — "kesinlikle ... büyük ihtimalle"
    gibi karışık dilde kesin sözcükler de temizlenir."""
    if not text:
        return text
    softened = text
    for phrase in DEFINITIVE_PHRASES:
        if phrase.casefold() in softened.casefold():
            softened = re.sub(re.escape(phrase), HEDGE_PHRASE, softened, flags=re.IGNORECASE)
    if HEDGE_PHRASE in softened.casefold():
        return softened
    return f"{HEDGE_PHRASE.capitalize()} {softened[0].lower()}{softened[1:]}"


def enforce_image_safety(result: ImageDiagnoseResponse, *, context: str = "") -> ImageDiagnoseResponse:
    """Görsel teşhis yanıtına güvenlik kurallarını uygula."""
    data = result.model_dump()
    haystack = " ".join(
        str(v) for v in (data["tespit"], data["sonraki_adim"], context) if v
    )

    # 1) Kesin teşhis dilini yumuşat.
    data["tespit"] = _ensure_hedge(data["tespit"])

    # 2) LPG müdahalesi tespit edilirse tarifi engelle, tamirciye yönlendir.
    if _mentions_lpg_intervention(haystack):
        data["guvenlik_uyarisi"] = LPG_SAFETY_WARNING
        data["sonraki_adim"] = "LPG sistemine müdahale etme. Yetkili LPG servisine git."
        data["tamirciye_git_onerisi"] = True

    # 3) Güvenlik konusu geçiyorsa ve uyarı boşsa, varsayılan uyarıyı ekle.
    elif _mentions_safety_topic(haystack) and not data.get("guvenlik_uyarisi"):
        data["guvenlik_uyarisi"] = DEFAULT_SAFETY_WARNING

    return ImageDiagnoseResponse(**data)


def enforce_sound_safety(result: SoundDiagnoseResponse, *, context: str = "") -> SoundDiagnoseResponse:
    """Ses teşhis yanıtına güvenlik kurallarını uygula."""
    data = result.model_dump()
    haystack = " ".join(
        str(v) for v in (data["tespit"], data["sonraki_adim"], context) if v
    )

    data["tespit"] = _ensure_hedge(data["tespit"])

    # Metalik vuruntu => her zaman acil + tamirci.
    if data["ses_kategorisi"] == SesKategori.metalik_vuruntu.value:
        data["aciliyet"] = Aciliyet.yuksek.value
        data["tamirciye_git_onerisi"] = True
        if not data.get("guvenlik_uyarisi"):
            data["guvenlik_uyarisi"] = (
                "Metalik vuruntu ciddi bir motor arızasının işareti olabilir. "
                "Aracı çalıştırmaya devam etme ve hemen tamirciye git."
            )

    if _mentions_lpg_intervention(haystack):
        data["guvenlik_uyarisi"] = LPG_SAFETY_WARNING
        data["tamirciye_git_onerisi"] = True
    elif _mentions_safety_topic(haystack) and not data.get("guvenlik_uyarisi"):
        data["guvenlik_uyarisi"] = DEFAULT_SAFETY_WARNING

    return SoundDiagnoseResponse(**data)


def enforce_dashboard_safety(
    result: DashboardDiagnoseResponse, *, context: str = ""
) -> DashboardDiagnoseResponse:
    """Pano uyarı ışığı yanıtına güvenlik kurallarını uygula.

    - Kesin teşhis dilini yumuşat.
    - en_yuksek_aciliyet'i ışıklardan yeniden hesapla (model düşük verse bile).
    - KIRMIZI ışık veya yüksek aciliyet => her zaman tamirci + güvenlik uyarısı.
    - Güvenlik konusu (yağ basıncı/hararet/fren/akü...) geçiyorsa uyarı zorunlu.
    """
    data = result.model_dump()
    lights = data.get("isiklar") or []
    haystack = " ".join(
        str(v)
        for v in (
            data["tespit"],
            data["sonraki_adim"],
            context,
            *[f"{l.get('isim','')} {l.get('anlam','')} {l.get('ne_yapmali','')}" for l in lights],
        )
        if v
    )

    # 1) Kesin teşhis dilini yumuşat — hem genel tespit hem HER ışığın anlamı
    #    (kullanıcının okuduğu asıl per-ışık teşhisi `anlam`).
    data["tespit"] = _ensure_hedge(data["tespit"])
    for light in data.get("isiklar") or []:
        if light.get("anlam"):
            light["anlam"] = _ensure_hedge(light["anlam"])

    # 2) En yüksek aciliyeti ışıklardan yeniden hesapla.
    if lights:
        top = max(_ACILIYET_RANK.get(l.get("aciliyet", "dusuk"), 0) for l in lights)
        for value, rank in _ACILIYET_RANK.items():
            if rank == max(top, _ACILIYET_RANK.get(data["en_yuksek_aciliyet"], 0)):
                data["en_yuksek_aciliyet"] = value
                break

    has_red = any(l.get("renk") == "kirmizi" for l in lights)

    # 3) LPG geçiyorsa tarif engelle, tamirciye yönlendir.
    if _mentions_lpg_intervention(haystack):
        data["guvenlik_uyarisi"] = LPG_SAFETY_WARNING
        data["tamirciye_git_onerisi"] = True
    # 4) Kırmızı ışık / yüksek aciliyet => tamirci + uyarı zorunlu.
    elif has_red or data["en_yuksek_aciliyet"] == Aciliyet.yuksek.value:
        data["tamirciye_git_onerisi"] = True
        if not data.get("guvenlik_uyarisi"):
            data["guvenlik_uyarisi"] = DASHBOARD_RED_WARNING
    # 5) Güvenlik konusu geçiyorsa ve uyarı boşsa varsayılanı ekle.
    elif _mentions_safety_topic(haystack) and not data.get("guvenlik_uyarisi"):
        data["guvenlik_uyarisi"] = DEFAULT_SAFETY_WARNING

    return DashboardDiagnoseResponse(**data)
