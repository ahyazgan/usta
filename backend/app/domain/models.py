"""ORM modelleri (SQLAlchemy 2.0 tipli)."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .enums import AIKind, FuelType, SubscriptionTier


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SAEnum(SubscriptionTier), default=SubscriptionTier.free, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    make: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    plate: Mapped[str | None] = mapped_column(String(15), nullable=True)
    engine_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fuel_type: Mapped[FuelType] = mapped_column(SAEnum(FuelType), nullable=False)
    current_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    owner: Mapped["User"] = relationship(back_populates="vehicles")
    spec: Mapped["VehicleSpec | None"] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", uselist=False
    )
    logs: Mapped[list["MaintenanceLog"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )


class VehicleSpec(Base):
    """Araca özel bakım verileri (yağ tıpası ölçüsü, parça numaraları...)."""

    __tablename__ = "vehicle_specs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), unique=True, index=True
    )
    oil_spec: Mapped[str | None] = mapped_column(String(60), nullable=True)
    oil_capacity_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    oil_drain_bolt_size: Mapped[str | None] = mapped_column(String(20), nullable=True)
    oil_drain_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    oil_filter_part: Mapped[str | None] = mapped_column(String(60), nullable=True)
    air_filter_part: Mapped[str | None] = mapped_column(String(60), nullable=True)
    cabin_filter_part: Mapped[str | None] = mapped_column(String(60), nullable=True)
    spark_plug_part: Mapped[str | None] = mapped_column(String(60), nullable=True)
    battery_spec: Mapped[str | None] = mapped_column(String(60), nullable=True)
    battery_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    transmission_type: Mapped[str | None] = mapped_column(String(40), nullable=True)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="spec")


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    task: Mapped[str] = mapped_column(String(60), nullable=False)
    km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Bu bakımı tetikleyen AI teşhisi (rehber kamera doğrulamasıyla bitince bağlanır).
    ai_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_sessions.id", ondelete="SET NULL"), nullable=True
    )
    # Kullanıcının beyan ettiği gerçek maliyet (TL; opsiyonel) — maliyet endeksi.
    cost_try: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="logs")


class AISession(Base):
    """Her AI çağrısı için token kullanımını + teşhis özetini loglar.

    Token alanları maliyet denetimi içindir; özet alanlar (task/tespit/guven/
    tamirciye_git) mobil "Teşhis Geçmişi" listesini besler. Özet, güvenlik
    kuralları ZORLANDIKTAN SONRAKİ metinden yazılır.
    """

    __tablename__ = "ai_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True
    )
    kind: Mapped[AIKind] = mapped_column(SAEnum(AIKind), nullable=False)
    model: Mapped[str] = mapped_column(String(60), nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    # Teşhis özeti (geçmiş listesi için; eski kayıtlarda null olabilir).
    task: Mapped[str | None] = mapped_column(String(60), nullable=True)
    tespit: Mapped[str | None] = mapped_column(String(500), nullable=True)
    guven: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tamirciye_git: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Yapılandırılmış kategori: görüntüde görev id'si, seste ses_kategorisi.
    kategori: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Kullanıcı geri bildirimi: teşhis doğru çıktı mı? (👍/👎; null = oylanmadı)
    # Bu etiket, veri setini doğrulanmış arıza-örüntü verisine çevirir.
    feedback_dogru: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RefreshToken(Base):
    """Yenileme token'ları sha256 hash olarak saklanır (düz metin DB'de tutulmaz)."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
