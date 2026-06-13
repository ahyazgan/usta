"""Pydantic şemaları: istek/yanıt sözleşmeleri.

AI yanıt şemaları ürün spesifikasyonuyla bire bir eşleşir.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .enums import (
    Aciliyet,
    AIKind,
    ArizaSistem,
    FuelType,
    ResolutionDurum,
    VehicleType,
    Guven,
    KayitKosulu,
    Konum,
    ReminderStatus,
    SesKategori,
    SubscriptionTier,
)

# --------------------------------------------------------------------------- #
# Kimlik doğrulama
# --------------------------------------------------------------------------- #


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    subscription_tier: SubscriptionTier
    created_at: datetime


# --------------------------------------------------------------------------- #
# Araç & Spec
# --------------------------------------------------------------------------- #


class VehicleSpecIn(BaseModel):
    oil_spec: str | None = None
    oil_capacity_l: float | None = None
    oil_drain_bolt_size: str | None = None
    oil_drain_location: str | None = None
    oil_filter_part: str | None = None
    air_filter_part: str | None = None
    cabin_filter_part: str | None = None
    spark_plug_part: str | None = None
    battery_spec: str | None = None
    battery_location: str | None = None
    transmission_type: str | None = None


class VehicleSpecOut(VehicleSpecIn):
    model_config = ConfigDict(from_attributes=True)


class VehicleCreate(BaseModel):
    make: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    year: int = Field(ge=1950, le=2100)
    plate: str | None = Field(default=None, max_length=15)
    fuel_type: FuelType
    vehicle_type: VehicleType = VehicleType.araba
    engine_code: str | None = Field(default=None, max_length=40)
    current_km: int | None = Field(default=None, ge=0)
    muayene_date: date | None = None
    sigorta_date: date | None = None
    spec: VehicleSpecIn | None = None


class VehicleUpdate(BaseModel):
    make: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    year: int | None = Field(default=None, ge=1950, le=2100)
    plate: str | None = Field(default=None, max_length=15)
    fuel_type: FuelType | None = None
    vehicle_type: VehicleType | None = None
    engine_code: str | None = Field(default=None, max_length=40)
    current_km: int | None = Field(default=None, ge=0)
    muayene_date: date | None = None
    sigorta_date: date | None = None


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    make: str
    model: str
    year: int
    plate: str | None
    fuel_type: FuelType
    vehicle_type: VehicleType | None
    engine_code: str | None
    current_km: int | None
    muayene_date: date | None
    sigorta_date: date | None
    spec: VehicleSpecOut | None = None


class VehicleSummaryOut(BaseModel):
    """Ana sayfa özeti: kayıtlı bakım sayısı + tahmini DIY tasarrufu (TL)."""

    maintenance_count: int
    savings_try: int


class GuideStepOut(BaseModel):
    """Adım adım rehberin tek adımı (araç spec'iyle doldurulmuş)."""

    step: int
    instruction_tr: str
    instruction_en: str
    tool_tr: str | None = None
    tool_en: str | None = None
    torque_nm: int | None = None
    warning_tr: str | None = None
    warning_en: str | None = None


class PrepPartOut(BaseModel):
    """Hazırlık listesi satırı: araca özel parça/sarf (etiket + değer + satın-al)."""

    label_tr: str
    label_en: str
    value: str
    # Affiliate iskeleti: parçayı satın al linki (yapılandırılabilir; yoksa null).
    buy_url: str | None = None


class TaskGuideOut(BaseModel):
    """Bir bakım görevinin adım adım rehberi."""

    task_id: str
    title_tr: str
    title_en: str
    risk: Aciliyet
    est_minutes: int
    # Bu işi kendin yapınca tahmini işçilik tasarrufu (TL) — bitiş ekranında gösterilir.
    diy_saving_try: int
    # "Başlamadan önce hazırla" — araca özel parça numaraları (spec'ten).
    parts: list[PrepPartOut] = []
    steps: list[GuideStepOut]
    # Zorunlu "vazgeç, tamirciye git" çıkışı.
    mechanic_note_tr: str
    mechanic_note_en: str


class DiagnosisHistoryOut(BaseModel):
    """Geçmiş AI teşhisi özeti (görüntü veya ses)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: AIKind
    task: str | None
    tespit: str | None
    guven: Guven | None
    tamirciye_git: bool | None
    kategori: str | None = None
    ariza_sistem: ArizaSistem | None = None
    feedback_dogru: bool | None = None
    resolution: ResolutionDurum | None = None
    # Tamirci çözdüyse beyan edilen ödeme (TL; fiyat çarkı yakıtı).
    cost_try: int | None = None
    created_at: datetime


class DiagnosisResolutionIn(BaseModel):
    """Kapanış sinyali: teşhis nasıl sonuçlandı? (tahmin doğruluğunu ölçer)"""

    resolution: ResolutionDurum
    # Yalnızca resolution=tamirci_cozdu ile anlamlı: tamirciye ödenen tutar (TL).
    cost_try: int | None = Field(default=None, ge=0, le=1_000_000)


# --------------------------------------------------------------------------- #
# KVKK — açık rıza + istatistik (anonim küme)
# --------------------------------------------------------------------------- #


class ConsentOut(BaseModel):
    """Kullanıcının açık rıza durumu (null → False olarak sunulur)."""

    analytics: bool
    data: bool


class ConsentUpdate(BaseModel):
    """Rıza güncelleme — yalnızca verilen alan değişir."""

    analytics: bool | None = None
    data: bool | None = None


class MechanicOut(BaseModel):
    """Küratörlü tamirci dizini kaydı."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str
    district: str | None
    phone: str
    whatsapp: str | None
    address: str | None
    maps_url: str | None
    specialties: str | None
    systems: str | None
    verified: bool


class MechanicLeadIn(BaseModel):
    """Tamirci yönlendirme sinyali — hangi kanaldan ulaşıldı."""

    channel: str = Field(pattern=r"^(call|whatsapp|directions)$")
    ai_session_id: int | None = Field(default=None, ge=1)


class SystemStatOut(BaseModel):
    """Anonim küme istatistiği — bir araç sistemi için (kişi-bağımsız).

    Yalnızca veri rızası veren kullanıcıların teşhisleri üzerinden hesaplanır;
    k-anonimlik için küçük kovalar gizlenir.
    """

    sistem: ArizaSistem
    count: int
    dogrulanan: int            # 👍/👎 verilmiş teşhis sayısı
    dogruluk_orani: float | None  # doğru oranı (oylanan varsa)


class CostEstimateOut(BaseModel):
    """Bir iş için tamirciye tahmini maliyet aralığı (TL).

    source: 'seed' = TR pazarı tohum bandı; 'community' = gerçek ödenen
    fiyatlardan (>= eşik örnek, k-anonim) türetilmiş. sample_size = harmana
    katkıda bulunan gerçek-fiyat kaydı sayısı.
    """

    low_try: int
    high_try: int
    currency: str = "TRY"
    source: Literal["seed", "community"]
    sample_size: int


class TaskEstimateOut(BaseModel):
    """Fiyat vitrini satırı: görev + tamirciye tahmini maliyet aralığı."""

    id: str
    title_tr: str
    title_en: str
    risk: Aciliyet
    low_try: int
    high_try: int
    currency: str = "TRY"
    source: Literal["seed", "community"]
    sample_size: int


# --------------------------------------------------------------------------- #
# AI — Görüntü teşhisi
# --------------------------------------------------------------------------- #


class ImageDiagnoseRequest(BaseModel):
    vehicle_id: int
    task: str = Field(min_length=1, max_length=60, description="örn. oil_change")
    step: int | None = Field(default=None, ge=1, le=99)
    frame_base64: str = Field(min_length=16, description="1024px JPEG 0.7, base64")
    media_type: str = Field(default="image/jpeg", pattern=r"^image/(jpeg|png|webp)$")
    user_note: str | None = Field(default=None, max_length=500)


class ImageDiagnoseResponse(BaseModel):
    """Ürün şeması — her görsel teşhis bu alanları döndürür."""

    tespit: str
    guven: Guven
    konum_tarifi: Konum | None
    dogru_yer_mi: bool | None
    sonraki_adim: str
    guvenlik_uyarisi: str | None
    tamirciye_git_onerisi: bool
    # Bu teşhisin AISession id'si — mobil 👍/👎 geri bildirimi buna bağlanır.
    session_id: int | None = None
    # Fiyat şeffaflığı: tamirciye tahmini maliyet (arıza sistemine göre; yoksa null).
    cost_estimate: CostEstimateOut | None = None


# --------------------------------------------------------------------------- #
# AI — Gösterge paneli uyarı ışığı tanıma
# --------------------------------------------------------------------------- #


class DashboardLight(BaseModel):
    """Panoda tanınan tek bir uyarı ışığı."""

    isim: str = Field(max_length=80, description="örn. Motor arıza lambası (check engine)")
    renk: Literal["kirmizi", "sari", "yesil", "mavi", "bilinmiyor"]
    anlam: str = Field(max_length=300, description="büyük ihtimalle ... ile başlayan açıklama")
    aciliyet: Aciliyet
    ne_yapmali: str = Field(max_length=300)


class DashboardDiagnoseRequest(BaseModel):
    vehicle_id: int
    frame_base64: str = Field(min_length=16, description="1024px JPEG 0.7, base64")
    media_type: str = Field(default="image/jpeg", pattern=r"^image/(jpeg|png|webp)$")
    user_note: str | None = Field(default=None, max_length=500)


class DashboardDiagnoseResponse(BaseModel):
    """Pano uyarı ışığı tanıma yanıtı (kesin teşhis YOK; 'büyük ihtimalle')."""

    tespit: str
    guven: Guven
    isiklar: list[DashboardLight]
    en_yuksek_aciliyet: Aciliyet
    guvenlik_uyarisi: str | None
    sonraki_adim: str
    tamirciye_git_onerisi: bool
    # Token/maliyet loglandığı AISession id'si — 👍/👎 geri bildirimi buna bağlanır.
    session_id: int | None = None


# --------------------------------------------------------------------------- #
# AI — Arıza kodu (OBD-II / DTC) açıklama
# --------------------------------------------------------------------------- #


class DtcDiagnoseRequest(BaseModel):
    vehicle_id: int
    code: str = Field(min_length=2, max_length=10, description="örn. P0300")
    user_note: str | None = Field(default=None, max_length=500)


class DtcDiagnoseResponse(BaseModel):
    """Arıza kodu açıklama yanıtı (kesin teşhis YOK; 'büyük ihtimalle')."""

    tespit: str
    guven: Guven
    kod: str = Field(max_length=10)
    baslik: str = Field(max_length=120, description="kodun kısa anlamı")
    olasi_nedenler: list[str]
    aciliyet: Aciliyet
    surulebilir_mi: bool | None
    sonraki_adim: str
    guvenlik_uyarisi: str | None
    tamirciye_git_onerisi: bool
    # Token/maliyet loglandığı AISession id'si — 👍/👎 geri bildirimi buna bağlanır.
    session_id: int | None = None


# --------------------------------------------------------------------------- #
# AI — Ses teşhisi (transkripsiyon YOK; tarif + koşul + araç verisi)
# --------------------------------------------------------------------------- #


class SoundDiagnoseRequest(BaseModel):
    vehicle_id: int
    user_description: str = Field(min_length=3, max_length=500)
    condition: KayitKosulu


class SoundDiagnoseResponse(BaseModel):
    tespit: str
    guven: Guven
    ses_kategorisi: SesKategori
    aciliyet: Aciliyet
    guvenlik_uyarisi: str | None
    sonraki_adim: str
    tamirciye_git_onerisi: bool
    # Bu teşhisin AISession id'si — mobil 👍/👎 geri bildirimi buna bağlanır.
    session_id: int | None = None
    # Fiyat şeffaflığı: tamirciye tahmini maliyet (arıza sistemine göre; yoksa null).
    cost_estimate: CostEstimateOut | None = None


# --------------------------------------------------------------------------- #
# AI — Canlı sesli rehber (Gemini Live oturumu)
# --------------------------------------------------------------------------- #


class LiveSessionRequest(BaseModel):
    vehicle_id: int
    task: str | None = Field(default=None, max_length=60)
    lang: Literal["tr", "en"] = "tr"


class LiveSessionOut(BaseModel):
    """Canlı oturum başlatma yanıtı — istemci bununla Gemini'ye bağlanır.

    system_instruction İÇERMEZ (server-side kalır; istemciye sızdırılmaz).
    """

    token: str  # ephemeral token
    model: str
    voice: str
    language: str
    live_usage_id: int  # bitişte süre bu kayda yazılır
    max_seconds: int  # tek oturum sert sınırı


class LiveSessionEndIn(BaseModel):
    seconds: int = Field(ge=0, le=86_400)


# --------------------------------------------------------------------------- #
# Abonelik / faturalandırma + parça niyeti (ölçüm)
# --------------------------------------------------------------------------- #


class SubscriptionOut(BaseModel):
    tier: SubscriptionTier
    is_premium: bool
    live_unlimited: bool
    free_live_seconds_remaining: int | None  # premium → null (sınırsız)


class BillingEventIn(BaseModel):
    """RevenueCat tarzı webhook (basitleştirilmiş): kullanıcıyı premium yap/yapma."""

    app_user_id: str = Field(min_length=3, max_length=255)  # = e-posta
    premium: bool


class BuyIntentIn(BaseModel):
    vehicle_id: int
    task: str | None = Field(default=None, max_length=60)
    part_label: str = Field(min_length=1, max_length=80)


class TaskOut(BaseModel):
    id: str
    title_tr: str
    title_en: str
    risk: Aciliyet


# --------------------------------------------------------------------------- #
# Bakım geçmişi & hatırlatma
# --------------------------------------------------------------------------- #


class MaintenanceLogCreate(BaseModel):
    task: str = Field(min_length=1, max_length=60)
    km: int | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=500)
    # Bu bakımı tetikleyen teşhis (varsa) — veri çarkı bağlantısı.
    ai_session_id: int | None = Field(default=None, ge=1)
    # Kullanıcının beyan ettiği gerçek maliyet (TL; opsiyonel).
    cost_try: int | None = Field(default=None, ge=0, le=1_000_000)


class MaintenanceLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task: str
    km: int | None
    note: str | None
    cost_try: int | None = None
    created_at: datetime


class DiagnosisFeedbackIn(BaseModel):
    """Kullanıcı geri bildirimi: teşhis doğru çıktı mı? (👍/👎)"""

    dogru: bool


class ReminderOut(BaseModel):
    task: str
    interval_km: int
    last_km: int | None
    due_km: int | None
    remaining_km: int | None
    status: ReminderStatus


class HealthResponse(BaseModel):
    status: str
    database: str
