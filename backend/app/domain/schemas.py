"""Pydantic şemaları: istek/yanıt sözleşmeleri.

AI yanıt şemaları ürün spesifikasyonuyla bire bir eşleşir.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .enums import (
    Aciliyet,
    FuelType,
    Guven,
    KayitKosulu,
    Konum,
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
    fuel_type: FuelType
    engine_code: str | None = Field(default=None, max_length=40)
    current_km: int | None = Field(default=None, ge=0)
    spec: VehicleSpecIn | None = None


class VehicleUpdate(BaseModel):
    make: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    year: int | None = Field(default=None, ge=1950, le=2100)
    fuel_type: FuelType | None = None
    engine_code: str | None = Field(default=None, max_length=40)
    current_km: int | None = Field(default=None, ge=0)


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    make: str
    model: str
    year: int
    fuel_type: FuelType
    engine_code: str | None
    current_km: int | None
    spec: VehicleSpecOut | None = None


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


class TaskOut(BaseModel):
    id: str
    title_tr: str
    title_en: str
    risk: Aciliyet


class HealthResponse(BaseModel):
    status: str
    database: str
