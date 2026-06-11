"""Domain enum'ları. AI yanıt şemalarının değerleri burada tek kaynaktan tanımlanır."""

from enum import Enum


class SubscriptionTier(str, Enum):
    free = "free"
    premium = "premium"


class FuelType(str, Enum):
    benzin = "benzin"
    dizel = "dizel"
    lpg = "lpg"
    hibrit = "hibrit"
    elektrik = "elektrik"


class Guven(str, Enum):
    """AI güven seviyesi — kesin teşhis dili yerine kademeli."""

    yuksek = "yuksek"
    orta = "orta"
    dusuk = "dusuk"


class Konum(str, Enum):
    """Kamera karesinde 3x3 konum sözlüğü (+ merkez)."""

    sol_ust = "sol-ust"
    orta_ust = "orta-ust"
    sag_ust = "sag-ust"
    sol_orta = "sol-orta"
    merkez = "merkez"
    sag_orta = "sag-orta"
    sol_alt = "sol-alt"
    orta_alt = "orta-alt"
    sag_alt = "sag-alt"


class SesKategori(str, Enum):
    """Motor sesi tarif kategorileri (transkripsiyon YOK)."""

    tikirti = "tikirti"
    kayis_sesi = "kayis_sesi"
    metalik_vuruntu = "metalik_vuruntu"  # her zaman acil + tamirci
    islik = "islik"
    egzoz_patlamasi = "egzoz_patlamasi"
    normal = "normal"
    belirsiz = "belirsiz"


class KayitKosulu(str, Enum):
    """Ses kaydının alındığı koşul."""

    rolanti = "rolanti"
    gazda = "gazda"
    soguk_motor = "soguk_motor"
    seyirde = "seyirde"


class Aciliyet(str, Enum):
    dusuk = "dusuk"
    orta = "orta"
    yuksek = "yuksek"


class AIKind(str, Enum):
    image = "image"
    sound = "sound"


class ReminderStatus(str, Enum):
    """Bakım hatırlatma durumu (km bazlı)."""

    ok = "ok"
    soon = "soon"
    due = "due"
    unknown = "unknown"  # km veya kayıt yoksa
