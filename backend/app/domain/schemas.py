"""Pydantic şemaları: istek/yanıt sözleşmeleri.

AI yanıt şemaları ürün spesifikasyonuyla bire bir eşleşir.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .enums import (
    Aciliyet,
    AIKind,
    ArizaSistem,
    FuelType,
    ResolutionDurum,
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


class TaskGuideOut(BaseModel):
    """Bir bakım görevinin adım adım rehberi."""

    task_id: str
    title_tr: str
    title_en: str
    risk: Aciliyet
    est_minutes: int
    # Bu işi kendin yapınca tahmini işçilik tasarrufu (TL) — bitiş ekranında gösterilir.
    diy_saving_try: int
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
    created_at: datetime


class DiagnosisResolutionIn(BaseModel):
    """Kapanış sinyali: teşhis nasıl sonuçlandı? (tahmin doğruluğunu ölçer)"""

    resolution: ResolutionDurum


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
