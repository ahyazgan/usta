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

from .enums import Aciliyet, SesKategori
from .schemas import ImageDiagnoseResponse, SoundDiagnoseResponse

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

DEFAULT_SAFETY_WARNING = (
    "Güvenlik: Motor sıcakken, araç kriko üzerindeyken veya akü/yakıt/fren/soğutma "
    "sistemi söz konusuyken dikkatli ol. Emin değilsen işlemi bırak ve tamirciye git."
)

LPG_SAFETY_WARNING = (
    "LPG sistemine kesinlikle müdahale etme. LPG dönüşümü ve bakımı yalnızca "
    "yetkili LPG servisi tarafından yapılmalıdır. Tamirciye git."
)


def _mentions_safety_topic(text: str) -> bool:
    low = text.casefold()
    return any(k in low for k in SAFETY_TRIGGER_KEYWORDS)


def _mentions_lpg_intervention(text: str) -> bool:
    low = text.casefold()
    return any(k in low for k in LPG_INTERVENTION_PATTERNS)


def _ensure_hedge(text: str) -> str:
    """Teşhis cümlesi kesin dil içeriyorsa hedge ekle."""
    if HEDGE_PHRASE in text.casefold():
        return text
    return f"{HEDGE_PHRASE.capitalize()} {text[0].lower()}{text[1:]}" if text else text


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
